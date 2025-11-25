#!/usr/bin/env python3
"""
Syntax and Import Validation Tests

Tests that all Python files compile correctly and imports work.
Can be run in Docker without hardware dependencies.
"""

import os
import sys
import py_compile
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def test_python_syntax():
    """Test that all Python files compile without syntax errors"""
    print("\n" + "="*60)
    print("SYNTAX VALIDATION TEST")
    print("="*60)

    python_files = [
        "harry_potter_wand_cv.py",
        "harry_potter_wand_sklearn.py",
        "config_loader.py",
        "setup_wizard.py",
        "test_setup.py",
        "utils/terminal_ui.py",
        "utils/hardware_checks.py",
        "utils/config_builder.py",
        "utils/animations.py",
        "utils/audio.py",
        "DatasetCreation/train_spell_classifier.py",
    ]

    errors = []
    passed = 0

    for filepath in python_files:
        full_path = PROJECT_ROOT / filepath
        if not full_path.exists():
            print(f"⚠️  SKIP: {filepath} (file not found)")
            continue

        try:
            py_compile.compile(str(full_path), doraise=True)
            print(f"✓ {filepath}")
            passed += 1
        except py_compile.PyCompileError as e:
            print(f"✗ {filepath}: {e}")
            errors.append((filepath, str(e)))

    print("\n" + "-"*60)
    print(f"Results: {passed} passed, {len(errors)} failed")

    if errors:
        print("\nErrors:")
        for filepath, error in errors:
            print(f"  {filepath}: {error}")
        return False

    print("✓ All files compile successfully!")
    return True


def test_imports():
    """Test that critical imports work (non-hardware)"""
    print("\n" + "="*60)
    print("IMPORT VALIDATION TEST")
    print("="*60)

    imports_to_test = [
        ("config_loader", "Config loader"),
        ("utils.terminal_ui", "Terminal UI"),
        ("utils.config_builder", "Config builder"),
        ("utils.animations", "Animations (will fail import but syntax OK)"),
        ("utils.audio", "Audio (will fail import but syntax OK)"),
    ]

    passed = 0
    failed = 0

    for module_name, description in imports_to_test:
        try:
            __import__(module_name)
            print(f"✓ {description}: {module_name}")
            passed += 1
        except ImportError as e:
            # Expected for hardware-dependent modules
            if "picamera2" in str(e) or "pygame" in str(e) or "pi5neo" in str(e) or "pandas" in str(e):
                print(f"⚠️  {description}: {module_name} (hardware dependency expected)")
                passed += 1
            else:
                print(f"✗ {description}: {module_name} - {e}")
                failed += 1
        except Exception as e:
            print(f"✗ {description}: {module_name} - {e}")
            failed += 1

    print("\n" + "-"*60)
    print(f"Results: {passed} passed, {failed} failed")

    if failed > 0:
        return False

    print("✓ All critical imports successful!")
    return True


if __name__ == "__main__":
    print("\n" + "="*60)
    print("INTERACTIVE WAND - SYNTAX & IMPORT TESTS")
    print("="*60)

    syntax_ok = test_python_syntax()
    imports_ok = test_imports()

    print("\n" + "="*60)
    print("FINAL RESULTS")
    print("="*60)
    print(f"Syntax Validation: {'✓ PASS' if syntax_ok else '✗ FAIL'}")
    print(f"Import Validation: {'✓ PASS' if imports_ok else '✗ FAIL'}")

    if syntax_ok and imports_ok:
        print("\n✓ ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print("\n✗ SOME TESTS FAILED")
        sys.exit(1)
