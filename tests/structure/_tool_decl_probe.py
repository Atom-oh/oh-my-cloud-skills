#!/usr/bin/env python3
"""Print the tool-declaration parser's behavior for test-plugin-structure.sh to assert on.

Loaded by path because `scripts/test-plugins.py` isn't an importable module name (hyphen).
Not a test itself — the assertions live in tests/structure/test-plugin-structure.sh.
"""
import importlib.util
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_spec = importlib.util.spec_from_file_location(
    "tp", os.path.join(_ROOT, "scripts", "test-plugins.py"))
tp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tp)

print("SPLIT", tp._split_tools("Read, Bash(git add:*, git commit:*), Grep")[0])
print("BALANCED", tp._split_tools("Read, Bash(git log:*)")[1])
print("EXTRA_CLOSE", tp._split_tools("Read, Bash(a))")[1])
print("EXTRA_OPEN", tp._split_tools("Read, Bash((a)")[1])
print("SCOPED_TOOLS", sorted(tp.SCOPED_TOOLS))
print("WIDE", sorted(tp.UNRESTRICTED_SCOPE_ITEMS))
print("MIRRORED", sorted(tp.MIRRORED_PLUGINS))
