"""Read-only native sigil smoke test for a TSV of known library title IDs."""

import argparse
import csv
from pathlib import Path
from tempfile import TemporaryDirectory

import sigil


def verify_manifest(
    manifest: Path, library: Path
) -> tuple[int, int, int, int, int, dict[str, int]]:
    checked = 0
    extraction_errors = 0
    title_id_mismatches = 0
    save_target_mismatches = 0
    layout_mismatches = 0
    save_mismatch_kinds: dict[str, int] = {}
    library_root = library.resolve(strict=True)
    with manifest.open(newline="", encoding="utf-8") as handle:
        for row in csv.reader(handle, delimiter="\t"):
            if not row or not row[0] or row[0].startswith("#"):
                continue
            if len(row) != 5:
                raise ValueError(
                    "Manifest rows must contain platform, path, ID, save target, and layout"
                )
            (
                platform,
                relative_path,
                expected_id,
                expected_save_target,
                expected_layout,
            ) = row
            rom_path = (library_root / relative_path).resolve(strict=True)
            if not rom_path.is_relative_to(library_root):
                raise ValueError("Manifest path escapes the read-only library root")
            checked += 1
            try:
                result = sigil.extract(
                    str(rom_path), platform=platform, filename_fallback=False
                )
            except sigil.SigilError:
                extraction_errors += 1
                continue
            title_id_mismatches += result.title_id != expected_id
            save_mismatch = result.save_id != expected_save_target
            save_target_mismatches += save_mismatch
            if save_mismatch:
                kind = f"{platform}.{rom_path.suffix.lower().lstrip('.')}"
                save_mismatch_kinds[kind] = save_mismatch_kinds.get(kind, 0) + 1
            layout_mismatches += result.usage != expected_layout
    return (
        checked,
        extraction_errors,
        title_id_mismatches,
        save_target_mismatches,
        layout_mismatches,
        save_mismatch_kinds,
    )


def verify_truncated_fixture(suffix: str, platform: str) -> bool:
    with TemporaryDirectory(prefix="romm-sigil-smoke-") as temporary_directory:
        fixture = Path(temporary_directory) / f"truncated.{suffix}"
        fixture.write_bytes(b"NCSD" + bytes(48))
        try:
            sigil.extract(str(fixture), platform=platform, filename_fallback=False)
        except sigil.SigilError:
            return True
        return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--library", type=Path, default=Path("/roms"))
    args = parser.parse_args()

    (
        checked,
        extraction_errors,
        title_id_mismatches,
        save_target_mismatches,
        layout_mismatches,
        save_mismatch_kinds,
    ) = verify_manifest(args.manifest, args.library)
    truncated_3ds_rejected = verify_truncated_fixture("3ds", "3ds")
    truncated_ps2_rejected = verify_truncated_fixture("bin", "ps2")
    print(
        f"binding={sigil.version()} checked={checked} extraction_errors={extraction_errors} "
        f"title_id_mismatches={title_id_mismatches} "
        f"save_target_mismatches={save_target_mismatches} "
        f"save_mismatch_kinds={save_mismatch_kinds} "
        f"layout_mismatches={layout_mismatches} "
        f"truncated_3ds_rejected={truncated_3ds_rejected} "
        f"truncated_ps2_rejected={truncated_ps2_rejected}"
    )
    return (
        0
        if checked > 0
        and extraction_errors == 0
        and title_id_mismatches == 0
        and save_target_mismatches == 0
        and layout_mismatches == 0
        and truncated_3ds_rejected
        and truncated_ps2_rejected
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
