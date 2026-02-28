import clang.cindex
from clang.cindex import Index

print("Testing Clang python bindings...")

try:
    index = Index.create()
    print("Success: Clang library loaded!")
except Exception as e:
    print(f"Error loading Clang: {e}")
    print("Underlying libclang.dll might be missing from the system.")
