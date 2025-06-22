import os
import zipfile

import polars as pl
import py7zr
from frictionless import describe


def unpack_file(csv_fn: str, zip_fn: str = None) -> None:
    """Unpack a file from a 7z or ZIP archive and warn if the expected
    file does not exist.

    Args:
        zip_fn (str): Path to the 7z or ZIP archive.
        csv_fn (str): Path to the expected file inside the archive.
    Raises:
        FileNotFoundError: If the archive does not exist or the file is not found
        inside the archive.
    Raises:
        ImportError: If the required libraries for unpacking are not available.
    """
    if zip_fn:
        if not os.path.exists(zip_fn):
            raise FileNotFoundError(f"File '{zip_fn}' does not exist.")

        if not os.path.exists(csv_fn):
            # If the zip_fn is a 7z archive, use py7zr to extract it.
            with py7zr.SevenZipFile(zip_fn, mode="r") as z:
                z.extractall()
            # If the zip_fn is a zip file, you can use the zipfile module.
            with zipfile.ZipFile(zip_fn, "r") as z:
                z.extract(csv_fn)

    if not os.path.exists(csv_fn):
        raise FileNotFoundError(f"File '{csv_fn}' does not exist inside '{zip_fn}'.")


def read_csv_in_chunks(csv_fn, sep=",", chunk_size=100000):
    """Yield Pandas DataFrames in chunks from a CSV file.

    The CSV can be local or on AWS S3.
    The CSV is read by Polars in lazy mode for efficient memory usage.

    Args:
        csv_fn (str): Path to the CSV file.
        sep (str): Separator used in the CSV file. Default is ','.
        chunk_size (int): Number of rows per chunk. Default is 100,000.

    Yields:
        pd.DataFrame: A chunk of the CSV file as a Pandas DataFrame.
    """
    df_lazy = pl.read_csv(
        csv_fn,
        has_header=True,
        separator=sep,
        quote_char='"',
        encoding="utf-8",
        infer_schema_length=100,
        try_parse_dates=True,
        low_memory=True,
        rechunk=False,
    ).lazy()

    for i in range(0, df_lazy.collect().height, chunk_size):
        yield df_lazy.slice(i, chunk_size).collect().to_pandas()


def make_coldef(csv_fn: str) -> dict:
    """Create a column definition dictionary from a CSV file.

    Args:
        csv_fn (str): Path to the CSV file.

    Returns:
        dict: A dictionary with column names as keys and their data
        types as values to be used in SQLMesh model DDLs as `columns` spec.
    """
    if not os.path.exists(csv_fn):
        raise FileNotFoundError(f"File '{csv_fn}' does not exist.")

    # Use frictionless describe to generate a JSON schema.
    schema = describe(csv_fn, type="schema")

    # Translate the frictionless schema to a name: type coldef.
    return {f.name: f.type for f in schema.fields}


def make_model_name(csv_fn: str, prefix=None, sep="_") -> str:
    """Generate a model name based on the CSV file name.

    Args:
        csv_fn (str): Path to the CSV file.
        prefix (str, optional): A prefix to prepend to the model name. Defaults to None.
        sep (str, optional): Separator to use between prefix and file name.
          Defaults to '_' which results in a one tier database structure.
          Use "." for a two tier database structure, or include a "." in the prefix
          for a three tier database structure.

    Returns:
        str: A model name derived from the CSV file name.
    """
    # from sqlmesh.core.signal import signal as _signal_decorator

    # def _print_registered_signals():
    #     print("🔍 Helper called inside model DDL - Registered signals:")
    #     for s in _signal_decorator.get_registry().values():
    #         print(f" - {s.name}")
    #     print("🔍 Helper called inside model DDL end")

    # _print_registered_signals()
    base_name = os.path.basename(csv_fn)
    name, _ = os.path.splitext(base_name)
    if prefix:
        name = f"{prefix}{sep}{name}"
    return name
