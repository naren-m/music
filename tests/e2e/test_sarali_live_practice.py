"""E2E test for the live Sarali Varisai practice loop using synthetic audio.

Drives the real frontend (Vite dev server on :3000, proxying /api and
/socket.io to the Flask backend on :5002) with a headless Chromium browser.
No microphone hardware is used: a sine-wave oscillator is routed into a
MediaStreamDestination and `navigator.mediaDevices.getUserMedia` is
monkey-patched to return that synthetic stream, so the real WebSocket audio
pipeline and pitch-detection/validation logic run end-to-end.

Requires the frontend and backend dev servers to already be running:
    - frontend: http://localhost:3000
    - backend:  http://localhost:5002

Run standalone (bypasses the coverage-gated addopts in pytest.ini):
    .venv/bin/python -m pytest tests/e2e/test_sarali_live_practice.py -v -s -o addopts=""
"""
import re
import time

import pytest
from playwright.sync_api import sync_playwright

FRONTEND_URL = "http://localhost:3000/"

# Sarali Varisai 1 (Mayamalavagowla, base Sa = 261.63 Hz): full arohanam +
# avarohanam sequence, one frequency per swara.
NOTE_SEQUENCE = [
    261.63, 275.63, 331.13, 348.84, 392.44, 413.44, 490.56, 523.26,
    523.26, 490.56, 413.44, 392.44, 348.84, 331.13, 275.63, 261.63,
]

SECONDS_PER_NOTE = 2.0

# Injected before any app script runs so we can capture console.log calls
# with object arguments (Playwright's own console API only gives
# "JSHandle@object" for those; JSON.stringify-ing at the source is simpler
# and more robust than round-tripping JSHandles). Must be an IIFE: unlike
# page.evaluate(), add_init_script() runs the string as raw source rather
# than auto-invoking a function expression.
CONSOLE_CAPTURE_SCRIPT = """
(() => {
  window.__logs = [];
  const orig = console.log.bind(console);
  console.log = (...args) => {
    try {
      window.__logs.push(args.map(a => {
        try { return typeof a === 'string' ? a : JSON.stringify(a); }
        catch (e) { return String(a); }
      }).join(' '));
    } catch (e) {}
    orig(...args);
  };
})();
"""

FAKE_MIC_SCRIPT = """
() => {
  const ctx = new AudioContext({ sampleRate: 44100 });
  const osc = ctx.createOscillator();
  osc.type = 'sine';
  osc.frequency.value = 261.63;
  const gain = ctx.createGain();
  gain.gain.value = 0.5;
  const dest = ctx.createMediaStreamDestination();
  osc.connect(gain);
  gain.connect(dest);
  osc.start();
  window.__osc = osc;
  navigator.mediaDevices.getUserMedia = async () => {
    await ctx.resume();
    return dest.stream;
  };
}
"""


@pytest.mark.e2e
def test_sarali_live_practice_with_synthetic_audio():
    # Managed by hand rather than via the pytest-playwright `page` fixture so
    # this test has no dependency on that plugin's tracing/context setup.
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.add_init_script(CONSOLE_CAPTURE_SCRIPT)

            # 1. Navigate -> redirected to /login
            page.goto(FRONTEND_URL)
            page.wait_for_url("**/login", timeout=15000)

            # 2. Continue as Guest -> /dashboard
            page.get_by_role("button", name="Continue as Guest").click()
            page.wait_for_url("**/dashboard", timeout=15000)

            # 3. SPA nav to the Sarali exercise (not page.goto - would drop the guest session)
            page.locator('a[href="/exercises/sarali"]').first.click()
            page.wait_for_url("**/exercises/sarali", timeout=15000)

            # 4. Wait for the socket.io connection indicator
            page.get_by_text("Connected", exact=True).wait_for(timeout=20000)

            # 5. Inject fake mic BEFORE clicking Start
            page.evaluate(FAKE_MIC_SCRIPT)

            # 6. Start the practice session
            page.get_by_role("button", name="Start", exact=True).click()

            def logs_text():
                return "\n".join(page.evaluate("window.__logs || []"))

            # Wait for the session-started confirmation from the server
            start = time.time()
            while "Practice session started" not in logs_text():
                assert time.time() - start < 15, "Timed out waiting for 'Practice session started'"
                time.sleep(0.5)

            def cycles_count():
                text = page.locator("text=Cycles").locator("..").inner_text()
                m = re.search(r"(\d+)", text)
                return int(m.group(1)) if m else 0

            def progress_count():
                text = page.locator("body").inner_text()
                m = re.search(r"Exercise Progress\s*\n?\s*(\d+)\s*/\s*16", text)
                return int(m.group(1)) if m else 0

            # 7. Sweep the oscillator through the Sarali Varisai 1 sequence.
            # The pitch-detection/validation round trip over the socket can lag
            # behind a fixed 2s-per-note clock, so after the nominal hold we
            # additionally wait (bounded) for the server to confirm it has
            # registered this note before moving on - this keeps the sweep from
            # permanently falling behind the note we're actually singing.
            for i, freq in enumerate(NOTE_SEQUENCE):
                if cycles_count() >= 1:
                    break
                page.evaluate("(f) => { window.__osc.frequency.value = f; }", freq)
                time.sleep(SECONDS_PER_NOTE)
                catch_up_deadline = time.time() + 6
                while progress_count() < i + 1 and cycles_count() < 1 and time.time() < catch_up_deadline:
                    time.sleep(0.3)

            # Let the pipeline finish confirming the final note(s) / cycle completion
            final_deadline = time.time() + 10
            while cycles_count() < 1 and progress_count() < len(NOTE_SEQUENCE) and time.time() < final_deadline:
                time.sleep(0.5)

            final_logs = logs_text()
            page_text = page.locator("body").inner_text()

            assert "Practice feedback received" in final_logs
            assert "Shadja" in final_logs
            assert "Antara Gandhara" in final_logs

            cycles_text = page.locator("text=Cycles").locator("..").inner_text()
            assert ("100.0%" in page_text) or ("1" in cycles_text), (
                f"page_text tail: {page_text[-600:]!r}"
            )
        finally:
            browser.close()
