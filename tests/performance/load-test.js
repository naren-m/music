// Carnatic Music Learning Platform - Performance Load Testing
// K6 Load Testing Script

import http from 'k6/http';
import ws from 'k6/ws';
import { check, sleep } from 'k6';
import { Counter, Rate, Trend } from 'k6/metrics';

// Custom metrics
const connectionErrors = new Counter('connection_errors');
const audioProcessingTime = new Trend('audio_processing_time', true);
const websocketConnections = new Counter('websocket_connections');
const apiResponseTime = new Trend('api_response_time', true);

// Test configuration
export const options = {
  stages: [
    { duration: '2m', target: 10 }, // Ramp up to 10 users
    { duration: '5m', target: 10 }, // Stay at 10 users
    { duration: '2m', target: 20 }, // Ramp up to 20 users
    { duration: '5m', target: 20 }, // Stay at 20 users
    { duration: '2m', target: 50 }, // Ramp up to 50 users
    { duration: '10m', target: 50 }, // Stay at 50 users
    { duration: '5m', target: 0 }, // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% of requests under 500ms
    http_req_failed: ['rate<0.01'], // Error rate under 1%
    websocket_connecting_time: ['p(95)<1000'], // WebSocket connection under 1s
    audio_processing_time: ['p(95)<100'], // Audio processing under 100ms
    connection_errors: ['count<10'], // Less than 10 connection errors total
  },
};

const BASE_URL = 'http://localhost:5001';
const WS_URL = 'ws://localhost:5001';

// Test data
const sampleAudioData = new Array(2048).fill(0).map(() => Math.random() * 2 - 1);

export default function () {
  const testScenario = Math.random();

  if (testScenario < 0.4) {
    // 40% API Testing
    testAPIEndpoints();
  } else if (testScenario < 0.8) {
    // 40% WebSocket Audio Processing
    testWebSocketAudioProcessing();
  } else {
    // 20% Mixed load testing
    testMixedWorkflow();
  }

  sleep(1);
}

function testAPIEndpoints() {
  const endpoints = [
    '/api/v1/health',
    '/api/v1/auth/status',
    '/',
    '/carnatic',
    '/learning'
  ];

  endpoints.forEach(endpoint => {
    const startTime = new Date().getTime();

    const response = http.get(`${BASE_URL}${endpoint}`, {
      timeout: '10s',
      tags: { endpoint: endpoint },
    });

    const duration = new Date().getTime() - startTime;
    apiResponseTime.add(duration);

    const success = check(response, {
      [`${endpoint} status is 200`]: (r) => r.status === 200,
      [`${endpoint} response time < 1s`]: () => duration < 1000,
    });

    if (!success) {
      connectionErrors.add(1);
    }
  });
}

function testWebSocketAudioProcessing() {
  const url = `${WS_URL}/ws/carnatic`;

  const response = ws.connect(url, {}, function (socket) {
    websocketConnections.add(1);

    socket.on('open', () => {
      console.log('WebSocket connected for audio processing');

      // Simulate audio chunk sending
      for (let i = 0; i < 10; i++) {
        const startTime = new Date().getTime();

        socket.send(JSON.stringify({
          type: 'audio_chunk',
          data: sampleAudioData,
          sampleRate: 44100,
          timestamp: Date.now()
        }));

        const processingTime = new Date().getTime() - startTime;
        audioProcessingTime.add(processingTime);

        sleep(0.1); // 100ms between chunks
      }
    });

    socket.on('message', (data) => {
      try {
        const response = JSON.parse(data);

        check(response, {
          'WebSocket response has frequency': (r) => r.frequency !== undefined,
          'WebSocket response has note': (r) => r.note !== undefined,
          'WebSocket processing time acceptable': () => {
            const latency = Date.now() - response.timestamp;
            return latency < 200; // Under 200ms total latency
          }
        });

      } catch (e) {
        connectionErrors.add(1);
        console.error('Failed to parse WebSocket response:', e);
      }
    });

    socket.on('error', (e) => {
      connectionErrors.add(1);
      console.error('WebSocket error:', e);
    });

    socket.setTimeout(() => {
      socket.close();
    }, 30000); // Close after 30 seconds
  });

  check(response, {
    'WebSocket connection successful': (r) => r && r.status === 101,
  });
}

function testMixedWorkflow() {
  // Simulate a complete user workflow

  // 1. Load main page
  let response = http.get(`${BASE_URL}/`);
  check(response, {
    'Main page loads': (r) => r.status === 200,
    'Main page has title': (r) => r.body.includes('Carnatic Music'),
  });

  sleep(1);

  // 2. Check API health
  response = http.get(`${BASE_URL}/api/v1/health`);
  check(response, {
    'Health check successful': (r) => r.status === 200,
    'Health response valid': (r) => {
      try {
        const data = JSON.parse(r.body);
        return data.status === 'healthy';
      } catch (e) {
        return false;
      }
    },
  });

  sleep(0.5);

  // 3. Load carnatic page
  response = http.get(`${BASE_URL}/carnatic`);
  check(response, {
    'Carnatic page loads': (r) => r.status === 200,
    'Carnatic page has shruti content': (r) => r.body.includes('shruti') || r.body.includes('Shruti'),
  });

  sleep(1);

  // 4. Test WebSocket connection briefly
  const wsUrl = `${WS_URL}/ws/carnatic`;
  ws.connect(wsUrl, {}, function (socket) {
    websocketConnections.add(1);

    socket.on('open', () => {
      // Send a few audio chunks
      for (let i = 0; i < 3; i++) {
        socket.send(JSON.stringify({
          type: 'audio_chunk',
          data: sampleAudioData.slice(0, 512), // Smaller chunks for mixed testing
          sampleRate: 44100,
          timestamp: Date.now()
        }));
        sleep(0.2);
      }

      socket.close();
    });

    socket.on('error', (e) => {
      connectionErrors.add(1);
    });
  });
}

