"""Build-time data mirror: copy authored knowledge into the wheel.

The installable ``legends_coolify._data`` mirror is generated during
``build_py`` from authored sources; it is never checked in. The wheel is
built from ``build_lib``, so mirrored files ship in every install while
the source tree stays free of duplicates. Missing mirror sources fail
the build rather than shipping a partial mirror.
"""
from pathlib import Path
import shutil

from setuptools import setup
from setuptools.command.build_py import build_py

MIRROR_FILES = ["README.md", "LICENSE", "NOTICE.md", "SUPPORT.md", "CONTRIBUTING.md", "AGENTS.md", "SECURITY.md", "CHANGELOG.md"]
MIRROR_DIRS = ["docs", "knowledge", "skills", "wiki", "references", "templates", "assets"]
MIRROR_SUFFIXES = {".md", ".json", ".png", ".webp"}
MIRROR_NAMES = {"LICENSE"}


def iter_mirror_sources(root):
    for name in MIRROR_FILES:
        path = root / name
        if not path.is_file() or path.is_symlink():
            raise RuntimeError("mirror source is missing: %s" % name)
        yield path, Path(name)
    for name in MIRROR_DIRS:
        top = root / name
        if not top.is_dir():
            raise RuntimeError("mirror source is missing: %s" % name)
        for path in sorted(top.rglob("*")):
            if not path.is_file() or path.is_symlink() or path.name.startswith("."):
                continue
            if path.suffix.lower() not in MIRROR_SUFFIXES and path.name not in MIRROR_NAMES:
                continue
            yield path, path.relative_to(root)


class BuildPyWithData(build_py):
    def run(self):
        root = Path(__file__).resolve().parent
        build_root = Path(self.build_lib).resolve()
        dest = build_root / "legends_coolify" / "_data"
        if dest.is_symlink() or (dest.exists() and dest.resolve() != dest):
            raise RuntimeError("refusing to clean an unexpected data dir: %s" % dest)
        if dest.exists():
            shutil.rmtree(dest)
        count = 0
        for source, relative in iter_mirror_sources(root):
            target = dest / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            count += 1
        (dest / "__init__.py").write_text(
            '"""Generated data mirror. Written at build time by setup.py; do not edit."""\n'
            "__all__ = []\n", encoding="utf-8")
        count += 1
        self.announce("mirrored %d data files into %s" % (count, dest), level=2)
        super().run()


setup(cmdclass={"build_py": BuildPyWithData})
