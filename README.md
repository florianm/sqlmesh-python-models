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

Start this repo in a Codespace, then run:

```bash
# sqlmesh plan dev
just pd

# sqlmesh plan
just pp
```

## Current issues

Signals are not working as expected, see 
<https://github.com/TobikoData/sqlmesh/issues/4779>.

To reproduce, modify the model in `models/bronze.py`
to enable a signal of your choice and observe the exceptions raised.
Enable print debug blocks for diagnostic output.