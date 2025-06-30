## Purpose

This repository contains a SQLMesh project showcasing how to load data
from CSV into DuckLake.

(In development:) A signal is used to trigger the loading of data only
when the CSV file is updated.

## Structure

- A [devcontainer](https://containers.dev/) setup for local development.
- A [pyproject.toml](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/) 
  for Python dependencies including
  [uv](https://docs.astral.sh/uv/), [just](https://github.com/casey/just),
  of course [sqlmesh](https://sqlmesh.readthedocs.io/en/stable/),
  and a range of useful other related packages.
- A `.venv` managed through `uv`.
- A `justfile` for convenience.
- Content created by `uv run sqlmesh init ducklake`,
  minus the default models, test, and config.
- A Python config that supports DuckLake as a datastore and DuckDB as engine.
- An SQL model `models/bronze.sql` that loads data from a CSV file into DuckLake.
- A file `signals/__init__.py` containing custom signals.
- A directory `scripts/__init__.py` containing helper functions for Python models 
  (currently unused).

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

Given the model `models/bronze.sql`
and the signal `ext_file_updated`  defined in `signals/__init__.py`,
the DDL interpolates `@execution_ts` as `1970-01-01 00:00:00`,
whereas the SQL body interpolates `@execution_ts` as `2025-06-30 00:00:00`,
which is the correct **date** but misses the **time** component.

### Model

```
MODEL (
  name bronze.seed_data,
  kind FULL,
  grain "id",
  cron '*/5 * * * *',
  signals [
    ext_file_updated(execution_ts := @execution_ts,
    file_path := 'seeds/seed_data.csv',
    cron_str := '*/5 * * * *'
    )
  ]
);

SELECT
  *, @execution_ts as "execution_ts"
FROM read_csv('seeds/seed_data.csv', delim = ',', header = true)
```

### Debug output from the plan
```
/workspaces/sqlmesh-python-models (main) $ just pd
uv run sqlmesh plan dev
Uninstalled 2 packages in 178ms
Installed 2 packages in 97ms

`dev` environment will be initialized

Requirements:
    + boto3==1.38.41
    + croniter==6.0.0
Models:
└── Added:
    └── bronze__dev.seed_data
Models needing backfill:
└── bronze__dev.seed_data: [full refresh]
Apply - Backfill Tables [y/n]: y

Updating physical layer ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100.0% • 1/1 • 0:00:00

✔ Physical layer updated

Got execution time 1970-01-01 00:00:00
The last run before '1970-01-01 00:00:00' based on cron schedule '*/5 * * * *' was 1969-12-31 23:55:00
Checking if file 'seeds/seed_data.csv' was updated (2025-06-22 11:57:42.994376) after last run (1969-12-31 23:55:00): True
[1/1] bronze__dev.seed_data   [full refresh]   0.17s
Executing model batches ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100.0% • 1/1 • 0:00:00

✔ Model batches executed

Updating virtual layer  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100.0% • 1/1 • 0:00:00

✔ Virtual layer updated
```

### Debug output from rendering the model
The SQL statement itself seems to get the date but is missing the time:

```
/workspaces/sqlmesh-pythnon-models (main) $ uv run sqlmesh render bronze.seed_data
SELECT *,
  '2025-06-30 00:00:00' AS "execution_ts",
  '2025-06-30 00:00:00+00:00' AS "execution_tstz"
FROM READ_CSV('seeds/seed_data.csv', "delim" = ',', "header" = TRUE) AS "_q_0"
```