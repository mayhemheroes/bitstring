#!/usr/bin/env python3

import atheris
import sys
import fuzz_helpers
import random

with atheris.instrument_imports():
    from bitstring import *

def TestOneInput(data):
    fdp = fuzz_helpers.EnhancedFuzzedDataProvider(data)
    test = fdp.ConsumeIntInRange(0, 3)
    try:
        if test == 0:
            BitArray(fdp.ConsumeRandomString())
        elif test == 1:
            a = Bits(bytes=fdp.ConsumeRandomBytes())
            a.pp('bin, hex', width=40)
        elif test == 2:
            pack(fdp.ConsumeRandomString())
        elif test == 3:
            BitStream(fdp.ConsumeRandomString())
    except Error:
        return -1
    except ValueError as e:
        if 'no value' in str(e):
            return -1
        if random.random() > 0.99:
            raise e
        return 0
    except KeyError:
        if random.random() > 0.99:
            raise
        return 0

def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
