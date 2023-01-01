# Build Stage
FROM fuzzers/atheris:2.0.7-python3.9

ADD ./mayhem/fuzz_helpers.py /fuzz_helpers.py
ADD ./mayhem/fuzz_bit.py /fuzz_bit.py

RUN python3 -m pip install bitstring

CMD ["/fuzz_bit.py"]
