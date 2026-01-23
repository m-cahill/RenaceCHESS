"""Ingestion module for downloading and caching Lichess database exports."""

from renacechess.ingest.cache import CacheManager
from renacechess.ingest.fetch import FileFetcher, HttpFetcher
from renacechess.ingest.lichess import LichessPreset, build_lichess_url
from renacechess.ingest.receipt import create_receipt, load_receipt, save_receipt

# Decompress is imported lazily in ingest.py to avoid requiring zstandard at import time
# from renacechess.ingest.decompress import decompress_zst

__all__ = [
    "CacheManager",
    "FileFetcher",
    "HttpFetcher",
    "build_lichess_url",
    "LichessPreset",
    "create_receipt",
    "load_receipt",
    "save_receipt",
]
