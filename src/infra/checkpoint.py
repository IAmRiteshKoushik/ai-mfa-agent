"""Aerospike connection lifetime belongs to the caller's context."""

from collections.abc import Iterator
from contextlib import contextmanager

from langgraph.checkpoint.aerospike import AerospikeSaver

from src.config import AppConfig
from src.infra.aerospike import open_aerospike_client


@contextmanager
def open_checkpointer() -> Iterator[AerospikeSaver]:
    config = AppConfig.from_env().aerospike
    with open_aerospike_client(config) as client:
        yield AerospikeSaver(client=client, namespace=config.namespace)
