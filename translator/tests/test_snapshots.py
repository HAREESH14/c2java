# tests/test_snapshots.py
# Snapshot tests: compare translator output against saved .expected files.
# This catches regressions — if the output changes, the test fails.
# To update expected files after intentional changes:
#   uv run python -c "import sys; sys.path.insert(0,'src'); import java_to_c; \
#     open('tests/expected/fibonacci_j2c.expected','w').write(java_to_c.translate_file('samples/fibonacci.java'))"
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


def test_fibonacci_java_to_c_snapshot():
    """fibonacci.java -> C  must match saved expected output."""
    actual   = java_to_c.translate_file(os.path.join(SAMPLES_DIR, 'fibonacci.java'))
    expected = _read(os.path.join(EXPECTED_DIR, 'fibonacci_j2c.expected'))
    assert actual == expected, (
        "Java->C output changed! If intentional, update the .expected file.\n"
        f"Run: uv run python -c \"import sys; sys.path.insert(0,'src'); "
        f"import java_to_c; open('tests/expected/fibonacci_j2c.expected','w',"
        f"encoding='utf-8').write(java_to_c.translate_file('samples/fibonacci.java'))\""
    )


def test_calculator_c_to_java_snapshot():
    """calculator.c -> Java  must match saved expected output."""
    actual   = c_to_java.translate_file(os.path.join(SAMPLES_DIR, 'calculator.c'))
    expected = _read(os.path.join(EXPECTED_DIR, 'calculator_c2j.expected'))
    assert actual == expected, (
        "C->Java output changed! If intentional, update the .expected file.\n"
        f"Run: uv run python -c \"import sys; sys.path.insert(0,'src'); "
        f"import c_to_java; open('tests/expected/calculator_c2j.expected','w',"
        f"encoding='utf-8').write(c_to_java.translate_file('samples/calculator.c'))\""
    )
