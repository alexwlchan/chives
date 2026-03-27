"""Shared helpers and test fixtures."""

from cassettes import cassette_name, vcr_cassette

pytest_plugins = "pytester"

__all__ = ["cassette_name", "vcr_cassette"]
