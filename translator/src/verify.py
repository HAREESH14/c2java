# =============================================================================
#  verify.py  -- WSL gcc compilation check for generated C code
# =============================================================================

import subprocess
import tempfile
import os


def compile_c_wsl(c_source: str) -> tuple[bool, str]:
    """
    Compile a C source string using WSL gcc.

    Returns:
        (success: bool, message: str)
        success=True  -> compiled cleanly
        success=False -> compile errors returned in message
    """
    with tempfile.NamedTemporaryFile(
        suffix='.c', mode='w', encoding='utf-8',
        delete=False, dir=tempfile.gettempdir()
    ) as tf:
        tf.write(c_source)
        c_path = tf.name

    # Convert Windows path to WSL path: C:\foo\bar -> /mnt/c/foo/bar
    wsl_path = _win_to_wsl(c_path)
    out_path  = wsl_path.replace('.c', '.out')

    cmd = ['wsl', 'gcc', '-Wall', '-o', out_path, wsl_path]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=15
        )
        ok  = result.returncode == 0
        msg = (result.stdout + result.stderr).strip()
        return ok, msg or 'Compiled successfully.'
    except FileNotFoundError:
        return False, 'WSL not found. Is WSL installed?'
    except subprocess.TimeoutExpired:
        return False, 'gcc timed out.'
    finally:
        try: os.unlink(c_path)
        except OSError: pass


def _win_to_wsl(win_path: str) -> str:
    """Convert Windows absolute path to /mnt/<drive>/... WSL path."""
    p = win_path.replace('\\', '/')
    if len(p) >= 2 and p[1] == ':':
        drive = p[0].lower()
        rest  = p[2:]
        return f'/mnt/{drive}{rest}'
    return p


def compile_c_file_wsl(c_path: str) -> tuple[bool, str]:
    """Compile an existing .c file on disk using WSL gcc."""
    with open(c_path, encoding='utf-8') as f:
        return compile_c_wsl(f.read())
