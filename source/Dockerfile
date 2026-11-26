# RAGStore - multi stage build.
#
# Stage 1 compiles the Rust binary. The crate has **no external dependencies**,
# so `cargo build --offline` succeeds without any network access, which makes
# the image build reproducible on an isolated builder.
#
# Stage 2 keeps only the resulting binary and the shared libraries it needs.

# ---- build stage -------------------------------------------------------------
FROM rust:1.98-bookworm AS builder

WORKDIR /build

# The dependency graph is empty, so the manifest is copied on its own first.
COPY ragstore/Cargo.toml ./Cargo.toml
COPY ragstore/src ./src

# `--offline` proves that the build needs no registry access.
RUN cargo build --release --offline --locked 2>/dev/null \
    || cargo build --release --offline

# ---- runtime stage -----------------------------------------------------------
FROM ubuntu:24.04

# No package installation on purpose: the server is a statically-linkable
# Rust binary that only needs glibc and libgcc, both present in this base
# image. Keeping the runtime stage free of `apt-get` means the build needs
# no network access at all, which keeps it reproducible on an isolated
# builder and avoids depending on an apt mirror being reachable.

COPY --from=builder /build/target/release/ragstore /usr/local/bin/ragstore

# The database keeps its files under /data, as the evaluation expects.
RUN mkdir -p /data && chmod 1777 /data
VOLUME ["/data"]

ENV RAGSTORE_DATA_DIR=/data
ENV RAGSTORE_MODE=exact
ENV RAGSTORE_DURABILITY=os
ENV RAGSTORE_BUFFER_POOL_MB=64

# The server speaks the JSON Lines protocol of the competition over stdin and
# stdout: it announces itself with `{"type":"ready"}`, answers every
# `execute` request with one response object, and answers the `shutdown`
# request before it exits with code 0.
#
# The image therefore has to start the server in that mode by default. It must
# not fall back to an SQL prompt or start a network service, because the judge
# drives the process over its standard streams.
ENTRYPOINT ["/usr/local/bin/ragstore"]
CMD ["--data-dir", "/data"]
