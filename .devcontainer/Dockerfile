ARG UV_VERSION=latest
ARG DEBIAN_VERSION=bookworm

FROM ghcr.io/astral-sh/uv:$UV_VERSION AS uv

FROM mcr.microsoft.com/vscode/devcontainers/base:$DEBIAN_VERSION
LABEL maintainer="Florian Mayer <Florian.Mayer@dpc.wa.gov.au>"

ENV PYTHONUNBUFFERED 1

# hadolint ignore=DL3008
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    fzf libgl1 libglib2.0-0 libpq-dev bat \
    && apt-get clean

COPY --from=uv --chown=vscode: /uv /uvx /bin/

# Persist bash history
# https://code.visualstudio.com/remote/advancedcontainers/persist-bash-history
RUN SNIPPET="export PROMPT_COMMAND='history -a' \
  && export HISTFILE=/commandhistory/.bash_history" \
  && echo "$SNIPPET" >> "/root/.bashrc"
