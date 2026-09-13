"""Portable archive checks plus an actual GNU tar integration test on Linux."""
import ast
import hashlib
import io
from pathlib import Path
import stat
import subprocess
import sys
import tarfile
import tempfile
import textwrap
import unittest
from unittest.mock import patch
import zipfile


def load_functions(workflow):
    source = workflow.read_text(encoding='utf-8')
    block = source.split("          python3 - <<'PY'\n", 1)[1].split('\n          PY', 1)[0]
    tree = ast.parse(textwrap.dedent(block))
    tree.body = [node for node in tree.body
                 if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef))]
    namespace = {}
    exec(compile(tree, str(workflow), 'exec'), namespace)
    return namespace


class PagesArtifactTests(unittest.TestCase):
    def setUp(self):
        workflow = Path(__file__).resolve().parents[1] / '.github/workflows/deploy-reviewed-pages.yml'
        self.functions = load_functions(workflow)
        self.package = self.functions['package_site']
        self.verify = self.functions['verify_pages_tar']
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.entries = {'index.html': b'Illustrative documentation',
                        '.well-known/skills/default/SKILL.md': b'Neutral example',
                        'assets/style.css': b'body {}'}
        self.archive = self.directory/'site.zip'
        self.destination = self.directory/'artifact.tar'
        self.write_zip(self.entries)
        self.uid = patch('os.getuid', return_value=1001, create=True)
        self.gid = patch('os.getgid', return_value=1001, create=True)
        self.uid.start()
        self.gid.start()
        self.addCleanup(self.uid.stop)
        self.addCleanup(self.gid.stop)

    def write_zip(self, entries, kind=stat.S_IFREG):
        with zipfile.ZipFile(self.archive, 'w') as archive:
            for name, data in entries.items():
                member = zipfile.ZipInfo(name)
                member.external_attr = (kind | 0o644) << 16
                archive.writestr(member, data)
        with zipfile.ZipFile(self.archive) as archive:
            self.assertEqual(archive.namelist(), list(entries))
        self.digest = hashlib.sha256(self.archive.read_bytes()).hexdigest()

    def mock_serializer(self, command, **kwargs):
        self.assertEqual(kwargs['env'], {'PATH': '/usr/bin:/bin', 'LANG': 'C', 'LC_ALL': 'C'})
        if command == ['/usr/bin/tar', '--version']:
            return subprocess.CompletedProcess(command, 0, stdout='tar (GNU tar) test double')
        self.assertEqual(command[:4], ['/usr/bin/tar', '--dereference', '--hard-dereference', '--directory'])
        self.assertEqual(command[5:], ['-cvf', str(self.destination), '--exclude=.git', '--exclude=.github', '.'])
        self.assertEqual(kwargs['timeout'], 120)
        self.assertTrue(kwargs['check'])
        site = Path(command[4])
        self.assertEqual({p.relative_to(site).as_posix(): p.read_bytes()
                          for p in site.rglob('*') if p.is_file()}, self.entries)
        self.staging = site
        with tarfile.open(self.destination, 'w', format=tarfile.GNU_FORMAT) as archive:
            for path in [site, *sorted(site.rglob('*'))]:
                name = './' + path.relative_to(site).as_posix() if path != site else './'
                member = tarfile.TarInfo(name)
                member.uid = member.gid = 1001
                member.uname = member.gname = 'runner'
                if path.is_dir():
                    member.type = tarfile.DIRTYPE
                    member.mode = 0o755
                    archive.addfile(member)
                else:
                    data = path.read_bytes()
                    member.mode = 0o644
                    member.size = len(data)
                    archive.addfile(member, io.BytesIO(data))
        return subprocess.CompletedProcess(command, 0)

    def test_materialization_and_exact_official_command_contract(self):
        with patch('subprocess.run', side_effect=self.mock_serializer) as run:
            self.package(self.archive, self.digest, self.destination)
        self.assertEqual(run.call_count, 2)
        self.assertFalse(self.staging.exists())
        self.verify(self.destination, self.entries)

    @unittest.skipUnless(sys.platform == 'linux', 'Actual GNU tar runs on Linux CI.')
    def test_actual_linux_gnu_tar_preserves_hidden_files_and_directories(self):
        # Use actual runner identity and serializer, not the portable test double.
        self.uid.stop()
        self.gid.stop()
        self.package(self.archive, self.digest, self.destination)
        self.verify(self.destination, self.entries)

    def test_root_refused_without_output(self):
        with patch('os.getuid', return_value=0, create=True), patch('subprocess.run') as run:
            with self.assertRaisesRegex(ValueError, 'unprivileged'):
                self.package(self.archive, self.digest, self.destination)
            run.assert_not_called()
        self.assertFalse(self.destination.exists())

    def test_non_gnu_refused_without_output(self):
        with patch('subprocess.run', return_value=subprocess.CompletedProcess([], 0, stdout='bsdtar')):
            with self.assertRaisesRegex(ValueError, 'GNU tar'):
                self.package(self.archive, self.digest, self.destination)
        self.assertFalse(self.destination.exists())

    def test_existing_output_preserved(self):
        self.destination.write_bytes(b'preserve')
        with self.assertRaisesRegex(ValueError, 'already exists'):
            self.package(self.archive, self.digest, self.destination)
        self.assertEqual(self.destination.read_bytes(), b'preserve')

    # The production packager runs on Linux. Preserve malformed ZIP names
    # during both fixture writing and parsing, including on Windows hosts.
    @patch('zipfile.os.sep', '/')
    def test_prior_malicious_archives(self):
        cases = [('wrong_hash', self.entries, stat.S_IFREG),
                 ('single_backslash', dict(self.entries, **{r'folder\name': b'x'}), stat.S_IFREG),
                 ('double_backslash', dict(self.entries, **{r'folder\\name': b'x'}), stat.S_IFREG),
                 ('traversal', dict(self.entries, **{'../outside': b'x'}), stat.S_IFREG),
                 ('symlink', self.entries, stat.S_IFLNK),
                 ('case_collision', dict(self.entries, **{'INDEX.html': b'x'}), stat.S_IFREG),
                 ('wrong_root', {'site/index.html': b'x'}, stat.S_IFREG),
                 ('file_parent', dict(self.entries, **{'assets': b'x'}), stat.S_IFREG),
                 ('git', dict(self.entries, **{'.git/config': b'x'}), stat.S_IFREG)]
        for name, entries, kind in cases:
            with self.subTest(case=name):
                self.write_zip(entries, kind)
                with patch('subprocess.run') as run:
                    with self.assertRaises(ValueError):
                        self.package(self.archive, '0'*64 if name == 'wrong_hash' else self.digest,
                                     self.destination)
                    run.assert_not_called()
                self.assertFalse(self.destination.exists())

    def test_post_tar_faults(self):
        for fault in ('extra_file', 'extra_directory', 'symlink', 'hardlink', 'wrong_owner',
                      'wrong_mode', 'wrong_directory_mode', 'changed_bytes', 'duplicate', 'missing_directory', 'unsafe_path'):
            with self.subTest(fault=fault):
                with patch('subprocess.run', side_effect=self.mock_serializer):
                    self.package(self.archive, self.digest, self.destination)
                with tarfile.open(self.destination) as archive:
                    members = [(member, archive.extractfile(member).read() if member.isfile() else None)
                               for member in archive]
                if fault in ('extra_file', 'extra_directory', 'duplicate'):
                    member = tarfile.TarInfo('./extra')
                    member.uid = member.gid = 1001
                    member.mode = 0o755 if fault == 'extra_directory' else 0o644
                    if fault == 'extra_directory': member.type = tarfile.DIRTYPE
                    members.append(members[-1] if fault == 'duplicate' else (member, b''))
                elif fault == 'wrong_directory_mode':
                    next(m for m, data in members if m.isdir()).mode = 0o700
                elif fault == 'missing_directory':
                    members = [(m, data) for m, data in members if m.name != '.']
                else:
                    member, data = next((m, data) for m, data in members if m.isfile())
                    if fault == 'symlink': member.type = tarfile.SYMTYPE
                    elif fault == 'hardlink': member.type = tarfile.LNKTYPE
                    elif fault == 'wrong_owner': member.uid = 0
                    elif fault == 'wrong_mode': member.mode = 0o777
                    elif fault == 'unsafe_path': member.name = '../outside'
                    elif fault == 'changed_bytes':
                        members = [(m, b'X'*len(d) if m is member else d) for m, d in members]
                with tarfile.open(self.destination, 'w') as archive:
                    for member, data in members:
                        archive.addfile(member, io.BytesIO(data) if data is not None else None)
                with self.assertRaises(ValueError):
                    self.verify(self.destination, self.entries)
                self.destination.unlink()


if __name__ == '__main__':
    unittest.main()
