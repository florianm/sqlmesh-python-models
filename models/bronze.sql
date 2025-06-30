/* A SQL model to import a CSV to a DuckLake database using the DuckDB engine. */

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
