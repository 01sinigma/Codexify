#!/usr/bin/env python3
"""
Codexify Test Runner

This script provides a convenient way to run the Codexify test suite
with various options for different testing scenarios.
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n🔄 {description}...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print("Output:")
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        if e.stdout:
            print("Stdout:")
            print(e.stdout)
        if e.stderr:
            print("Stderr:")
            print(e.stderr)
        return False


def install_test_dependencies():
    """Install testing dependencies."""
    return run_command(
        [sys.executable, "-m", "pip", "install", "-r", "requirements-test.txt"],
        "Installing test dependencies"
    )


def run_unit_tests(verbose=False, coverage=False, parallel=False):
    """Run unit tests."""
    cmd = [sys.executable, "-m", "pytest", "tests/"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend(["--cov=codexify", "--cov-report=html", "--cov-report=term"])
    
    if parallel:
        cmd.extend(["-n", "auto"])
    
    return run_command(cmd, "Running unit tests")


def run_integration_tests(verbose=False):
    """Run integration tests."""
    cmd = [sys.executable, "-m", "pytest", "tests/", "-m", "integration"]
    
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd, "Running integration tests")


def run_specific_test(test_path, verbose=False):
    """Run a specific test file or test function."""
    cmd = [sys.executable, "-m", "pytest", test_path]
    
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd, f"Running specific test: {test_path}")


def run_linting():
    """Run code linting and formatting checks."""
    # Run flake8
    flake8_success = run_command(
        [sys.executable, "-m", "flake8", "codexify/", "tests/"],
        "Running flake8 linting"
    )
    
    # Run black check
    black_success = run_command(
        [sys.executable, "-m", "black", "--check", "codexify/", "tests/"],
        "Running black formatting check"
    )
    
    # Run isort check
    isort_success = run_command(
        [sys.executable, "-m", "isort", "--check-only", "codexify/", "tests/"],
        "Running isort import sorting check"
    )
    
    return flake8_success and black_success and isort_success


def run_type_checking():
    """Run mypy type checking."""
    return run_command(
        [sys.executable, "-m", "mypy", "codexify/"],
        "Running mypy type checking"
    )


def run_coverage_report():
    """Generate and display coverage report."""
    return run_command(
        [sys.executable, "-m", "coverage", "report"],
        "Generating coverage report"
    )


def run_all_checks(verbose=False, coverage=False, parallel=False):
    """Run all checks and tests."""
    print("🚀 Starting comprehensive Codexify testing and quality checks...")
    
    # Install dependencies
    if not install_test_dependencies():
        print("❌ Failed to install test dependencies. Aborting.")
        return False
    
    # Run linting
    if not run_linting():
        print("❌ Linting failed. Please fix code style issues.")
        return False
    
    # Run type checking
    if not run_type_checking():
        print("❌ Type checking failed. Please fix type issues.")
        return False
    
    # Run unit tests
    if not run_unit_tests(verbose, coverage, parallel):
        print("❌ Unit tests failed. Please fix failing tests.")
        return False
    
    # Run integration tests
    if not run_integration_tests(verbose):
        print("❌ Integration tests failed. Please fix failing tests.")
        return False
    
    # Generate coverage report if requested
    if coverage:
        run_coverage_report()
    
    print("\n🎉 All checks completed successfully!")
    return True


def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(
        description="Codexify Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py                    # Run all tests and checks
  python run_tests.py --unit-only        # Run only unit tests
  python run_tests.py --test tests/test_state.py  # Run specific test file
  python run_tests.py --coverage         # Run tests with coverage report
  python run_tests.py --parallel         # Run tests in parallel
  python run_tests.py --lint-only        # Run only linting checks
  python run_tests.py --verbose          # Verbose output
        """
    )
    
    parser.add_argument(
        "--unit-only",
        action="store_true",
        help="Run only unit tests"
    )
    
    parser.add_argument(
        "--integration-only",
        action="store_true",
        help="Run only integration tests"
    )
    
    parser.add_argument(
        "--lint-only",
        action="store_true",
        help="Run only linting and formatting checks"
    )
    
    parser.add_argument(
        "--test",
        type=str,
        help="Run a specific test file or test function"
    )
    
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Generate coverage report"
    )
    
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run tests in parallel (requires pytest-xdist)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="Install test dependencies only"
    )
    
    args = parser.parse_args()
    
    # Check if we're in the right directory
    if not Path("codexify/").exists():
        print("❌ Error: Please run this script from the codexify_project directory")
        print("   Current directory:", Path.cwd())
        sys.exit(1)
    
    # Install dependencies only
    if args.install_deps:
        success = install_test_dependencies()
        sys.exit(0 if success else 1)
    
    # Run specific test
    if args.test:
        success = run_specific_test(args.test, args.verbose)
        sys.exit(0 if success else 1)
    
    # Run only linting
    if args.lint_only:
        success = run_linting() and run_type_checking()
        sys.exit(0 if success else 1)
    
    # Run only unit tests
    if args.unit_only:
        success = run_unit_tests(args.verbose, args.coverage, args.parallel)
        sys.exit(0 if success else 1)
    
    # Run only integration tests
    if args.integration_only:
        success = run_integration_tests(args.verbose)
        sys.exit(0 if success else 1)
    
    # Run all checks (default)
    success = run_all_checks(args.verbose, args.coverage, args.parallel)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
