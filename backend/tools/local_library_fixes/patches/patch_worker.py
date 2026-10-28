"""Apply the narrowly scoped DB-pool cleanup patch to the pinned RomM worker."""

import ast
import hashlib
import sys
from pathlib import Path

EXPECTED_SHA256 = "d410c902246f16e95acef1ed470c91529c0c78d0848b08361601c22f8b0fb053"
METHOD = """    def perform_job(self, job: Job, queue: Any) -> bool:
        try:
            return super().perform_job(job, queue)
        finally:
            # RQ exits work horses with os._exit, so return pooled DB connections explicitly.
            # Avoid importing the ORM for jobs that never used the database.
            database = sys.modules.get("handler.database.base_handler")
            if database is not None:
                try:
                    database.sync_engine.dispose()
                except Exception:
                    self.log.exception("Could not close the work horse database pool")

"""


def patch(source: str) -> str:
    """Patch exact upstream source or fail closed when it has changed."""
    if hashlib.sha256(source.encode()).hexdigest() != EXPECTED_SHA256:
        raise ValueError(
            "Unsupported RomM worker source; review this patch before upgrading"
        )
    if source.count("import logging\n") != 1:
        raise ValueError("Expected exactly one logging import")
    anchor = "    def handle_work_horse_killed(\n"
    if source.count(anchor) != 1:
        raise ValueError("Expected exactly one worker-killed handler")

    patched = source.replace("import logging\n", "import logging\nimport sys\n", 1)
    patched = patched.replace(anchor, METHOD + anchor, 1)
    ast.parse(patched)
    return patched


def main() -> None:
    path = Path(sys.argv[1])
    path.write_text(patch(path.read_text()))


if __name__ == "__main__":
    main()
