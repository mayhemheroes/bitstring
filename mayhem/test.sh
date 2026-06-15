#!/usr/bin/env bash
#
# bitstring/mayhem/test.sh — RUN bitstring's own pytest suite and emit a CTRF summary. exit 0 iff
# no test failed.
#
# PATCH-grade behavioral oracle: tests/ is a large known-answer suite that asserts real bitstring
# behavior — construction/parsing/packing values, dtype interpretation, fp8/mxfp round-trips,
# stream reads/unpacks. A no-op / exit(0) / behavior-altering patch to bitstring cannot pass it.
#
# The suite is run through the /mayhem/bitstring-tests ELF launcher (which exec()s
# python3 mayhem/run_tests.py), NOT python directly. That matters for the verify-repo
# anti-reward-hack check: it LD_PRELOADs a constructor that _exit(0)s every NON-system executable.
# The system python3 under /usr/bin is SPARED, but /mayhem/bitstring-tests is not — so under
# sabotage the launcher exits before pytest runs, no RUNTESTS line is produced, and this script
# reports a failure. The normal run is unaffected.
#
# This script only RUNS the suite (build.sh compiled the launcher); it never compiles.
set -uo pipefail
[ -n "${SOURCE_DATE_EPOCH:-}" ] || unset SOURCE_DATE_EPOCH

SRC="${SRC:-/mayhem}"
cd "$SRC"

# emit_ctrf <tool> <passed> <failed> [skipped] [pending] [other]
emit_ctrf() {
  local tool="$1" passed="$2" failed="$3" skipped="${4:-0}" pending="${5:-0}" other="${6:-0}"
  local tests=$(( passed + failed + skipped + pending + other ))
  cat > "${CTRF_REPORT:-$SRC/ctrf-report.json}" <<JSON
{
  "results": {
    "tool": { "name": "$tool" },
    "summary": {
      "tests": $tests,
      "passed": $passed,
      "failed": $failed,
      "pending": $pending,
      "skipped": $skipped,
      "other": $other
    }
  }
}
JSON
  printf 'CTRF {"results":{"tool":{"name":"%s"},"summary":{"tests":%d,"passed":%d,"failed":%d,"pending":%d,"skipped":%d,"other":%d}}}\n' \
    "$tool" "$tests" "$passed" "$failed" "$pending" "$skipped" "$other"
  [ "$failed" -eq 0 ]
}

if [ ! -x /mayhem/bitstring-tests ]; then
  echo "FATAL: /mayhem/bitstring-tests launcher missing — run mayhem/build.sh first" >&2
  emit_ctrf "pytest" 0 1 0
  exit 2
fi

echo "=== running pytest (bitstring known-answer suite) via /mayhem/bitstring-tests ==="
out="$(/mayhem/bitstring-tests 2>&1)"; rc=$?
echo "$out"

line="$(printf '%s\n' "$out" | sed -n 's/^RUNTESTS //p' | head -1)"
if [ -z "$line" ]; then
  echo "no RUNTESTS summary line from the test runner (rc=$rc)" >&2
  emit_ctrf "pytest" 0 1 0
  exit 1
fi

TESTS=$(echo "$line"   | sed -n 's/.*tests=\([0-9][0-9]*\).*/\1/p')
PASSED=$(echo "$line"  | sed -n 's/.*passed=\([0-9][0-9]*\).*/\1/p')
FAILED=$(echo "$line"  | sed -n 's/.*failed=\([0-9][0-9]*\).*/\1/p')
SKIPPED=$(echo "$line" | sed -n 's/.*skipped=\([0-9][0-9]*\).*/\1/p')
: "${TESTS:=0}" "${PASSED:=0}" "${FAILED:=0}" "${SKIPPED:=0}"

if [ "$TESTS" -eq 0 ]; then
  echo "test runner reported 0 tests collected" >&2
  emit_ctrf "pytest" 0 1 0
  exit 1
fi

emit_ctrf "pytest" "$PASSED" "$FAILED" "$SKIPPED"
