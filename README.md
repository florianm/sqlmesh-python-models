## Purpose
This repository contains a SQLMesh project showcasing Python models to load data 
from a CSV file into Postgres tables.

## Structure
- A devcontainer setup for local development.
- A pyproject.toml file for Python dependencies  including uv, just, , sqlmesh, and a range of useful other related packages.
- A .venv managed through uv.
- A justfile for convenience.
- Content created by `uv run sqlmesh init duckdb`, minus the default models, test, and config.
- A Python config that supports the attached Postgres database.
- A Python model `models/bronze.py` that loads data from a CSV file into a Postgres table.
- A file `signals/__init__.py` containing custom signals.
- A directory `scripts/__init__.py` containing helper functions for the model.

## Run
Start this repo in a Codespace, then run the following commands in the terminal:

```bash
# sqlmesh plan dev
just pd

# sqlmesh plan
just pp
```

## Current issues

`sqlmesh plan dev` (`just pd`) fails with:
```
Failed models

  "bronze_seed_data"

    BinderException:
      Binder Error: Column "pk_col" referenced that exists in the SELECT clause - but this column cannot be referenced before it is defined
  
Error: Plan application failed.
error: Recipe `pd` failed on line 62 with exit code 1
```

Signals are not working as expected, see <https://github.com/TobikoData/sqlmesh/issues/4779>.
To reproduce, modify the model in `models/bronze.py` 
to enable a signal of your choice and observe the exceptions raised.
Enable print debug blocks for diagnostic output.