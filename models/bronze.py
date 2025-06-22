"""
A Python model to access data within a CSV.

The model infers the CSV's column schema on the fly using a helper.
It has knowledge of the file's location and primary key, against which
it runs an audit.


Input: A CSV stored in a local folder or on AWS S3.
Output: A Pandas dataframe.
"""

import typing as t

import pandas as pd
from sqlglot.expressions import to_column  # , Literal
from sqlmesh import model

# # ----------------------------------------------------------------------------#
# # Debug: are signals loaded?
from sqlmesh.core.signal import signal as _signal_decorator

from scripts import (
    make_coldef,
    make_model_name,
    read_csv_in_chunks,
)


def _print_registered_signals():
    print("🔍 models/bronze.py outside model class - Registered signals:")
    for s in _signal_decorator.get_registry().values():
        print(f" - {s.name}")
    print("🔍 End")


_print_registered_signals()
# # Output when running sqlmesh plan dev:
# # 🔍 models/bronze.py outside model class - Registered signals:
# #  - one_week_ago
# #  - always_true
# #  - ext_file_exists
# #  - ext_file_updated
# # 🔍 End
# # So, signals are registered when this file is executed.
# # When the file is serialised, are the signals loaded?
# ----------------------------------------------------------------------------#

csv_fn = "seeds/seed_data.csv"
csv_pk = "id"


@model(
    name=make_model_name(csv_fn, prefix="bronze", sep="."),
    kind="full",
    cron="@hourly",
    signals=[
        # ("always_true", {},),  # Signal 'always_true' is undefined
        # ("ext_file_exists", {"file_path": Literal.string(csv_fn)}),
        # ("ext_file_updated",
        # #{"execution_dt": "@execution_dt", "file_path": csv_fn}),
    ],
    grain=csv_pk,
    columns=make_coldef(csv_fn),
    audits=[
        ("not_null", {"columns": [to_column(csv_pk)]}),
    ],
)
def execute(
    # context: ExecutionContext,
    # start: datetime,
    # end: datetime,
    # execution_time: datetime,
    csv_fn=csv_fn,
    **kwargs: t.Any,
) -> pd.DataFrame:
    """Read data from a CSV in chunks."""
    return read_csv_in_chunks(csv_fn)
