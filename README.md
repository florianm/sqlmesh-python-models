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

Signals are not working as expected, see
<https://github.com/TobikoData/sqlmesh/issues/4779>.

To reproduce, modify the model in `models/bronze.py`
to enable a signal of your choice and observe the exceptions raised.
Enable print debug blocks for diagnostic output.

To fix, apply the patch from <https://github.com/TobikoData/sqlmesh/issues/4779>:

Patch `sqlmesh/core/model/definition.py#L2340` > create_python_model():

```
# Import "signal" at L45
from sqlmesh.core.signal import signal, SignalRegistry

# Get the signal registry before create_python_model returns
signal_definitions=signal.get_registry()

    return _create_model(
        PythonModel,
        name,
        path=path,
        depends_on=depends_on,
        entrypoint=entrypoint,
        python_env=python_env,
        macros=macros,
        jinja_macros=jinja_macros,
        module_path=module_path,
        variables=variables,
        blueprint_variables=blueprint_variables,
        # Add signal_definitions explicitly:
        signal_definitions=signal_definitions,
        **kwargs,
    )
```