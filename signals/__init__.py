import datetime
import os
import re

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


@signal(name="always_true")
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
    batch: DatetimeRanges, execution_dt: str | datetime.datetime, file_path: str
) -> bool:
    """Generic file update signal."""
    print(
        f"Checking if file '{file_path}' was updated after "
        f"execution time '{execution_dt}'"
    )
    # import ipdb; ipdb.set_trace()

    # Parse execution_dt
    if isinstance(execution_dt, str):
        try:
            execution_dt = datetime.datetime.fromisoformat(execution_dt)
        except ValueError:
            raise ValueError(
                f"execution_dt must be datetime or ISO string, got '{execution_dt}'"
            )
    elif not isinstance(execution_dt, datetime.datetime):
        raise ValueError(
            f"execution_dt must be datetime or ISO string, got {type(execution_dt)}"
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
    if execution_dt.tzinfo is None and file_mtime.tzinfo is not None:
        execution_dt = execution_dt.replace(tzinfo=datetime.UTC)
    elif execution_dt.tzinfo is not None and file_mtime.tzinfo is None:
        file_mtime = file_mtime.replace(tzinfo=datetime.UTC)

    return file_mtime > execution_dt


# from sqlmesh.core.signal import signal as _signal_decorator

# def _print_registered_signals():
#     print("🔍 Registered signals:")
#     for s in _signal_decorator.get_registry().values():
#         print(f" - {s.name}")

# _print_registered_signals()