// Setup function run once at the beginning
export function setup() {
  console.log('🚀 Starting Carnatic Music Learning Platform Load Test');

  // Verify the application is running
  const response = http.get(`${BASE_URL}/api/v1/health`);
  if (response.status !== 200) {
    throw new Error(`Application not ready. Health check failed with status: ${response.status}`);
  }

  console.log('✅ Application health check passed, starting load test...');
  return { baseUrl: BASE_URL };
}

// Teardown function run once at the end
export function teardown(data) {
  console.log('🏁 Load test completed');
  console.log(`📊 Base URL tested: ${data.baseUrl}`);
}

// Custom function to handle different user types
export function handleSummary(data) {
  return {
    'stdout': textSummary(data, { indent: ' ', enableColors: true }),
    'performance-summary.json': JSON.stringify(data, null, 2),
    'performance-summary.html': htmlReport(data),
  };
}

function textSummary(data, options = {}) {
  const indent = options.indent || '';
  const colors = options.enableColors || false;

  let summary = '\n' + indent + '📈 Carnatic Music Learning Platform - Performance Test Summary\n';
  summary += indent + '================================================================\n\n';

  // Test execution info
  summary += indent + `🕒 Test Duration: ${Math.round(data.state.testRunDurationMs / 1000)}s\n`;
  summary += indent + `👥 Max VUs: ${data.metrics.vus_max.values.max}\n`;
  summary += indent + `🔄 Iterations: ${data.metrics.iterations.values.count}\n\n`;

  // HTTP metrics
  summary += indent + '🌐 HTTP Performance:\n';
  summary += indent + `   • Request Duration (avg): ${Math.round(data.metrics.http_req_duration.values.avg)}ms\n`;
  summary += indent + `   • Request Duration (p95): ${Math.round(data.metrics.http_req_duration.values['p(95)'])}ms\n`;
  summary += indent + `   • Request Rate: ${Math.round(data.metrics.http_reqs.values.rate)}/s\n`;
  summary += indent + `   • Failed Requests: ${data.metrics.http_req_failed.values.rate * 100}%\n\n`;

  // WebSocket metrics
  if (data.metrics.websocket_connections) {
    summary += indent + '🔗 WebSocket Performance:\n';
    summary += indent + `   • Connections: ${data.metrics.websocket_connections.values.count}\n`;

    if (data.metrics.audio_processing_time) {
      summary += indent + `   • Audio Processing (avg): ${Math.round(data.metrics.audio_processing_time.values.avg)}ms\n`;
      summary += indent + `   • Audio Processing (p95): ${Math.round(data.metrics.audio_processing_time.values['p(95)'])}ms\n`;
    }
  }

  // Error summary
  if (data.metrics.connection_errors) {
    summary += indent + `❌ Connection Errors: ${data.metrics.connection_errors.values.count}\n`;
  }

  return summary;
}

function htmlReport(data) {
  return `<!DOCTYPE html>
<html>
<head>
    <title>Carnatic Music Platform - Performance Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .header { background: #f0f8ff; padding: 20px; border-radius: 8px; }
        .metric { margin: 10px 0; padding: 10px; background: #f9f9f9; border-radius: 4px; }
        .pass { color: green; }
        .fail { color: red; }
        .warn { color: orange; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎵 Carnatic Music Learning Platform</h1>
        <h2>Performance Test Report</h2>
        <p>Generated: ${new Date().toISOString()}</p>
    </div>

    <div class="metric">
        <h3>📊 Test Summary</h3>
        <p>Duration: ${Math.round(data.state.testRunDurationMs / 1000)}s</p>
        <p>Max VUs: ${data.metrics.vus_max.values.max}</p>
        <p>Iterations: ${data.metrics.iterations.values.count}</p>
    </div>

    <div class="metric">
        <h3>🌐 HTTP Performance</h3>
        <p>Average Response Time: ${Math.round(data.metrics.http_req_duration.values.avg)}ms</p>
        <p>95th Percentile: ${Math.round(data.metrics.http_req_duration.values['p(95)'])}ms</p>
        <p>Request Rate: ${Math.round(data.metrics.http_reqs.values.rate)}/s</p>
        <p class="${data.metrics.http_req_failed.values.rate > 0.01 ? 'fail' : 'pass'}">
            Failed Requests: ${(data.metrics.http_req_failed.values.rate * 100).toFixed(2)}%
        </p>
    </div>

    ${data.metrics.websocket_connections ? `
    <div class="metric">
        <h3>🔗 WebSocket Performance</h3>
        <p>Total Connections: ${data.metrics.websocket_connections.values.count}</p>
        ${data.metrics.audio_processing_time ? `
        <p>Audio Processing (avg): ${Math.round(data.metrics.audio_processing_time.values.avg)}ms</p>
        <p class="${data.metrics.audio_processing_time.values['p(95)'] > 100 ? 'warn' : 'pass'}">
            Audio Processing (p95): ${Math.round(data.metrics.audio_processing_time.values['p(95)'])}ms
        </p>
        ` : ''}
    </div>
    ` : ''}
</body>
</html>`;
}