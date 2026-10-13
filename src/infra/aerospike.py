"""Aerospike driver client creation and connection lifetime."""

from collections.abc import Iterator
from contextlib import contextmanager

import aerospike

from src.config.aerospike import AerospikeConfig, Environment


def _client_options(config: AerospikeConfig) -> dict[str, object]:
    """Build driver options for the selected environment."""
    # Local is intentionally the minimal single-node setup. Other environments
    # can add their HA, TLS, authentication, and policy options here as needed.
    if config.environment in (Environment.LOCAL, Environment.DEV):
        return {"hosts": [(config.host, config.port)]}
    return {"hosts": [(config.host, config.port)]}


@contextmanager
def open_aerospike_client(config: AerospikeConfig) -> Iterator[aerospike.Client]:
    """Connect to Aerospike and always close the client on context exit."""
    client = aerospike.client(_client_options(config)).connect()
    try:
        yield client
    finally:
        close_aerospike_client(client)


def close_aerospike_client(client: aerospike.Client) -> None:
    """Close an Aerospike client connection."""
    client.close()
