#!/usr/bin/env bash
#
# bitstring/mayhem/build.sh — compile the ELF launcher shims for the Atheris fuzz harness and the
# pytest oracle runner.
#
# bitstring (scott-griffiths/bitstring) is a pure-Python binary-data library backed by the bitarray
# and tibs wheels. The Atheris harness (mayhem/fuzz_bit.py) drives bitstring's real format-string /
# construction mini-language parser (BitArray/Bits/BitStream/pack/unpack/read/pp) — all Python; the
# native backings ship as ordinary manylinux wheels. So there is nothing here to sanitize.
#
# Mayhem requires every target `cmd:` to be an ELF (it rejects a shebang/script wrapper and
# fuzz-smoke.sh checks the ELF magic), so we compile a tiny C shim per Python entry point that
# exec()s `python3 <script>` (see mayhem/launcher.c). The Python deps (atheris, bitstring + bitarray
# + tibs, pytest + hypothesis + gfloat + pytest-benchmark) are installed into the image system
# Python by the Dockerfile (root + network); this script does NOT pip-install, so its offline
# PATCH-tier re-run (non-root `mayhem`, --network none) stays idempotent + air-gapped: it only
# compiles the shims (clang, no network).
set -euo pipefail

# clang rejects SOURCE_DATE_EPOCH='' — must be unset or a valid integer.
[ -n "${SOURCE_DATE_EPOCH:-}" ] || unset SOURCE_DATE_EPOCH

SRC="${SRC:-/mayhem}"
cd "$SRC"

: "${CC:=clang}"

# $DEBUG_FLAGS threads DWARF < 4 debug info onto the shims (SPEC §6.2 item 10): clang-19's plain
# `-g` emits DWARF-5, which Mayhem's triage can't read, so force DWARF-3 explicitly.
: "${DEBUG_FLAGS:=-gdwarf-3}"

# bitstring's fuzzed code (the format-string parser) is pure Python, run under Atheris/libFuzzer at
# runtime; the shims are pure exec() wrappers (sanitizing them would only add ASan noise on the
# wrapper, never on the fuzzed Python). Referenced for parity / so an override is visible.
echo "SANITIZER_FLAGS=${SANITIZER_FLAGS:-<unset>} (pure-Python fuzz target; not applied to the exec shims)"
echo "DEBUG_FLAGS=$DEBUG_FLAGS"

build_launcher() {
  local out="$1" script="$2"
  echo "--- compiling launcher /mayhem/$out -> $script ---"
  # Dynamically linked (default) so the verify-repo sabotage oracle's LD_PRELOAD can reach it.
  "$CC" $DEBUG_FLAGS -O1 -DPY_SCRIPT="\"$script\"" -o "/mayhem/$out" mayhem/launcher.c
  chmod +x "/mayhem/$out"
}

# Fuzz target: the preserved Atheris harness (bitstring parser). Name kept for parity.
build_launcher fuzz-bit        /mayhem/mayhem/fuzz_bit.py
# Test oracle runner: runs bitstring's real pytest suite (driven by mayhem/test.sh through this ELF
# so the sabotage check can neuter it).
build_launcher bitstring-tests /mayhem/mayhem/run_tests.py

echo "build.sh complete:"
ls -la /mayhem/fuzz-bit /mayhem/bitstring-tests
