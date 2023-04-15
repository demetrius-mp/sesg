import zlib
from typing import Sequence


def compress_scopus_titles(
    titles: Sequence[str],
) -> bytes:
    return zlib.compress(str(titles).encode())


def decompress_scopus_titles(
    compressed_titles: bytes,
) -> Sequence[str]:
    decompressed_string = zlib.decompress(compressed_titles).decode()

    return eval(decompressed_string)
