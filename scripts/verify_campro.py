#!/usr/bin/env python3
import sys, platform
print("Python:", sys.version)
print("Implementation:", platform.python_implementation())
print("Executable:", sys.executable)
try:
    import campro
    print("campro module:", campro.__file__)
except Exception as e:
    print("campro import failed:", e)
