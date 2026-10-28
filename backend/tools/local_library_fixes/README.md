# Local RomM 5.4.1 compatibility image

This is a local, opt-in image build for the cilate RomM host. It is not an upstream
RomM release, and it must not replace the running service until the image and its
read-only library checks have been reviewed separately.

The final image is pinned to the official RomM 5.4.1 `linux/amd64` manifest
digest. Its sigil binding is rebuilt with RomM's own 5.4.1 Dockerfile procedure
and pinned to Argosy sigil commit
`0190443fe39dd72d0534db3d07bfabc5f35997a5`, which includes native CIA and PS2
raw BIN/CUE support. The overlay contains only two source-checked changes:

- dispose the RQ work-horse SQLAlchemy pool before RQ exits the work horse;
- classify sigil's typed routine errors as expected no-result outcomes.

The previous CIA/PS2 Python compatibility readers are intentionally absent.
Both patch scripts verify the exact RomM 5.4.1 source SHA-256 before changing a
file, and fail closed on any source drift.

## Build on cilate

Copy this directory to the separate context
`/home/dietpi/docker_data/romm/library-fixes-5.4.1-build`, keeping the existing
`library-fixes-build` directory and image untouched. Then build the candidate:

```sh
cd /home/dietpi/docker_data/romm/library-fixes-5.4.1-build
docker build --pull \
  --tag local/romm:5.4.1-library-fixes-native-sigil \
  --file Dockerfile .
```

Do not run `docker compose up`, replace the configured image, or restart RomM as
part of this preparation. Keep the old image available for rollback.

The `tests/` scripts run in ephemeral containers with `--network none`. Mount the
game library read-only and use a temporary metadata manifest derived from
read-only database queries: relative paths, platform slugs, title IDs, save
targets, and save-target layouts. Keep that manifest outside this repository.
The validation set contains 47 files: 24 files from the 12 CIA/`.3ds` pairs, 18
PS2 BIN/CUE files from nine games, two PSX files, and one file each from PSP,
GameCube, and Wii. The runner reports totals and mismatch categories only, never
file names or IDs. Synthetic truncated `.3ds` and `.bin` probes are created in a
temporary directory, never in the ROM library.

The 42 CIA/`.3ds` and PS2 files retained their database title IDs, save targets,
and layouts. The four non-Wii platform samples did too. The Wii sample kept its
title ID, while sigil 1.0.0 changed its save layout from `folder-exact` to
`folder-split` and now derives the folder from the disc ticket. This is an
intentional upstream fix documented in [Argosy sigil issue #15](https://github.com/rommapp/argosy-sigil/issues/15),
not a regression. The private test manifest expects this new Wii metadata shape;
it does not match the current database entry. No rescan or database write was
performed.

Run `tests/smoke_adapter.py` in the same isolated container with
`ROMM_AUTH_SECRET_KEY=local-test-only-not-a-secret-123456` to verify the adapter
classifies a synthetic unknown-format error as routine and that no fallback
reader module remains in the image. This value is deliberately synthetic and is
not a deployment credential.

## Prepared candidate

Built on 2026-10-29 (Europe/Rome) as
`local/romm:5.4.1-library-fixes-native-sigil`, image ID
`sha256:e11ac4ec63bbacf713485fbe0de73e4d0f888f8569c1a405dd412c0b6975a760`.
The build used official RomM 5.4.1 amd64 digest
`sha256:923a808be529a834a171b3e045821aeb7e2851f4b6fc9514076785b68a9142f6`.

The private 47-file run completed with no extraction errors or title-ID
mismatches. The 42 CIA/`.3ds` and PS2 files also matched existing database save
targets and layouts; PSX, PSP, and GameCube samples matched as well. The Wii
sample matched the new native target/layout recorded above. Truncated `.3ds` and
PS2 `.bin` probes were rejected, routine errors logged at debug level, and an
unexpected I/O error logged at error level. The live RomM service was not
replaced or restarted, and the prior image remains available for rollback.

## Optional Compose override

`compose.override.example.yml` only selects the already-built local tag. Copy it
to the private deployment directory and merge it with the host's existing
runtime Compose files after a separate deployment decision. It contains no
credentials, mounts, or other host settings.
