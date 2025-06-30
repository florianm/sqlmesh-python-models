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

It is probably incorrect to call the macro variables from the DDL.

However, the signal itself can access the Execution context, and
with the help of the model name and the cron schedule we can
(somewhat clumsily) reconstruct the last execution time.

### Model

```
MODEL (
  name peoplewa.bronze.seed_data,
  kind FULL,
  grain "id",
  cron '*/5 * * * *',
  signals [
    ext_file_updated(
      file_path := 'seeds/seed_data.csv',
      cron_str := '*/5 * * * *',
      model_name := 'peoplewa.bronze.seed_data',
      execution_tstz := @execution_tstz
    ),
  ]
);

SELECT
  *, @execution_ts as "execution_ts", @execution_tstz as "execution_tstz"
FROM read_csv('seeds/seed_data.csv', delim = ',', header = true)
```

### Debug output from the plan

Pretend we've updated the CSV:
```
touch seeds/seed_data.csv
```

Re-run the plan - now it should detect the updated mtime of the CSV and re-run the model.

```
/workspaces/sqlmesh-python-models (main) $ just rd
uv run sqlmesh run dev
Signal 'ext_file_updated' called with
  file_path 'seeds/seed_data.csv'
  execution_tstz '1970-01-01 00:00:00+00:00'
  start_ts NA
  cron_str '*/5 * * * *'
  model_name 'peoplewa.bronze.seed_data'
  this model 'NA'
Found ExecutionContext created_ts: '2025-06-30 13:33:41.331000+00:00'
Found execution_ts: '1970-01-01 00:00:00+00:00'
Guessing this run started on '2025-06-30 13:33:41.331000+00:00'.
The last run before '2025-06-30 13:33:41.331000+00:00' based on cron schedule '*/5 * * * *' was '2025-06-30 13:30:00+00:00'
Checking if file 'seeds/seed_data.csv' was updated (2025-06-30 13:35:26.078871+00:00) after last run (2025-06-30 13:30:00+00:00): True
[1/1] bronze__dev.seed_data   [full refresh]   0.37s
Executing model batches ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100.0% • 1/1 • 0:00:00

✔ Model batches executed

Run finished for environment 'dev'
```

### Debug output from rendering the model
The SQL statement itself seems to get the date but is missing the time:

```
/workspaces/sqlmesh-pythnon-models (main) $ uv run sqlmesh render bronze.seed_data
SELECT
  *,
  '2025-06-30 00:00:00' AS "execution_ts",
  '2025-06-30 00:00:00+00:00' AS "execution_tstz"
FROM READ_CSV('seeds/seed_data.csv', "delim" = ',', "header" = TRUE) AS "_q_0"
```
