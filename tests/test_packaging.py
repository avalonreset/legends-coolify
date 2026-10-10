"""Mirror completeness: authored sources, membership links, wheel smoke.

The installable ``legends_coolify._data`` mirror is generated at build time
by setup.py from authored sources; it is never checked in. These checks
prove the mechanism three ways:

1. the real setup.py mirror iterator covers every declared source;
2. every local Markdown link inside the mirror set resolves to a member
   of the mirror set (no dangling support links);
3. the installed wheel ships the full mirror with resolving links.
"""
import json
import posixpath
from importlib import metadata as importlib_metadata
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
MAX_FILES = 4000
REQUIRED_DATA = [
    "legends_coolify/_data/README.md",
    "legends_coolify/_data/LICENSE",
    "legends_coolify/_data/NOTICE.md",
    "legends_coolify/_data/SUPPORT.md",
    "legends_coolify/_data/CONTRIBUTING.md",
    "legends_coolify/_data/AGENTS.md",
    "legends_coolify/_data/docs/AGENT-RECIPE.md",
    "legends_coolify/_data/docs/KNOWLEDGE-PACK.md",
    "legends_coolify/_data/knowledge/coolify/pack.json",
    "legends_coolify/_data/wiki/index.md",
    "legends_coolify/_data/references/sources.md",
    "legends_coolify/_data/templates/private-operation-receipt.md",
    "legends_coolify/_data/skills/cto-legends/SKILL.md",
    "legends_coolify/_data/SECURITY.md",
    "legends_coolify/_data/CHANGELOG.md",
]


def load_mirror():
    """Evaluate setup.py with a stubbed setup() call; runs no packaging."""
    try:
        import setuptools  # noqa: F401
    except ImportError:
        raise unittest.SkipTest("setuptools is required to evaluate the data mirror")
    raw = (ROOT / "setup.py").read_text(encoding="utf-8")
    needle = "from setuptools import setup"
    assert needle in raw, "setup.py import shape changed; update the evaluation stub"
    source = raw.replace(needle, "# setup() call stubbed for evaluation", 1)
    namespace = {"setup": lambda *args, **kwargs: None}
    exec(source, namespace)
    return namespace


def mirror_members():
    """Mirror-relative posix path to source absolute path, via setup.py."""
    namespace = load_mirror()
    members = {}
    for source, relative in namespace["iter_mirror_sources"](ROOT):
        members[relative.as_posix()] = source
    return members


def local_target(raw):
    if raw.startswith(("https://", "http://", "mailto:", "#", "data:")):
        return None
    target = unquote(raw.split("#", 1)[0].split("?", 1)[0]).strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1]
    return target or None


def check_membership(members):
    """Every local link inside the mirror set must resolve inside the set."""
    errors = []
    pages = sorted(name for name in members if name.endswith(".md"))
    dirs = {"."}
    for name in members:
        parent = posixpath.dirname(name)
        while parent and parent != ".":
            dirs.add(parent)
            parent = posixpath.dirname(parent)
    for page in pages[:MAX_FILES]:
        try:
            text = members[page].read_text(encoding="utf-8-sig")
        except OSError:
            errors.append("Unreadable: %s" % page)
            continue
        for raw in LINK_RE.findall(text):
            target = local_target(raw)
            if target is None:
                continue
            resolved = posixpath.normpath(posixpath.join(posixpath.dirname(page), target))
            if resolved == "." or resolved.startswith(".."):
                errors.append("Escapes mirror: %s: %s" % (page, raw))
            elif resolved not in members and resolved not in dirs:
                errors.append("Dangling in mirror: %s: %s" % (page, raw))
    if len(pages) > MAX_FILES:
        errors.append("Mirror exceeds %d pages; capped walk is incomplete." % MAX_FILES)
    return errors


def check_installed(data_root):
    """Every local link in the installed mirror must resolve inside it."""
    errors = []
    pages = sorted(data_root.rglob("*.md"))
    for page in pages[:MAX_FILES]:
        try:
            text = page.read_text(encoding="utf-8-sig")
        except OSError:
            errors.append("Unreadable: %s" % page.name)
            continue
        for raw in LINK_RE.findall(text):
            target = local_target(raw)
            if target is None:
                continue
            resolved = (page.parent / target).resolve()
            try:
                resolved.relative_to(data_root.resolve())
            except ValueError:
                errors.append("Escapes mirror: %s: %s" % (page.name, raw))
                continue
            if not resolved.exists():
                errors.append("Dangling link: %s: %s" % (page.name, raw))
    if len(pages) > MAX_FILES:
        errors.append("Mirror exceeds %d pages; capped walk is incomplete." % MAX_FILES)
    return errors


class FakeDist:
    def __init__(self, anchor, direct=None):
        self._path = Path(anchor)
        self._direct = direct
        self.metadata = {"Name": "legends-coolify"}

    def read_text(self, name):
        return self._direct if name == "direct_url.json" else None


