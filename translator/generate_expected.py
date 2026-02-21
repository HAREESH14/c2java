"""Generate all snapshot expected files from current translator output."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
import java_to_c, c_to_java

SAMPLES  = os.path.join(os.path.dirname(__file__), 'samples')
EXPECTED = os.path.join(os.path.dirname(__file__), 'tests', 'expected')

pairs = [
    ('fibonacci.java',       'fibonacci_j2c.expected',       'j2c'),
    ('calculator.c',         'calculator_c2j.expected',      'c2j'),
    ('all_features.java',    'all_features_j2c.expected',    'j2c'),
    ('all_features.c',       'all_features_c2j.expected',    'c2j'),
    ('hashmap_strings.java', 'hashmap_strings_j2c.expected', 'j2c'),
]

for src, exp, direction in pairs:
    path = os.path.join(SAMPLES, src)
    if direction == 'j2c':
        out = java_to_c.translate_file(path)
    else:
        out = c_to_java.translate_file(path)
    exp_path = os.path.join(EXPECTED, exp)
    with open(exp_path, 'w', encoding='utf-8') as f:
        f.write(out)
    print(f"  [OK] {src:30s} -> {exp} ({len(out)} chars)")

print(f"\nGenerated {len(pairs)} expected files.")
