import datetime
import os
import re

from croniter import croniter

try:
    import boto3
except ImportError:
    boto3 = None


from sqlmesh import DatetimeRanges, signal
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


@signal(name="ext_file_updated")
def ext_file_updated(
    batch: DatetimeRanges,
    file_path: str,
    execution_ts: str | datetime.datetime,
    cron_str: str = "@hourly",
) -> bool:
    """Return True if a given file was modified after the previous execution.

    Args:
        batch (DatetimeRanges) Automatically received by the signal when used
          from a SQL model.
        file_path (str) The path to the file to be checked for a modification
          date past execution_ts.
        execution_ts (str | datetime.datetime) The value of the macro
          `@execution_ts`, which is the current run of the model.
        cron_str (str) The cron expression string, default: "@hourly" as per
          SQLMesh default. Pass the model's cron string.

    Returns:
        bool Whether to run the model or not.

    Examples:
        MODEL (
            ...,
            signals [
                ext_file_updated(execution_ts := @execution_ts,
                file_path := 'path/to/file.csv',
                cron_str = '*/5 * * * *'
                )
            ]
        )
    """
    print(f"Got execution time {execution_ts}")
    # Parse execution_ts
    if isinstance(execution_ts, str):
        try:
            execution_ts = datetime.datetime.fromisoformat(execution_ts)
        except ValueError:
            raise ValueError(
                f"execution_ts must be datetime or ISO string, got '{execution_ts}'"
            )
    elif not isinstance(execution_ts, datetime.datetime):
        raise ValueError(
            f"execution_ts must be datetime or ISO string, got {type(execution_ts)}"
        )

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
        raise ValueError(f"Invalid cron string: {cron_string}")

    cron = croniter(cron_string, execution_ts)
    last_run = cron.get_prev(datetime.datetime)

    print(
        f"The last run before '{execution_ts}' based on cron schedule '{cron_string}' "
        f"was {last_run}"
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
    if last_run.tzinfo is None and file_mtime.tzinfo is not None:
        last_run = last_run.replace(tzinfo=datetime.UTC)
    elif last_run.tzinfo is not None and file_mtime.tzinfo is None:
        file_mtime = file_mtime.replace(tzinfo=datetime.UTC)

    will_run = file_mtime > last_run
    print(
        f"Checking if file '{file_path}' was updated ({file_mtime}) after "
        f"last run ({last_run}): {will_run}"
    )
    return will_run
