---
name: dockerfile-style
description: >
  Personal Dockerfile convention: multi-stage layout with separate dev and
  prod targets, a header comment that documents each target's build command,
  and BuildKit cache mounts for apt, uv, mamba and ccache instead of
  uncached pip/conda installs. Use whenever writing or editing a Dockerfile,
  or when the user says "docker build is slow", "cache installs in docker",
  "dev and prod images", or similar.
---

Apply this whenever you write or edit a `Dockerfile`.

Two rules carry most of the value:

1. One file, several targets. A `dev` image and a slim `prod` image come from
   the same `Dockerfile`, not from two files that drift apart.
2. Every install step runs under a BuildKit cache mount.

## Header block

Start with the syntax directive, then a comment that names each target and
gives the exact command that builds it. A reader must not have to guess how
to build the image they want:

```dockerfile
# syntax=docker/dockerfile:1
#
# myproject — two images from one file:
#
#   prod : slim; ships the application and its runtime dependencies only.
#            docker buildx build --target prod --platform=linux/amd64 -t myproject .
#
#   dev  : adds the test, lint and debug tooling. Shell into it to work.
#            docker buildx build --target dev -t myproject:dev .
#
# Needs BuildKit (DOCKER_BUILDKIT=1, or use `docker buildx`).
```

## Stage skeleton

The layout is the same in every language. Only the build command changes.

- **`builder`** — the full toolchain and the build dependencies. Produces
  artifacts: a compiled binary, a wheel, a virtual environment.
- **`dev`** — extends `builder`. Adds the test, lint and debug tooling. This
  is the image you shell into. Give it the project source.
- **`test`** (optional) — extends `dev`. Its last `RUN` executes the test
  suite, so `docker buildx build --target test .` fails the build when a test
  fails. This makes one command a complete CI gate.
- **`prod`** — a fresh slim base image. `COPY --from=builder` the artifacts
  only. Add the minimum runtime libraries. No toolchain, no source tree, no
  test fixtures.

`prod` must never extend `dev`. The whole point is that the production image
never contains the compiler or the test tooling.

## Cache mounts

A plain `RUN pip install -r requirements.txt`, `RUN conda install ...` or
`RUN apt-get install ...` re-downloads and re-resolves everything on every
build, even when one package changed. Mount the tool's cache directory so it
persists across builds.

Use `uv` for Python packages and `mamba` for conda-forge environments — not
`pip`/`conda`. They are faster resolvers to begin with; the cache mount is on
top of that speedup, not instead of it.

```dockerfile
# Python deps via uv
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen
# or: uv pip install -r requirements.txt

# Conda-forge deps via mamba
RUN --mount=type=cache,target=/opt/conda/pkgs \
    mamba install -y -n base <packages>
```

apt needs its cleanup hooks disabled first, otherwise Docker's base images
delete the very packages you are caching:

```dockerfile
RUN rm -f /etc/apt/apt.conf.d/docker-clean \
 && echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends <packages>
```

**Do not** add `rm -rf /var/lib/apt/lists/*` to a cached `apt-get` step. That
line is the correct habit for an uncached build. Here it deletes the cache
mount contents, and the two cancel out.

For compiled code, mount the compiler cache too:

```dockerfile
ENV CCACHE_DIR=/root/.ccache CCACHE_MAXSIZE=5G CCACHE_COMPILERCHECK=content
RUN --mount=type=cache,target=/root/.ccache \
    cmake --build /build -j "$(nproc)"
```

## Worked example: Python with uv

The dev/prod split maps directly onto dependency groups (see the
`python-style` skill): `[project].dependencies` is what `prod` installs,
the `dev` dependency group is what `dev` adds on top.

```dockerfile
# syntax=docker/dockerfile:1
ARG PYTHON_VERSION=3.12

FROM python:${PYTHON_VERSION}-slim AS builder
SHELL ["/bin/bash", "-euo", "pipefail", "-c"]
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
# PATH is set here, not only in prod: without it a shell in the dev image gets
# the system interpreter instead of the project environment.
ENV UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/opt/venv PATH=/opt/venv/bin:$PATH
WORKDIR /app

# Lockfile first: the dependency layer then rebuilds only when deps change,
# not on every source edit.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

FROM builder AS dev
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen
COPY tests ./tests
CMD ["/bin/bash"]

FROM dev AS test
RUN uv run pytest

FROM python:${PYTHON_VERSION}-slim AS prod
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app/src /app/src
ENV PATH=/opt/venv/bin:$PATH
WORKDIR /app
CMD ["myproject"]
```

`--no-install-project` on the first sync keeps your own package out of the
dependency layer, so editing source does not invalidate it.

## Compiled languages

Same skeleton, different middle. `builder` installs the toolchain and
compiles with a `ccache` mount and `-j "$(nproc)"`. `test` runs the suite
(`ctest --output-on-failure`) as its final `RUN`. `prod` starts from the slim
base and copies the binary and nothing else — often one `COPY --from=builder`
plus one runtime library.

Reference implementation:
`~/mskcc/VIPER_project/repos/ARACNe3/Dockerfile`.

## Rules

- Pin the base image through an `ARG` (`ARG DEBIAN_VERSION=bookworm`), so a
  version bump is one line and is visible in `docker build --build-arg`.
- Set `SHELL ["/bin/bash", "-euo", "pipefail", "-c"]` in every stage that
  runs a multi-command `RUN`. Without `pipefail` a failure in the middle of a
  pipe is silently ignored.
- Keep a `.dockerignore`. `.git` and test fixtures often dwarf the source and
  are uploaded into the build context on every build.
- Fetch large third-party sources with `git clone` at a pinned commit inside
  the build. Do not `COPY` a checked-out vendor directory into the context.
- Requires BuildKit, the default in modern Docker and `docker buildx`.
- Don't suggest `pip` or `conda` unless the project is explicitly locked into
  one of them — default to `uv`/`mamba`.
