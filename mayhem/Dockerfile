# syntax=docker/dockerfile:1.7
#
# Commit-image Dockerfile (SMALL form) — builds ON TOP of the org base image
# (ghcr.io/mayhemheroes/base). The base provides debian + clang/llvm + libFuzzer + Python 3 + the
# identities + the build-contract ENV. bitstring (scott-griffiths/bitstring) is a pure-Python
# binary-data library backed by the bitarray + tibs wheels; the Atheris fuzz harness drives its
# format-string / construction parser (all Python), so the fuzz target has no native code to
# sanitize. This image installs the Atheris engine plus bitstring, its runtime deps, and its test
# deps into the base system Python as root, then (as non-root `mayhem`) compiles the ELF launcher
# shims and runs the real pytest suite via build.sh / test.sh.
#
# Build (from the repo root):
#   DOCKER_BUILDKIT=1 docker build -f mayhem/Dockerfile \
#       --build-arg COMMIT=$(git rev-parse HEAD) \
#       [--build-arg SOURCE_DATE_EPOCH=$(date +%s)] \
#       -t bitstring-commit:test .

FROM ghcr.io/mayhemheroes/base:20260621

ARG COMMIT
ARG REPO_URL
# SOURCE_DATE_EPOCH stays an ARG (available to build.sh); never bake it as ENV — an empty value
# breaks clang. build.sh unsets it when empty.
ARG SOURCE_DATE_EPOCH
# Declared for parity with the build contract; the bitstring fuzz target (pure-Python parser) has no
# native code to sanitize.
ARG SANITIZER_FLAGS

# Python headers (atheris builds a native module against the base clang/libFuzzer).
USER root
RUN apt-get update && apt-get install -yq --no-install-recommends \
      python3-dev python-is-python3 \
    && rm -rf /var/lib/apt/lists/*

# Atheris (the libFuzzer harness engine — builds a native module against the base clang/libFuzzer)
# goes into the base SYSTEM Python. PEP 668 marks that interpreter externally-managed, so
# --break-system-packages. This is the (networked) install step; build.sh deliberately does NOT
# pip-install, so its offline PATCH-tier re-run stays air-gapped. Atheris is pinned for a
# reproducible engine.
RUN pip install --no-cache-dir --break-system-packages atheris==3.1.0

# Source enters from the build CONTEXT (the CI checkout): the FULL repo (incl. .git history)
# is copied to /mayhem as `mayhem`; build.sh builds in place.
WORKDIR /mayhem
COPY --chown=2000:2000 . /mayhem

# Install bitstring itself + its runtime deps (bitarray, tibs) so the harness and the oracle can
# `import bitstring`, plus the pinned test deps (pytest, hypothesis, gfloat, pytest-benchmark) the
# known-answer suite needs. All networked here so build.sh's re-run stays offline.
RUN pip install --no-cache-dir --break-system-packages . \
 && pip install --no-cache-dir --break-system-packages -r tests/requirements.txt

USER mayhem

# Compile the ELF launcher shims (Mayhem needs an ELF target, not a .py).
RUN bash mayhem/build.sh

# Run bitstring's real pytest known-answer suite at build time; a failing suite fails the build.
RUN if [ -f mayhem/test.sh ]; then bash mayhem/test.sh; else echo "no mayhem/test.sh"; fi

LABEL org.opencontainers.image.source="${REPO_URL}" \
      org.opencontainers.image.revision="${COMMIT}" \
      rlenv.tier="commit" \
      rlenv.source_date_epoch="${SOURCE_DATE_EPOCH}" \
      rlenv.user="mayhem"

USER mayhem
WORKDIR /mayhem
