# syntax=docker/dockerfile:1.6
# Multi-stage build for a minimal bankstatementparser-mcp image.
#
# The container runs the FastMCP server over stdio so an MCP client can
# launch it directly with ``docker run -i --rm bankstatementparser-mcp``.

# Pinned by digest; Dependabot's docker updater moves it.
FROM python:3.14-slim@sha256:9aaa474097d094040649f2162a627c0049b408f52138d980916788d80f04802f AS builder

WORKDIR /build

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# requirements/runtime.txt is exported from poetry.lock with hashes, so
# the image installs exactly the locked runtime set; the package itself
# goes on top without resolving anything further.
#
# pyproject.toml carries ``readme = "README.md"``, so README.md must be
# present at build-time for ``pip install .`` to resolve the package
# metadata.
COPY requirements/runtime.txt ./requirements.txt
COPY pyproject.toml README.md ./
COPY bankstatementparser_mcp ./bankstatementparser_mcp

RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --require-hashes -r requirements.txt \
    && /opt/venv/bin/pip wheel --no-deps --wheel-dir /tmp/wheels . \
    && /opt/venv/bin/pip install --no-deps /tmp/wheels/*.whl

FROM python:3.14-slim@sha256:9aaa474097d094040649f2162a627c0049b408f52138d980916788d80f04802f

LABEL org.opencontainers.image.title="bankstatementparser-mcp" \
      org.opencontainers.image.description="Model Context Protocol server for the bankstatementparser bank statement parsing library." \
      org.opencontainers.image.source="https://github.com/sebastienrousseau/bankstatementparser-mcp" \
      org.opencontainers.image.licenses="Apache-2.0"

# Non-root user (MCP clients launch the container with stdio; no extra
# privileges needed).
RUN groupadd --system mcp && useradd --system --gid mcp --home /home/mcp mcp \
    && mkdir -p /home/mcp \
    && chown -R mcp:mcp /home/mcp

COPY --from=builder /opt/venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER mcp
WORKDIR /home/mcp

# A non-zero exit here means an import / dependency mismatch; the MCP
# client will see it before the first tool call.
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import bankstatementparser_mcp.server" || exit 1

ENTRYPOINT ["bankstatementparser-mcp"]
