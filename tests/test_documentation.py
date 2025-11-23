#!/usr/bin/env python3
"""
Documentation Validation Tests

Tests documentation files for consistency and accuracy.
Can be run in Docker without hardware dependencies.
"""

import sys
from pathlib import Path
import re

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def test_documentation_files_exist():
    """Test that all expected documentation files exist"""
    print("\n" + "="*60)
    print("DOCUMENTATION FILES TEST")
    print("="*60)

    expected_docs = [
        "README.md",
        "docs/CONFIGURATION.md",
        "docs/TRAINING_CUSTOM_SPELLS.md",
        "docs/REFACTORING_METRICS.md",
    ]

    all_exist = True

    for doc_path in expected_docs:
        full_path = PROJECT_ROOT / doc_path
        if full_path.exists():
            print(f"✓ {doc_path}")
        else:
            print(f"✗ {doc_path} missing")
            all_exist = False

    if all_exist:
        print("\n✓ All documentation files exist!")
        return True
    else:
        print("\n✗ Some documentation files missing")
        return False


def test_no_old_filenames():
    """Test that documentation uses new snake_case filenames"""
    print("\n" + "="*60)
    print("FILENAME REFERENCE TEST")
    print("="*60)

    docs_to_check = [
        "README.md",
        "docs/CONFIGURATION.md",
        "docs/TRAINING_CUSTOM_SPELLS.md",
    ]

    old_patterns = [
        r"HarryPotterWandcv\.py(?!.*→)",  # Ignore in "renamed from" context
        r"HarryPotterWandsklearn\.py(?!.*→)",
    ]

    issues = []

    for doc_path in docs_to_check:
        full_path = PROJECT_ROOT / doc_path
        if not full_path.exists():
            continue

        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')

        for pattern in old_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                # Find line number
                line_num = content[:match.start()].count('\n') + 1
                line_content = lines[line_num - 1].strip()
                issues.append((doc_path, line_num, line_content))

    if issues:
        print("✗ Found old filename references:")
        for doc, line, content in issues:
            print(f"  {doc}:{line} - {content[:60]}...")
        return False
    else:
        print("✓ All filename references use snake_case!")
        return True


def test_mermaid_diagrams():
    """Test that Mermaid diagrams are present"""
    print("\n" + "="*60)
    print("MERMAID DIAGRAM TEST")
    print("="*60)

    docs_with_diagrams = {
        "README.md": 3,  # Expected: System Architecture, Installation Flow, Detection Pipeline
        "docs/CONFIGURATION.md": 1,  # Expected: Config Hierarchy
        "docs/TRAINING_CUSTOM_SPELLS.md": 1,  # Expected: Training Pipeline
        "docs/REFACTORING_METRICS.md": 6,  # Expected: Various refactoring diagrams
    }

    all_correct = True

    for doc_path, expected_count in docs_with_diagrams.items():
        full_path = PROJECT_ROOT / doc_path
        if not full_path.exists():
            print(f"⚠️  {doc_path} not found")
            continue

        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()

        actual_count = content.count('```mermaid')

        if actual_count >= expected_count:
            print(f"✓ {doc_path}: {actual_count} diagrams (expected {expected_count}+)")
        else:
            print(f"✗ {doc_path}: {actual_count} diagrams (expected {expected_count}+)")
            all_correct = False

    if all_correct:
        print("\n✓ All expected Mermaid diagrams present!")
        return True
    else:
        print("\n✗ Some Mermaid diagrams missing")
        return False


def test_internal_links():
    """Test internal documentation links (basic check)"""
    print("\n" + "="*60)
    print("INTERNAL LINKS TEST")
    print("="*60)

    readme_path = PROJECT_ROOT / "README.md"

    if not readme_path.exists():
        print("⚠️  README.md not found")
        return None

    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find markdown links to other docs
    doc_links = re.findall(r'\[.*?\]\((docs/[^\)]+\.md)\)', content)

    broken_links = []

    for link in doc_links:
        full_path = PROJECT_ROOT / link
        if not full_path.exists():
            broken_links.append(link)

    if broken_links:
        print("✗ Broken internal links found:")
        for link in broken_links:
            print(f"  - {link}")
        return False
    else:
        print(f"✓ All {len(doc_links)} internal links valid!")
        return True


if __name__ == "__main__":
    print("\n" + "="*60)
    print("INTERACTIVE WAND - DOCUMENTATION TESTS")
    print("="*60)

    results = {
        "Documentation files exist": test_documentation_files_exist(),
        "No old filenames": test_no_old_filenames(),
        "Mermaid diagrams": test_mermaid_diagrams(),
        "Internal links": test_internal_links(),
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
        print("\n✓ ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print("\n✗ SOME TESTS FAILED")
        sys.exit(1)
