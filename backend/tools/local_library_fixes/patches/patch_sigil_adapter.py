"""Use sigil's typed routine errors in the pinned RomM adapter."""

import ast
import hashlib
import sys
from pathlib import Path

EXPECTED_SHA256 = "6bce62451966fd90a0b48905a6d3b661e0bd82d83b4d0e193c53f771df6d5660"
OLD_CODES = """# Errors that are expected for arbitrary library files (no title id present,
# format sigil can't parse, missing decryption keys). Logged at debug level.
ROUTINE_SIGIL_ERROR_CODES: Final = frozenset(
    {"NOT_FOUND", "UNSUPPORTED", "UNSUPPORTED_FORMAT", "NEEDS_KEY"}
)

"""
OLD_CHECK = "            if code in ROUTINE_SIGIL_ERROR_CODES:"
NEW_CHECK = """            if isinstance(
                exc,
                (
                    sigil.SigilNotFoundError,
                    sigil.SigilUnsupportedFormatError,
                    sigil.SigilNeedsKeyError,
                ),
            ):"""


def patch(source: str) -> str:
    """Patch exact upstream source or fail closed when it has changed."""
    if hashlib.sha256(source.encode()).hexdigest() != EXPECTED_SHA256:
        raise ValueError(
            "Unsupported RomM sigil adapter; review this patch before upgrading"
        )
    if source.count(OLD_CODES) != 1 or source.count(OLD_CHECK) != 1:
        raise ValueError(
            "Expected sigil routine-error handling was not found exactly once"
        )

    patched = source.replace(OLD_CODES, "", 1).replace(OLD_CHECK, NEW_CHECK, 1)
    ast.parse(patched)
    return patched


def main() -> None:
    path = Path(sys.argv[1])
    path.write_text(patch(path.read_text()))


if __name__ == "__main__":
    main()
