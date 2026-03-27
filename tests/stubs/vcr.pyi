import contextlib

from vcr.cassette import Cassette

def use_cassette(
    cassette_name: str,
    cassette_library_dir: str,
    decode_compressed_response: bool,
    filter_query_parameters: list[tuple[str, str]] | None = None,
    filter_headers: list[tuple[str, str]] | None = None,
) -> contextlib.AbstractContextManager[Cassette]: ...