def installed_wheel_dist():
    """Return (dist, None) for a real installed wheel, else (None, reason)."""
    egg_seen = False
    editable_seen = False
    for dist in importlib_metadata.distributions():
        name = (dist.metadata["Name"] or "").lower()
        if name != "legends-coolify":
            continue
        anchor = getattr(dist, "_path", None)
        if anchor is None or Path(anchor).suffix != ".dist-info":
            egg_seen = True
            continue
        direct = dist.read_text("direct_url.json")
        editable = False
        if direct:
            try:
                info = json.loads(direct)
            except ValueError:
                info = {}
            editable = isinstance(info, dict) and isinstance(info.get("dir_info"), dict) \
                and bool(info["dir_info"].get("editable"))
        if editable:
            editable_seen = True
            continue
        return dist, None
    if editable_seen:
        return None, "editable install provides no wheel payload; source mirror tests apply"
    if egg_seen:
        return None, "source egg-info is not an installed wheel; run pip install . then rerun"
    return None, "requires installed legends-coolify wheel; run pip install . then rerun"


class Mirror(unittest.TestCase):
    def test_mirror_sources_exist(self):
        members = mirror_members()
        for key in ("README.md", "LICENSE", "AGENTS.md", "docs/AGENT-RECIPE.md",
                    "knowledge/coolify/pack.json", "wiki/index.md"):
            self.assertIn(key, members)
        self.assertGreater(len(members), 40)

    def test_mirror_links_resolve(self):
        self.assertEqual(check_membership(mirror_members()), [])

    def test_walker_catches_dangling(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "a.md").write_text("[ok](sub/b.md) [missing](gone.md)\n", encoding="utf-8")
            (root / "sub").mkdir()
            (root / "sub" / "b.md").write_text("[up](../a.md) ![img](pic.png)\n", encoding="utf-8")
            (root / "sub" / "pic.png").write_bytes(b"fake")
            members = {"a.md": root / "a.md", "sub/b.md": root / "sub" / "b.md",
                       "sub/pic.png": root / "sub" / "pic.png"}
            errors = check_membership(members)
        self.assertEqual(len(errors), 1)
        self.assertIn("gone.md", errors[0])

    def test_walker_accepts_good_mirror(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "README.md").write_text("[doc](docs/a.md) ![banner](assets/b.png)\n", encoding="utf-8")
            (root / "docs").mkdir()
            (root / "docs" / "a.md").write_text("[root](../README.md)\n", encoding="utf-8")
            (root / "assets").mkdir()
            (root / "assets" / "b.png").write_bytes(b"fake")
            members = {"README.md": root / "README.md", "docs/a.md": root / "docs" / "a.md",
                       "assets/b.png": root / "assets" / "b.png"}
            self.assertEqual(check_membership(members), [])

    def test_walker_ignores_external_and_fragments(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "a.md").write_text(
                "[web](https://example.org/x) [mail](mailto:a@example.org) "
                "[frag](#top) [with-frag](a.md#top) [query](a.md?v=1)\n", encoding="utf-8")
            self.assertEqual(check_membership({"a.md": root / "a.md"}), [])

    def test_walker_refuses_escape(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "sub").mkdir()
            (root / "sub" / "a.md").write_text("[out](../../outside.md)\n", encoding="utf-8")
            errors = check_membership({"sub/a.md": root / "sub" / "a.md"})
        self.assertEqual(len(errors), 1)
        self.assertIn("Escapes mirror", errors[0])


class WheelSelection(unittest.TestCase):
    def test_missing_distribution_skips(self):
        with patch.object(importlib_metadata, "distributions", return_value=[]):
            dist, reason = installed_wheel_dist()
        self.assertIsNone(dist)
        self.assertIn("pip install", reason)

    def test_source_egg_info_skips(self):
        fake = FakeDist("legends_coolify.egg-info")
        with patch.object(importlib_metadata, "distributions", return_value=[fake]):
            dist, reason = installed_wheel_dist()
        self.assertIsNone(dist)
        self.assertIn("egg-info", reason)

    def test_editable_install_skips(self):
        direct = '{"dir_info": {"editable": true}, "url": "file:///src"}'
        fake = FakeDist("legends_coolify-0.2.0.dist-info", direct)
        with patch.object(importlib_metadata, "distributions", return_value=[fake]):
            dist, reason = installed_wheel_dist()
        self.assertIsNone(dist)
        self.assertIn("editable", reason)

    def test_wheel_distribution_accepted(self):
        fake = FakeDist("legends_coolify-0.2.0.dist-info")
        with patch.object(importlib_metadata, "distributions", return_value=[fake]):
            dist, reason = installed_wheel_dist()
        self.assertIs(dist, fake)
        self.assertIsNone(reason)

    def test_wheel_preferred_over_shadowing_egg_info(self):
        egg = FakeDist("legends_coolify.egg-info")
        wheel = FakeDist("legends_coolify-0.2.0.dist-info")
        with patch.object(importlib_metadata, "distributions", return_value=[egg, wheel]):
            dist, reason = installed_wheel_dist()
        self.assertIs(dist, wheel)
        self.assertIsNone(reason)


class WheelSmoke(unittest.TestCase):
    def test_installed_wheel_ships_full_mirror(self):
        dist, reason = installed_wheel_dist()
        if dist is None:
            self.skipTest(reason)
        names = set()
        by_name = {}
        for entry in (dist.files or []):
            name = str(entry).replace("\\", "/")
            names.add(name)
            by_name[name] = entry
        missing = [name for name in REQUIRED_DATA if name not in names]
        self.assertEqual(missing, [])
        data_files = sorted(name for name in names if name.startswith("legends_coolify/_data/"))
        self.assertGreater(len(data_files), 40)
        data_root = Path(str(dist.locate_file(by_name[REQUIRED_DATA[0]]))).parent
        self.assertEqual(check_installed(data_root), [])


if __name__ == "__main__":
    unittest.main()
