#!/usr/bin/env python3

import atheris
import sys
import fuzz_helpers

with atheris.instrument_imports():
    import bitstring

def TestOneInput(data):
    fdp = fuzz_helpers.EnhancedFuzzedDataProvider(data)
    test = fdp.ConsumeIntInRange(0, 3)
    if test == 0:
        BitArray(fdp.ConsumeRandomString())
    elif test == 1:
        a = Bits(bytes=fdp.ConsumeRandomBytes())
        a.pp('bin, hex', width=40)
    elif test == 2:
        pack(fdp.ConsumeRandomString())
    elif test == 3:
        BitStream(fdp.ConsumeRandomString())

def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
