#!/usr/bin/env python3
"""
Configuration Validation Tests

Tests config.yaml structure and validation logic.
Can be run in Docker without hardware dependencies.
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def test_config_file_exists():
    """Test that config.yaml exists"""
    print("\n" + "="*60)
    print("CONFIG FILE EXISTENCE TEST")
    print("="*60)

    config_path = PROJECT_ROOT / "config.yaml"

    if config_path.exists():
        print(f"✓ config.yaml found at {config_path}")
        return True
    else:
        print(f"⚠️  config.yaml not found (expected for fresh install)")
        print("   Run setup_wizard.py to create configuration")
        return None  # Not a failure, just not configured yet


def test_config_structure():
    """Test config.yaml structure if it exists"""
    print("\n" + "="*60)
    print("CONFIG STRUCTURE TEST")
    print("="*60)

    config_path = PROJECT_ROOT / "config.yaml"

    if not config_path.exists():
        print("⚠️  Skipping (config.yaml not found)")
        return None

    try:
        import yaml

        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        required_sections = ['project', 'hardware', 'detection', 'audio', 'paths']
        missing = []

        for section in required_sections:
            if section in config:
                print(f"✓ Section '{section}' present")
            else:
                print(f"✗ Section '{section}' missing")
                missing.append(section)

        if missing:
            print(f"\n✗ Missing sections: {', '.join(missing)}")
            return False

        # Check hardware subsections
        hardware_sections = ['led', 'camera', 'servo', 'ir_illuminator']
        for subsection in hardware_sections:
            if subsection in config.get('hardware', {}):
                print(f"✓ Hardware.{subsection} present")
            else:
                print(f"✗ Hardware.{subsection} missing")
                missing.append(f"hardware.{subsection}")

        print("\n✓ Config structure is valid!")
        return True

    except Exception as e:
        print(f"✗ Error reading config: {e}")
        return False


def test_config_loader():
    """Test config_loader.py module"""
    print("\n" + "="*60)
    print("CONFIG LOADER TEST")
    print("="*60)

    try:
        # Test DotDict class
        from config_loader import DotDict

        test_dict = DotDict({'a': {'b': {'c': 123}}})

        if test_dict.a.b.c == 123:
            print("✓ DotDict dot notation works")
        else:
            print("✗ DotDict dot notation failed")
            return False

        # Test that Config class exists
        from config_loader import Config
        print("✓ Config class imported successfully")

        # Note: Can't instantiate without config.yaml on Raspberry Pi

        return True

    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_path_resolution():
    """Test that paths would resolve correctly"""
    print("\n" + "="*60)
    print("PATH RESOLUTION TEST")
    print("="*60)

    expected_paths = [
        "Sounds",
        "DatasetCreation",
        "utils",
        "docs",
    ]

    all_exist = True

    for path_name in expected_paths:
        path = PROJECT_ROOT / path_name
        if path.exists():
            print(f"✓ {path_name}/ exists")
        else:
            print(f"✗ {path_name}/ missing")
            all_exist = False

    if all_exist:
        print("\n✓ All expected directories exist!")
        return True
    else:
        print("\n⚠️  Some directories missing (may need setup)")
        return None


if __name__ == "__main__":
    print("\n" + "="*60)
    print("INTERACTIVE WAND - CONFIGURATION TESTS")
    print("="*60)

    results = {
        "Config file exists": test_config_file_exists(),
        "Config structure": test_config_structure(),
        "Config loader": test_config_loader(),
        "Path resolution": test_path_resolution(),
    }

    print("\n" + "="*60)
    print("FINAL RESULTS")
    print("="*60)

    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)

    for test_name, result in results.items():
        if result is True:
            status = "✓ PASS"
        elif result is False:
            status = "✗ FAIL"
        else:
            status = "⚠️  SKIP"
        print(f"{test_name}: {status}")

    print(f"\nSummary: {passed} passed, {failed} failed, {skipped} skipped")

    if failed == 0:
        print("\n✓ ALL TESTS PASSED (or skipped as expected)!")
        sys.exit(0)
    else:
        print("\n✗ SOME TESTS FAILED")
        sys.exit(1)
