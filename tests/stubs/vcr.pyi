from contextlib import AbstractContextManager
from typing import Any, Callable

from vcr.cassette import Cassette

def use_cassette(
    cassette_name: str,
    cassette_library_dir: str,
    decode_compressed_response: bool,
    filter_query_parameters: list[tuple[str, str]] | None = None,
    filter_headers: list[tuple[str, str]] | None = None,
    before_record_response: Callable[[Any], Any] | None = None,
) -> AbstractContextManager[Cassette]: ...
