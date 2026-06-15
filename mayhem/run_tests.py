#!/usr/bin/python3
"""run_tests.py — RUN bitstring's own pytest suite and print a parseable summary.

Invoked via the /mayhem/bitstring-tests ELF launcher (NOT directly), so the verify-repo sabotage
oracle can neuter the launcher and prove the test oracle is behavioral: bitstring's suite (tests/)
is a large set of known-answer cases that assert real construction/parsing/packing behavior
(BitArray/Bits/BitStream values, dtype interpretation, fp8/mxfp round-trips, pack/unpack results),
so a no-op / exit(0) / behavior-altering patch to bitstring cannot pass it.

The suite references fixtures by CWD-relative paths (e.g. tests/test.m1v, tests/smalltestfile), so we
chdir to the repo root first. The perf-only benchmark module (tests/test_benchmarks.py) is excluded —
it times execution rather than asserting behavior.
"""
from __future__ import annotations

import os
import sys
import xml.etree.ElementTree as ET

import pytest

SRC = os.environ.get("SRC", "/mayhem")
XML = "/tmp/bitstring-junit.xml"
TESTS_DIR = "tests"


def main() -> int:
    os.chdir(SRC)
    pytest.main([
        "-q",
        "-p", "no:cacheprovider",
        "-o", "addopts=",
        TESTS_DIR,
        "--ignore=tests/test_benchmarks.py",
        "--junitxml", XML,
    ])

    root = ET.parse(XML).getroot()
    suites = root.findall("testsuite") or ([root] if root.tag == "testsuite" else [])
    if not suites:
        print("RUNTESTS tests=0 passed=0 failed=1 skipped=0")
        return 1

    tests = failed = skipped = 0
    for s in suites:
        tests += int(s.get("tests", 0))
        failed += int(s.get("failures", 0)) + int(s.get("errors", 0))
        skipped += int(s.get("skipped", 0))
    passed = tests - failed - skipped

    print(f"RUNTESTS tests={tests} passed={passed} failed={failed} skipped={skipped}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
