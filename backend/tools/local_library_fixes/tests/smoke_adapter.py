"""Check typed routine-error handling in the patched RomM service."""

import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import sigil

from adapters.services.sigil import SigilService
from utils.platform_slugs import UniversalPlatformSlug as UPS


def main() -> int:
    with TemporaryDirectory(prefix="romm-sigil-adapter-") as temporary_directory:
        fixture = Path(temporary_directory) / "unknown-format.3ds"
        fixture.write_bytes(bytes(1024 * 1024))
        routine_errors = (
            sigil.SigilNotFoundError,
            sigil.SigilUnsupportedFormatError,
            sigil.SigilNeedsKeyError,
        )
        try:
            sigil.extract(str(fixture), platform="3ds", filename_fallback=False)
        except routine_errors:
            pass
        else:
            raise AssertionError(
                "Synthetic unknown content was not rejected as a routine error"
            )

        with (
            patch("adapters.services.sigil.log.debug") as debug_log,
            patch("adapters.services.sigil.log.error") as error_log,
        ):
            result = asyncio.run(
                SigilService().extract_title_id(UPS.N3DS, str(fixture))
            )
            if result is not None:
                raise AssertionError(
                    "Routine sigil error unexpectedly returned metadata"
                )
            debug_log.assert_called_once()
            error_log.assert_not_called()

        with (
            patch(
                "adapters.services.sigil.sigil.extract",
                side_effect=OSError("smoke test"),
            ),
            patch("adapters.services.sigil.log.error") as error_log,
        ):
            result = asyncio.run(
                SigilService().extract_title_id(UPS.N3DS, str(fixture))
            )
            if result is not None:
                raise AssertionError(
                    "Unexpected sigil error unexpectedly returned metadata"
                )
            error_log.assert_called_once()
    if Path("/backend/adapters/services/title_id_fallbacks.py").exists():
        raise AssertionError("Legacy CIA/PS2 fallback reader is still installed")

    print(
        "routine_error_logged_at_debug=True unexpected_error_logged_at_error=True "
        "legacy_readers_absent=True"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
