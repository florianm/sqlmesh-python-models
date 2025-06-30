import datetime
import os
import re

from croniter import croniter

try:
    import boto3
except ImportError:
    boto3 = None


from sqlglot.expressions import Literal
from sqlmesh import DatetimeRanges, ExecutionContext, signal
from sqlmesh.utils.date import to_datetime


# signal that returns only intervals that are <= 1 week ago
@signal(name="one_week_ago")
def one_week_ago(batch: DatetimeRanges) -> bool | DatetimeRanges:
    dt = to_datetime("1 week ago")

    return [(start, end) for start, end in batch if start <= dt]


@signal()
def always_true(batch: DatetimeRanges) -> bool:
    """Signal that always returns True."""
    print("Signal always_true called")
    return True


@signal(name="ext_file_exists")
def ext_file_exists(
    batch: DatetimeRanges,
    file_path: str,
) -> bool:
    """Signal to check if a file exists."""
    print(f"Checking if file '{file_path}' exists")

    if file_path.startswith("s3://"):
        if boto3 is None:
            raise ImportError("boto3 is required to check S3 file existence")

        match = re.match(r"s3://([^/]+)/(.+)", file_path)
        if not match:
            raise ValueError(f"Invalid S3 path: {file_path}")
        bucket, key = match.groups()

        s3 = boto3.client("s3")
        try:
            s3.head_object(Bucket=bucket, Key=key)
            return True
        except s3.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            raise
    else:
        return os.path.exists(file_path)


def quote_dotted_string(s):
    return ".".join(f'"{part}"' for part in s.split("."))


@signal()
def ext_file_updated(
    batch: DatetimeRanges,
    file_path: str,
    cron_str: str = "@hourly",
    model_name: str = None,
    context: ExecutionContext = None,
    **kwargs,
) -> bool:
    """Return True if a given file was modified after the previous execution.

    Args:
        batch (DatetimeRanges) Automatically received by the signal when used
          from a SQL model.
        file_path (str) The path to the file to be checked for a modification
          date past execution_ts.
        cron_str (str) The cron expression string, default: "@hourly"
        model_name (str) The model name as defined in the DDL,
          e.g. 'catalog.schema.dataset'
        kwargs Any kwargs like `execution_tstz` or `start_ts`.
        SQLMesh automatically injects the ExecutionContext.

    Returns:
        bool Whether to run the model or not.

    Examples:
        MODEL (
            ...,
            signals [
                ext_file_updated(
                file_path := 'path/to/data.csv',
                cron_str := '*/5 * * * *',
                model_name := 'catalog.schema.dataset'
                )
            ]

             signals [
                c(
                file_path := 'path/to/data.csv',
                cron_str := '*/5 * * * *',
                model_name := 'catalog.schema.dataset',
                execution_tstz := @execution_tstz,
                start_ts := @start_ts,
                )
            ]
        )
    """
    # Diagnostics
    print(
        "Signal 'ext_file_updated' called with\n"
        f"  file_path '{file_path}'\n"
        f"  execution_tstz {kwargs.get('execution_tstz', 'NA')}\n"
        f"  start_ts {kwargs.get('start_ts', 'NA')}\n"
        f"  cron_str '{cron_str}'\n"
        f"  model_name '{model_name}'\n"
    )

    this_run_ec = None
    this_run_et = None
    last_run = None

    # Parse ExecutionContext
    # Needs the model name as snapshots contains snapshots of all models
    mn = quote_dotted_string(model_name)
    if mn in context.snapshots:
        epoch_millis = context.snapshots[mn].created_ts
        this_run_ec = datetime.datetime.fromtimestamp(epoch_millis / 1000.0).replace(
            tzinfo=datetime.UTC
        )
        print(f"Found ExecutionContext created_ts: '{this_run_ec}'")
    else:
        print(f"Found no snapshot of model {mn} in the ExecutionContext.")

    # Parse execution_tstz
    execution_tstz = kwargs.get("execution_tstz", None)
    if execution_tstz:
        if isinstance(execution_tstz, str):
            try:
                this_run_et = datetime.datetime.fromisoformat(execution_tstz)
            except ValueError:
                raise ValueError(
                    "execution_ts must be datetime or ISO string, "
                    f"got '{execution_tstz}'"
                )
        elif isinstance(execution_tstz, Literal):
            try:
                this_run_et = datetime.datetime.fromisoformat(execution_tstz.to_py())
            except ValueError:
                raise ValueError(
                    "execution_ts failed to parse from Sqlglot Literal, "
                    f"got '{execution_tstz}'"
                )
        elif not isinstance(execution_tstz, datetime.datetime):
            raise ValueError(
                "execution_ts must be datetime, ISO string, or "
                f"Sqlglot Literal, got {type(execution_tstz)}"
            )
        else:
            this_run_et = execution_tstz

        this_run_et = this_run_et.replace(tzinfo=datetime.UTC)
        print(f"Found execution_ts: '{this_run_et}'")

    # Reconstruct last execution date from execution_ts and cron string
    cron_map = {
        "@yearly": "0 0 1 1 *",
        "@annually": "0 0 1 1 *",
        "@monthly": "0 0 1 * *",
        "@weekly": "0 0 * * 0",
        "@daily": "0 0 * * *",
        "@midnight": "0 0 * * *",
        "@hourly": "0 * * * *",
    }
    cron_string = cron_map.get(cron_str, cron_str)

    if not croniter.is_valid(cron_string):
        raise ValueError(f"Invalid cron string: '{cron_string}'")

    # Pick our best guess for current execution time
    # from ExecutionContext and execution_tstz
    best_guess = max(filter(None, [this_run_ec, this_run_et]), default=None)
    print(f"Guessing this run started on '{best_guess}'.")

    # Substract cron interval to calculate time of last execution
    if best_guess:
        cron = croniter(cron_string, best_guess)
        last_run = cron.get_prev(datetime.datetime).replace(tzinfo=datetime.UTC)

        print(
            f"The last run before '{best_guess}' "
            f"based on cron schedule '{cron_string}' "
            f"was '{last_run}'"
        )

    # Parse file_path
    if file_path.startswith("s3://"):
        if boto3 is None:
            raise ImportError("boto3 is required to check S3 file timestamps")

        match = re.match(r"s3://([^/]+)/(.+)", file_path)
        if not match:
            raise ValueError(f"Invalid S3 path: {file_path}")
        bucket, key = match.groups()

        s3 = boto3.client("s3")
        try:
            response = s3.head_object(Bucket=bucket, Key=key)
            file_mtime = response["LastModified"]
            if file_mtime.tzinfo is None:
                file_mtime = file_mtime.replace(tzinfo=datetime.UTC)
        except Exception as e:
            raise FileNotFoundError(f"S3 object not found: {file_path}") from e
    else:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Local file not found: {file_path}")
        file_mtime = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))

    # Fix timezones
    if best_guess.tzinfo is None and file_mtime.tzinfo is not None:
        best_guess = best_guess.replace(tzinfo=datetime.UTC)
    elif best_guess.tzinfo is not None and file_mtime.tzinfo is None:
        file_mtime = file_mtime.replace(tzinfo=datetime.UTC)

    will_run = file_mtime > last_run
    print(
        f"Checking if file '{file_path}' was updated ({file_mtime}) after "
        f"last run ({last_run}): {will_run}"
    )
    return will_run
