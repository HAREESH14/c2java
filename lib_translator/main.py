#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
#  main.py  —  CLI entry point for the library-based C ↔ Java translator
#
#  Usage:
#    python main.py input.c          → translates C to Java (uses pycparser)
#    python main.py input.java       → translates Java to C (uses javalang)
#    python main.py input.c --ast    → also prints the pycparser AST
#
#  How it differs from the pure-Python version (../src/main.py):
#    • No hand-written lexer or parser — external libraries handle that.
#    • pycparser builds a full, standards-compliant C AST.
#    • javalang builds a full Java AST.
#    • We only write the VISITOR (code generation) layer.
# ─────────────────────────────────────────────────────────────────────────────

import sys
import os
import pathlib


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <input.c | input.java> [--ast]")
        sys.exit(1)

    input_path = sys.argv[1]
    show_ast   = '--ast' in sys.argv

    if not os.path.exists(input_path):
        print(f"Error: file not found: {input_path}")
        sys.exit(1)

    ext = pathlib.Path(input_path).suffix.lower()

    print("=" * 55)
    print("  C ↔ JAVA TRANSLATOR  (Library-Based: pycparser / javalang)")
    print("=" * 55)

    # ── C → Java ──────────────────────────────────────────────────────────────
    if ext == '.c':
        try:
            import c_to_java
        except ImportError:
            print("Error: pycparser not installed. Run:  pip install pycparser")
            sys.exit(1)

        print(f"\nMode: C → Java")
        print(f"Input:  {input_path}")
        print(f"Parser: pycparser (external library)\n")

        if show_ast:
            # Show the raw pycparser AST before translation
            try:
                import pycparser
                fake_libc = os.path.join(
                    os.path.dirname(pycparser.__file__),
                    'utils', 'fake_libc_include'
                )
                ast = pycparser.parse_file(
                    input_path,
                    use_cpp=True,
                    cpp_path='gcc',
                    cpp_args=['-E', f'-I{fake_libc}']
                )
                print("── pycparser AST ──────────────────────────────────")
                ast.show(attrnames=True, nodenames=True)
                print()
            except Exception as e:
                print(f"[AST] Could not show AST (needs gcc on PATH): {e}\n")

        # Try full translation with preprocessor first, fall back to string mode
        try:
            java_code = c_to_java.translate_file(input_path)
        except Exception as e:
            print(f"[Note] Full preprocessing failed ({e})")
            print("[Note] Falling back to direct parse (stripping includes & comments)\n")
            with open(input_path, 'r', encoding='utf-8') as f:
                src = f.read()

            import re
            def strip_comments(text):
                # Regex to match //... and /*...*/
                pattern = r'//.*?$|/\*.*?\*/'
                return re.sub(pattern, '', text, flags=re.MULTILINE | re.DOTALL)

            # Strip includes and comments
            lines = [l for l in src.splitlines() if not l.strip().startswith('#include')]
            clean_src = strip_comments('\n'.join(lines))
            
            java_code = c_to_java.translate_string(clean_src)


        print("── GENERATED JAVA CODE ─────────────────────────────")
        print(java_code)

        # Save output
        out_path = pathlib.Path(input_path).stem + '_lib.java'
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(java_code)
        print(f"\n✓ Saved to {out_path}")

    # ── Java → C ──────────────────────────────────────────────────────────────
    elif ext == '.java':
        try:
            import java_to_c
        except ImportError:
            print("Error: javalang not installed. Run:  pip install javalang")
            sys.exit(1)

        print(f"\nMode: Java → C")
        print(f"Input:  {input_path}")
        print(f"Parser: javalang (external library)\n")

        if show_ast:
            try:
                import javalang
                with open(input_path, 'r', encoding='utf-8') as f:
                    src = f.read()
                tree = javalang.parse.parse(src)
                print("── javalang AST ───────────────────────────────────")
                print(tree)
                print()
            except Exception as e:
                print(f"[AST] Could not show AST: {e}\n")

        c_code = java_to_c.translate_file(input_path)

        print("── GENERATED C CODE ────────────────────────────────")
        print(c_code)

        out_path = pathlib.Path(input_path).stem + '_lib.c'
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(c_code)
        print(f"\n✓ Saved to {out_path}")

    else:
        print(f"Error: unsupported file extension '{ext}'. Use .c or .java")
        sys.exit(1)


if __name__ == '__main__':
    main()
