from sqlmesh.core.config import (
    Config,
    DuckDBConnectionConfig,
    GatewayConfig,
    ModelDefaultsConfig,
)
from sqlmesh.core.config.connection import DuckDBAttachOptions

config = Config(
    gateways={
        "dev": GatewayConfig(
            connection=DuckDBConnectionConfig(
                catalogs={
                    "peoplewa": DuckDBAttachOptions(
                        type="ducklake",
                        path="dev_metadata.ducklake",
                        data_path="data/ducklake",
                        # Optional: encrypted=True, data_inlining_row_limit=10,
                    ),
                },
                extensions=["ducklake"],
            ),
            # Use a separate DuckDB file for state tracking
            state_connection=DuckDBConnectionConfig(
                database="dev_state.db",
                type="duckdb",
            ),
        ),
    },
    default_gateway="dev",
    model_defaults=ModelDefaultsConfig(
        dialect="duckdb",
        start="2024-01-01",
    ),
)
