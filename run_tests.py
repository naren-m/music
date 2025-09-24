#!/usr/bin/env python3
"""
Test Runner for Carnatic Learning Application
Comprehensive test execution with reporting and validation
"""

import sys
import os
import subprocess
import argparse
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


class TestRunner:
    """Comprehensive test runner with multiple execution modes."""
    
    def __init__(self):
        self.project_root = project_root
        self.test_dir = self.project_root / "tests"
        self.coverage_dir = self.project_root / "coverage_html"
        
    def run_unit_tests(self, verbose=False):
        """Run unit tests only."""
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/test_models.py",
            "tests/test_audio_engine.py",
            "-m", "unit",
            "--tb=short"
        ]
        
        if verbose:
            cmd.append("-v")
        
        return self._execute_command(cmd, "Unit Tests")
    
    def run_integration_tests(self, verbose=False):
        """Run API integration tests."""
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/test_api_integration.py",
            "-m", "integration",
            "--tb=short"
        ]
        
        if verbose:
            cmd.append("-v")
        
        return self._execute_command(cmd, "Integration Tests")
    
    def run_e2e_tests(self, headless=True, verbose=False):
        """Run end-to-end tests with Playwright."""
        # Install Playwright browsers if needed
        self._install_playwright_browsers()
        
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/test_e2e_playwright.py",
            "-m", "e2e",
            "--tb=short"
        ]
        
        if verbose:
            cmd.append("-v")
        
        if not headless:
            cmd.extend(["--headed"])
        
        return self._execute_command(cmd, "End-to-End Tests")
    
    def run_performance_tests(self, verbose=False):
        """Run performance benchmarking tests."""
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/",
            "-m", "performance",
            "--tb=short",
            "--durations=0"
        ]
        
        if verbose:
            cmd.append("-v")
        
        return self._execute_command(cmd, "Performance Tests")
    
    def run_accessibility_tests(self, verbose=False):
        """Run accessibility compliance tests."""
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/test_e2e_playwright.py::TestAccessibility",
            "-m", "accessibility",
            "--tb=short"
        ]
        
        if verbose:
            cmd.append("-v")
        
        return self._execute_command(cmd, "Accessibility Tests")
    
    def run_all_tests(self, verbose=False, coverage=True):
        """Run comprehensive test suite."""
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/",
            "--tb=short"
        ]
        
        if verbose:
            cmd.append("-v")
        
        if coverage:
            cmd.extend([
                "--cov=core",
                "--cov=api", 
                "--cov=modules",
                "--cov-report=html",
                "--cov-report=term-missing",
                "--cov-report=xml"
            ])
        
        return self._execute_command(cmd, "Complete Test Suite")
    
    def run_quick_tests(self):
        """Run quick smoke tests for CI/CD."""
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/test_models.py",
            "tests/test_audio_engine.py::TestAdvancedPitchDetector::test_pitch_detector_initialization",
            "tests/test_api_integration.py::TestAuthenticationAPI::test_register_endpoint",
            "-x",  # Stop on first failure
            "--tb=line"
        ]
        
        return self._execute_command(cmd, "Quick Smoke Tests")
    
    def lint_and_format(self):
        """Run code linting and formatting checks."""
        results = {}
        
        # Black formatting check
        black_cmd = [sys.executable, "-m", "black", "--check", "core/", "api/", "modules/"]
        results['black'] = self._execute_command(black_cmd, "Black Formatting", capture_output=True)
        
        # Flake8 linting
        flake8_cmd = [sys.executable, "-m", "flake8", "core/", "api/", "modules/"]
        results['flake8'] = self._execute_command(flake8_cmd, "Flake8 Linting", capture_output=True)
        
        # MyPy type checking
        mypy_cmd = [sys.executable, "-m", "mypy", "core/", "api/", "modules/"]
        results['mypy'] = self._execute_command(mypy_cmd, "MyPy Type Checking", capture_output=True)
        
        return results
    
    def generate_test_report(self):
        """Generate comprehensive test report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.project_root / f"test_report_{timestamp}.json"
        
        # Run all test categories
        results = {
            'timestamp': timestamp,
            'unit_tests': self.run_unit_tests(),
            'integration_tests': self.run_integration_tests(),
            'performance_tests': self.run_performance_tests(),
            'lint_results': self.lint_and_format()
        }
        
        # Calculate overall status
        all_passed = all(
            result.get('success', False) 
            for category in ['unit_tests', 'integration_tests', 'performance_tests']
            for result in [results[category]]
        )
        
        results['overall_status'] = 'PASSED' if all_passed else 'FAILED'
        
        # Save report
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📊 Test report saved to: {report_file}")
        print(f"🎯 Overall Status: {results['overall_status']}")
        
        return results
    
    def _execute_command(self, cmd, description, capture_output=False):
        """Execute command and return results."""
        print(f"\n🔄 Running {description}...")
        print(f"📝 Command: {' '.join(cmd)}")
        
        try:
            if capture_output:
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
            else:
                result = subprocess.run(cmd, cwd=self.project_root)
            
            success = result.returncode == 0
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"📊 {description}: {status}")
            
            return {
                'success': success,
                'returncode': result.returncode,
                'command': ' '.join(cmd),
                'description': description
            }
            
        except Exception as e:
            print(f"❌ Error running {description}: {e}")
            return {
                'success': False,
                'error': str(e),
                'command': ' '.join(cmd),
                'description': description
            }
    
    def _install_playwright_browsers(self):
        """Install Playwright browsers if needed."""
        try:
            install_cmd = [sys.executable, "-m", "playwright", "install", "chromium"]
            subprocess.run(install_cmd, check=True, capture_output=True)
            print("🌐 Playwright browsers installed successfully")
        except subprocess.CalledProcessError:
            print("⚠️  Warning: Could not install Playwright browsers")
        except FileNotFoundError:
            print("⚠️  Warning: Playwright not found, skipping browser installation")


def main():
    """Main test runner entry point."""
    parser = argparse.ArgumentParser(description="Carnatic Learning Application Test Runner")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--e2e", action="store_true", help="Run end-to-end tests")
    parser.add_argument("--performance", action="store_true", help="Run performance tests")
    parser.add_argument("--accessibility", action="store_true", help="Run accessibility tests")
    parser.add_argument("--quick", action="store_true", help="Run quick smoke tests")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--lint", action="store_true", help="Run linting and formatting checks")
    parser.add_argument("--report", action="store_true", help="Generate comprehensive test report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--headed", action="store_true", help="Run Playwright tests in headed mode")
    parser.add_argument("--no-coverage", action="store_true", help="Skip coverage reporting")
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    print("🎵 Carnatic Learning Application Test Runner")
    print("=" * 50)
    
    # Default to quick tests if no specific test type is specified
    if not any([args.unit, args.integration, args.e2e, args.performance, 
                args.accessibility, args.quick, args.all, args.lint, args.report]):
        args.quick = True
    
    results = []
    
    if args.unit:
        results.append(runner.run_unit_tests(verbose=args.verbose))
    
    if args.integration:
        results.append(runner.run_integration_tests(verbose=args.verbose))
    
    if args.e2e:
        results.append(runner.run_e2e_tests(headless=not args.headed, verbose=args.verbose))
    
    if args.performance:
        results.append(runner.run_performance_tests(verbose=args.verbose))
    
    if args.accessibility:
        results.append(runner.run_accessibility_tests(verbose=args.verbose))
    
    if args.quick:
        results.append(runner.run_quick_tests())
    
    if args.all:
        results.append(runner.run_all_tests(verbose=args.verbose, coverage=not args.no_coverage))
    
    if args.lint:
        lint_results = runner.lint_and_format()
        results.extend(lint_results.values())
    
    if args.report:
        runner.generate_test_report()
        return
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Execution Summary")
    print("=" * 50)
    
    passed = sum(1 for r in results if r.get('success', False))
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    if total > 0:
        success_rate = (passed / total) * 100
        print(f"📈 Success Rate: {success_rate:.1f}%")
    
    # Exit with appropriate code
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()