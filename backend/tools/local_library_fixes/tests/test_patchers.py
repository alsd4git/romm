import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

PATCHERS = Path(__file__).parents[1] / "patches"


def load_patcher(name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, PATCHERS / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


patch_sigil_adapter = load_patcher("patch_sigil_adapter")
patch_worker = load_patcher("patch_worker")

BACKEND = Path(__file__).parents[3]


@pytest.mark.parametrize(
    ("patcher", "source_path", "expected"),
    [
        (
            patch_worker,
            BACKEND / "handler/rq_worker.py",
            "database.sync_engine.dispose()",
        ),
        (
            patch_sigil_adapter,
            BACKEND / "adapters/services/sigil.py",
            "sigil.SigilUnsupportedFormatError",
        ),
    ],
)
def test_patches_exact_5_4_1_source(
    patcher: ModuleType, source_path: Path, expected: str
) -> None:
    source = source_path.read_text()

    patched = patcher.patch(source)

    assert expected in patched


@pytest.mark.parametrize("patcher", [patch_worker, patch_sigil_adapter])
def test_rejects_modified_source(patcher: ModuleType) -> None:
    with pytest.raises(ValueError, match="Unsupported RomM"):
        patcher.patch("# unexpected source\n")
