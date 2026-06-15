#!/usr/bin/env python3

import re
import atheris
import sys
import os
import fuzz_helpers

# bitstring honours explicit field lengths verbatim (e.g. 'uint:9999999999=0'
# allocates ~10 gigabits) -- documented behaviour, not a bug. Letting the fuzzer
# emit such a token just grows the process past libFuzzer's RSS limit and
# reports a spurious out-of-memory "crash" (a harness amplification artifact,
# not a library defect). Reject inputs whose format string requests an
# unreasonable bit length up front, so we still exercise the PARSER on every
# input but never trigger a giant allocation. ~1 megabit is far more than any
# real format token needs while staying tiny in memory.
MAX_FIELD_BITS = 1 << 20
_BIG_LEN = re.compile(r'[0-9]{7,}')


def _too_big(s):
    return any(int(m) > MAX_FIELD_BITS for m in _BIG_LEN.findall(s))

with atheris.instrument_imports():
    import bitstring
    from bitstring import Bits, BitArray, BitStream, ConstBitStream, pack, Error

# bitstring's declared/expected error hierarchy. CreationError and
# InterpretError are aliases of ValueError in current upstream; Error is the
# package base and ReadError subclasses both Error and IndexError. These are
# the exceptions the format-string / construction mini-language raises on bad
# input -- catch exactly these (plus the stdlib types they alias to) and let
# everything else crash as a real finding. MemoryError/OverflowError are the
# documented consequence of a token requesting an over-large explicit length
# (see _too_big above), so they are expected outcomes, not defects.
EXPECTED = (bitstring.Error, ValueError, IndexError, KeyError, MemoryError, OverflowError)

# Bound the fuzzer-supplied format/auto strings (the parser is fully exercised
# at this size) and the raw byte inputs fed to the printer / streaming readers.
MAX_STR = 512
PP_MAX_BYTES = 4096
_DEVNULL = open(os.devnull, 'w')


def TestOneInput(data):
    fdp = fuzz_helpers.EnhancedFuzzedDataProvider(data)
    op = fdp.ConsumeIntInRange(0, 4)
    try:
        if op == 0:
            # Construct a BitArray from a fuzzed format/auto string.
            s = fdp.ConsumeUnicodeNoSurrogates(MAX_STR)
            if _too_big(s):
                return -1
            BitArray(s)
        elif op == 1:
            # Construct from raw bytes, then exercise the pretty-printer
            # (a rich format-string consumer). Bound the size (see above).
            a = Bits(bytes=fdp.ConsumeBytes(PP_MAX_BYTES))
            a.pp('bin, hex', width=40, stream=_DEVNULL)
        elif op == 2:
            # Drive the pack() format mini-language parser.
            s = fdp.ConsumeUnicodeNoSurrogates(MAX_STR)
            if _too_big(s):
                return -1
            pack(s)
        elif op == 3:
            # Streaming container + read() format-string parsing.
            fmt = fdp.ConsumeUnicodeNoSurrogates(MAX_STR)
            if _too_big(fmt):
                return -1
            s = BitStream(bytes=fdp.ConsumeBytes(PP_MAX_BYTES))
            s.read(fmt)
        elif op == 4:
            # Construct from bytes then unpack with a fuzzed format string --
            # the format-string mini-language parser is the richest target.
            fmt = fdp.ConsumeUnicodeNoSurrogates(MAX_STR)
            if _too_big(fmt):
                return -1
            b = ConstBitStream(bytes=fdp.ConsumeBytes(PP_MAX_BYTES))
            b.unpack(fmt)
    except EXPECTED:
        return -1


def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
