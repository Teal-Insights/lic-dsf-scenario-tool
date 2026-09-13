"""Check Pages archive ownership and preserve the reviewed site bytes."""
import ast
import hashlib
from pathlib import Path
import stat
import tarfile
import tempfile
import textwrap
import unittest
from unittest.mock import patch
import zipfile


def load_packager(workflow):
    source = workflow.read_text(encoding="utf-8")
    start = source.index("          python3 - <<'PY'\n")
    block = source[start:].split("\n          PY", 1)[0].split("\n", 1)[1]
    tree = ast.parse(textwrap.dedent(block))
    tree.body = [node for node in tree.body
                 if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef))]
    namespace = {}
    exec(compile(tree, str(workflow), "exec"), namespace)
    return namespace["package_site"]


class PagesArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        workflow = Path(__file__).resolve().parents[1] / ".github/workflows/deploy-reviewed-pages.yml"
        self.package = load_packager(workflow)
        self.entries = {"index.html": b"Illustrative documentation",
                        ".well-known/skills/default/SKILL.md": b"Neutral example"}
        self.archive = self.directory / "site.zip"
        with zipfile.ZipFile(self.archive, "w") as archive:
            for name, value in self.entries.items():
                member = zipfile.ZipInfo(name)
                member.external_attr = (stat.S_IFREG | 0o644) << 16
                archive.writestr(member, value)
        self.digest = hashlib.sha256(self.archive.read_bytes()).hexdigest()
        self.destination = self.directory / "artifact.tar"

    def test_nonroot_owner_and_exact_site_bytes(self):
        with patch("os.getuid", return_value=1001, create=True), patch("os.getgid", return_value=1001, create=True):
            self.package(self.archive, self.digest, self.destination)
        with tarfile.open(self.destination) as archive:
            members = archive.getmembers()
            self.assertEqual({m.name.removeprefix("./"): archive.extractfile(m).read()
                              for m in members}, self.entries)
            for member in members:
                self.assertTrue(member.isfile())
                self.assertEqual((member.uid, member.gid), (1001, 1001))
                self.assertEqual((member.uname, member.gname), ("", ""))
                self.assertEqual(member.mode, 0o644)

    def test_root_packaging_is_rejected_without_output(self):
        with patch("os.getuid", return_value=0, create=True), patch("os.getgid", return_value=0, create=True):
            with self.assertRaisesRegex(ValueError, "unprivileged"):
                self.package(self.archive, self.digest, self.destination)
        self.assertFalse(self.destination.exists())

    def test_reviewed_digest_still_required(self):
        with patch("os.getuid", return_value=1001, create=True), patch("os.getgid", return_value=1001, create=True):
            with self.assertRaisesRegex(ValueError, "hash/size"):
                self.package(self.archive, "0" * 64, self.destination)
        self.assertFalse(self.destination.exists())


if __name__ == "__main__":
    unittest.main()
