#!/usr/bin/env python3
"""
Run All Tests

Orchestrates all test suites and provides comprehensive results.
Designed to run in Docker without hardware dependencies.
"""

import sys
import subprocess
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def run_test_suite(test_name, test_file):
    """Run a test suite and return results"""
    print("\n" + "="*70)
    print(f"RUNNING: {test_name}")
    print("="*70)

    try:
        result = subprocess.run(
            [sys.executable, str(test_file)],
            capture_output=True,
            text=True,
            timeout=30
        )

        print(result.stdout)
        if result.stderr:
            print(result.stderr)

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        print(f"✗ {test_name} timed out!")
        return False
    except Exception as e:
        print(f"✗ {test_name} error: {e}")
        return False


def main():
    """Run all test suites"""
    print("="*70)
    print(" INTERACTIVE WAND - COMPREHENSIVE TEST SUITE")
    print("="*70)
    print("\nRunning all validation tests...")
    print("Note: Hardware-specific tests will be skipped in Docker environment")

    tests_dir = Path(__file__).parent

    test_suites = [
        ("Syntax & Import Validation", tests_dir / "test_syntax.py"),
        ("Configuration Validation", tests_dir / "test_config.py"),
        ("Utils Module Testing", tests_dir / "test_utils.py"),
        ("Documentation Validation", tests_dir / "test_documentation.py"),
    ]

    results = {}

    for test_name, test_file in test_suites:
        if test_file.exists():
            results[test_name] = run_test_suite(test_name, test_file)
        else:
            print(f"\n⚠️  Skipping {test_name} - {test_file.name} not found")
            results[test_name] = None

    # Summary
    print("\n" + "="*70)
    print(" FINAL TEST SUMMARY")
    print("="*70)

    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)

    for test_name, result in results.items():
        if result is True:
            status = "✓ PASS"
            color = ""
        elif result is False:
            status = "✗ FAIL"
            color = ""
        else:
            status = "⚠️  SKIP"
            color = ""
        print(f"{color}{test_name}: {status}")

    print(f"\n{'='*70}")
    print(f"Total: {len(results)} test suites")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Skipped: {skipped}")
    print(f"{'='*70}")

    if failed == 0:
        print("\n✓ ALL TEST SUITES PASSED!")
        print("\nThe codebase is ready for deployment to Raspberry Pi 5.")
        print("Next steps:")
        print("  1. Transfer code to Raspberry Pi")
        print("  2. Run ./install.sh")
        print("  3. Run python3 setup_wizard.py")
        print("  4. Run python3 test_setup.py (hardware validation)")
        print("  5. Run python3 harry_potter_wand_cv.py")
        return 0
    else:
        print("\n✗ SOME TESTS FAILED - Please review errors above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
