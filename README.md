## Purpose

This repository contains a SQLMesh project showcasing Python models to load data
from a CSV file into Postgres tables.

(In development:) A signal is used to trigger the loading of data only
when the CSV file is updated.

## Structure

- A [devcontainer](https://containers.dev/) setup for local development.
- A [pyproject.toml](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/) for Python dependencies including
  [uv](https://docs.astral.sh/uv/), [just](https://github.com/casey/just),
  of course [sqlmesh](https://sqlmesh.readthedocs.io/en/stable/),
  and a range of useful other related packages.
- A .venv managed through uv.
- A justfile for convenience.
- Content created by `uv run sqlmesh init postgres`,
  minus the default models, test, and config.
- A YAML config that supports the attached Postgres database.
- A Python model `models/bronze.py` that loads data from a CSV file into a Postgres table.
- A file `signals/__init__.py` containing custom signals.
- A directory `scripts/__init__.py` containing helper functions for the model.

## Run

Start this repo in a Codespace, then run the SQLMesh pipelines in the virtualenv.
The justfile provides some convenience commands.

```bash
# uv run sqlmesh plan dev
just pd

# uv run sqlmesh plan
just pp

# uv run sqlmesh run dev
just rd

# uv run sqlmesh run
just rp
```

## Current issues

SQL models do not interpolate time macros as expected.

The DDL does not remember the last run and returns 