# tests/test_snapshots.py
# Snapshot tests: compare translator output against saved .expected files.
# To update expected files: uv run python generate_expected.py
import sys, os, pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import java_to_c
import c_to_java

TESTS_DIR    = os.path.dirname(__file__)
EXPECTED_DIR = os.path.join(TESTS_DIR, 'expected')
SAMPLES_DIR  = os.path.join(TESTS_DIR, '..', 'samples')


def _read(path):
    with open(path, encoding='utf-8') as f:
        return f.read()


def _check(actual, expected_file):
    expected = _read(os.path.join(EXPECTED_DIR, expected_file))
    assert actual == expected, (
        f"Output changed vs {expected_file}! "
        f"If intentional, run: uv run python generate_expected.py"
    )


# ── Java -> C snapshots ──────────────────────────────────────────────────────

def test_fibonacci_j2c_snapshot():
    actual = java_to_c.translate_file(os.path.join(SAMPLES_DIR, 'fibonacci.java'))
    _check(actual, 'fibonacci_j2c.expected')


def test_all_features_j2c_snapshot():
    actual = java_to_c.translate_file(os.path.join(SAMPLES_DIR, 'all_features.java'))
    _check(actual, 'all_features_j2c.expected')


def test_hashmap_strings_j2c_snapshot():
    actual = java_to_c.translate_file(os.path.join(SAMPLES_DIR, 'hashmap_strings.java'))
    _check(actual, 'hashmap_strings_j2c.expected')


# ── C -> Java snapshots ──────────────────────────────────────────────────────

def test_calculator_c2j_snapshot():
    actual = c_to_java.translate_file(os.path.join(SAMPLES_DIR, 'calculator.c'))
    _check(actual, 'calculator_c2j.expected')


def test_all_features_c2j_snapshot():
    actual = c_to_java.translate_file(os.path.join(SAMPLES_DIR, 'all_features.c'))
    _check(actual, 'all_features_c2j.expected')
