"""Local unsigned preparation and Windows-only read-only signature sealing.

No signing, cloud calls, native build, package-file mutation or release approval.
The candidate bundle is for a later independently reviewed assembler integration.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import struct
import subprocess
import sys

SCHEMA = 'licdsf-windows-signing-plan-v1'
MANIFEST = 'FILE-MANIFEST.json'
ROLES = frozenset({'application-launcher', 'application-installer'})
MAX_FILES = 10000
MAX_FILE = 256 * 1024 * 1024
MAX_TOTAL = 1024 * 1024 * 1024
FACTS_SCRIPT = Path(__file__).with_name('signature_facts.ps1')


class PreparationError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def _fail(code):
    raise PreparationError(code)


def _json(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False,
                       allow_nan=False) + '\n').encode('utf-8')


def _decode(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('DUPLICATE_JSON_FIELD')
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=unique)


def _identity(st):
    return (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns)


def _linked(st):
    return stat.S_ISLNK(st.st_mode) or bool(getattr(st, 'st_file_attributes', 0) & 0x400)


def _read(path, code):
    try:
        before = path.lstat()
        if _linked(before) or not stat.S_ISREG(before.st_mode) or before.st_size > MAX_FILE:
            _fail(code)
        fd = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
        with os.fdopen(fd, 'rb') as stream:
            opened = os.fstat(stream.fileno())
            if _identity(opened) != _identity(before):
                _fail(code)
            raw = stream.read(MAX_FILE + 1)
            after_open = os.fstat(stream.fileno())
        after = path.lstat()
        if len(raw) > MAX_FILE or _identity(before) != _identity(after_open) or _identity(before) != _identity(after) or _linked(after):
            _fail(code)
        return raw, _identity(after)
    except OSError:
        _fail(code)


def _name(name):
    if type(name) is not str or not name or '\\' in name or ':' in name:
        return False
    p = PurePosixPath(name)
    reserved = {'CON', 'PRN', 'AUX', 'NUL'} | {f'COM{x}' for x in range(1, 10)} | {f'LPT{x}' for x in range(1, 10)}
    return not p.is_absolute() and p.as_posix() == name and all(x not in {'.', '..', '.git', '__pycache__'} and not x.endswith((' ', '.')) and x.split('.')[0].upper() not in reserved for x in p.parts) and not any(ord(x) < 32 or x in '<>\"|?*' for x in name)


def _rows(value, code):
    if type(value) is not list or not value or len(value) > MAX_FILES:
        _fail(code)
    seen = set()
    for row in value:
        if type(row) is not dict or set(row) != {'path', 'sha256', 'bytes'}:
            _fail(code)
        if not _name(row['path']) or row['path'] == MANIFEST or row['path'].casefold() in seen:
            _fail(code)
        seen.add(row['path'].casefold())
        if type(row['sha256']) is not str or re.fullmatch('[0-9a-f]{64}', row['sha256']) is None:
            _fail(code)
        if type(row['bytes']) is not int or not 0 <= row['bytes'] <= MAX_FILE:
            _fail(code)
    if sum(x['bytes'] for x in value) > MAX_TOTAL:
        _fail(code)
    return sorted(value, key=lambda x: x['path'])


def _tree(root, code):
    try:
        root = Path(root)
        if _linked(root.lstat()) or not root.is_dir():
            _fail(code)
        result = {}
        seen = set()
        def scan_failed(_error):
            _fail(code)

        for base, dirs, files in os.walk(root, followlinks=False, onerror=scan_failed):
            for name in dirs + files:
                p = Path(base) / name
                st = p.lstat()
                rel = p.relative_to(root).as_posix()
                if _linked(st) or not _name(rel) or rel.casefold() in seen:
                    _fail(code)
                seen.add(rel.casefold())
                if not stat.S_ISREG(st.st_mode) and not stat.S_ISDIR(st.st_mode):
                    _fail(code)
            for name in files:
                p = Path(base) / name
                raw, identity = _read(p, code)
                result[p.relative_to(root).as_posix()] = (hashlib.sha256(raw).hexdigest(), len(raw), identity)
                if len(result) > MAX_FILES + 1:
                    _fail(code)
        if sum(x[1] for x in result.values()) > MAX_TOTAL:
            _fail(code)
        return result
    except OSError:
        _fail(code)


def _manifest(root, code):
    raw, _ = _read(Path(root) / MANIFEST, code)
    try:
        rows = _rows(_decode(raw), code)
    except (ValueError, UnicodeError):
        _fail(code)
    return hashlib.sha256(raw).hexdigest(), rows


def _pe(path):
    raw, _ = _read(path, 'APPLICATION_TARGET_INVALID')
    try:
        pe = struct.unpack_from('<I', raw, 0x3c)[0]
        return len(raw) >= 512 and raw[:2] == b'MZ' and raw[pe:pe+4] == b'PE\0\0' and struct.unpack_from('<H', raw, pe+4)[0] == 0x8664 and struct.unpack_from('<H', raw, pe+24)[0] == 0x20b
    except (struct.error, IndexError):
        return False


def _targets(root, targets, rows):
    if type(targets) is not list or len(targets) > 32:
        _fail('APPLICATION_TARGET_INVALID')
    available = {x['path'] for x in rows}
    seen = set()
    for target in targets:
        if type(target) is not dict or set(target) != {'path', 'role'}:
            _fail('APPLICATION_TARGET_INVALID')
        name = target['path']
        if not _name(name) or name not in available or name.casefold().startswith('runtime/') or name.casefold() in seen or type(target['role']) is not str or target['role'] not in ROLES or Path(name).suffix.lower() != '.exe':
            _fail('APPLICATION_TARGET_INVALID')
        if not _pe(Path(root) / name):
            _fail('APPLICATION_TARGET_INVALID')
        seen.add(name.casefold())
    return sorted(targets, key=lambda x: x['path'])


def prepare_unsigned(root, targets, expected_subject=None):
    """Read the existing payload contract; an empty target list is informative."""
    digest, rows = _manifest(root, 'PAYLOAD_MANIFEST_INVALID')
    tree = _tree(root, 'PAYLOAD_MANIFEST_INVALID')
    if set(tree) != {x['path'] for x in rows} | {MANIFEST} or any(tree[x['path']][:2] != (x['sha256'], x['bytes']) for x in rows):
        _fail('PAYLOAD_MANIFEST_INVALID')
    selected = _targets(root, targets, rows)
    if expected_subject is not None and (type(expected_subject) is not str or not expected_subject or any(ord(c) < 32 for c in expected_subject)):
        _fail('EXPECTED_PUBLISHER_REQUIRED')
    plan = {'schema': SCHEMA, 'source_manifest_sha256': digest,
            'payload': rows, 'targets': selected, 'expected_subject': expected_subject}
    if _tree(root, 'PAYLOAD_CHANGED') != tree or _manifest(root, 'PAYLOAD_CHANGED')[0] != digest:
        _fail('PAYLOAD_CHANGED')
    return _decode(_json(plan))


def _plan(root, plan):
    if type(plan) is not dict or set(plan) != {'schema', 'source_manifest_sha256', 'payload', 'targets', 'expected_subject'} or plan['schema'] != SCHEMA:
        _fail('SIGNING_PLAN_INVALID')
    rows = _rows(plan['payload'], 'SIGNING_PLAN_INVALID')
    if type(plan['source_manifest_sha256']) is not str or re.fullmatch('[0-9a-f]{64}', plan['source_manifest_sha256']) is None:
        _fail('SIGNING_PLAN_INVALID')
    if not plan['targets']:
        _fail('APPLICATION_SIGNING_TARGETS_MISSING')
    if type(plan['expected_subject']) is not str or not plan['expected_subject'] or any(ord(c) < 32 for c in plan['expected_subject']):
        _fail('EXPECTED_PUBLISHER_REQUIRED')
    targets = _targets(root, plan['targets'], rows)
    digest, original = _manifest(root, 'PAYLOAD_CHANGED')
    if digest != plan['source_manifest_sha256'] or original != rows:
        _fail('PAYLOAD_CHANGED')
    tree = _tree(root, 'PAYLOAD_CHANGED')
    selected = {x['path'] for x in targets}
    if set(tree) != {x['path'] for x in rows} | {MANIFEST} or any(tree[x['path']][:2] != (x['sha256'], x['bytes']) for x in rows if x['path'] not in selected):
        _fail('PAYLOAD_CHANGED')
    return tree


def _tool(path):
    p = Path(path)
    if not p.is_absolute() or p.suffix.lower() != '.exe':
        _fail('WINDOWS_TOOL_INVALID')
    raw, identity = _read(p, 'WINDOWS_TOOL_INVALID')
    return p, (hashlib.sha256(raw).hexdigest(), identity)


def _facts(raw, subject):
    try:
        d = _decode(raw.decode('utf-8-sig'))
    except (ValueError, UnicodeError, AttributeError):
        _fail('SIGNATURE_FACTS_INVALID')
    keys = {'status', 'signature_type', 'subject', 'issuer', 'thumbprint', 'code_signing_eku', 'timestamp_present', 'embedded_signature_count', 'primary_signer_count', 'nested_signature_count'}
    if type(d) is not dict or set(d) != keys or d['status'] != 'Valid' or d['signature_type'] != 'Authenticode' or d['subject'] != subject:
        _fail('SIGNATURE_FACTS_INVALID')
    if d['code_signing_eku'] is not True or d['timestamp_present'] is not True or any(type(d[k]) is not int for k in ('embedded_signature_count', 'primary_signer_count', 'nested_signature_count')) or (d['embedded_signature_count'], d['primary_signer_count'], d['nested_signature_count']) != (1, 1, 0):
        _fail('SIGNATURE_FACTS_INVALID')
    if type(d['issuer']) is not str or not d['issuer'] or type(d['thumbprint']) is not str or re.fullmatch('[0-9A-Fa-f]{40}', d['thumbprint']) is None:
        _fail('SIGNATURE_FACTS_INVALID')
    return d


def verify_sealing_candidate(root, plan, signtool, powershell):
    """Read-only Windows verification; return a bundle without changing payload."""
    observed = _plan(root, plan)
    if sys.platform != 'win32':
        _fail('WINDOWS_VERIFICATION_REQUIRED')
    before_plan = _json(plan)
    tool, tool_state = _tool(signtool)
    shell, shell_state = _tool(powershell)
    script_raw, script_identity = _read(FACTS_SCRIPT, 'WINDOWS_TOOL_INVALID')
    script_state = (hashlib.sha256(script_raw).hexdigest(), script_identity)
    receipts = []

    def recheck():
        # No cached graph, signature outcome or source state is reused.
        if _json(plan) != before_plan or _plan(root, plan) != observed:
            _fail('VERIFICATION_INPUT_CHANGED')
        if _tool(tool)[1] != tool_state or _tool(shell)[1] != shell_state:
            _fail('VERIFICATION_INPUT_CHANGED')
        raw, identity = _read(FACTS_SCRIPT, 'WINDOWS_TOOL_INVALID')
        if (hashlib.sha256(raw).hexdigest(), identity) != script_state:
            _fail('VERIFICATION_INPUT_CHANGED')

    for target in plan['targets']:
        recheck()
        path = (Path(root) / target['path']).absolute()
        commands = [[str(tool), 'verify', '/pa', '/all', '/v', '/tw', str(path)],
                    [str(shell), '-NoProfile', '-NonInteractive', '-File', str(FACTS_SCRIPT), str(path)]]
        outputs = []
        for command in commands:
            try:
                result = subprocess.run(command, capture_output=True, timeout=30, check=False)
            except (OSError, subprocess.SubprocessError):
                _fail('SIGNATURE_VERIFICATION_FAILED')
            recheck()
            if result.returncode != 0:
                _fail('SIGNATURE_VERIFICATION_FAILED')
            outputs.append(result.stdout)
        facts = _facts(outputs[1], plan['expected_subject'])
        receipts.append({'path': target['path'], 'role': target['role'],
                         'sha256': observed[target['path']][0], 'bytes': observed[target['path']][1],
                         'facts': facts})
    recheck()
    rows = [{'path': x, 'sha256': v[0], 'bytes': v[1]}
            for x, v in sorted(observed.items()) if x != MANIFEST]
    return {'schema': 'licdsf-windows-sealing-candidate-v1',
            'status': 'SIGNATURE_VERIFIED_MANIFEST_CANDIDATE',
            'signed_product_accepted': False, 'windows_first_launch_accepted': False,
            'source_manifest_sha256': plan['source_manifest_sha256'],
            'file_manifest': rows, 'file_manifest_sha256': hashlib.sha256(_json(rows)).hexdigest(),
            'signed_targets': receipts,
            'verification_tools': {'signtool_sha256': tool_state[0],
                                   'powershell_sha256': shell_state[0],
                                   'reader_sha256': script_state[0]}}



def write_new_json(path, value, root):
    """Emit one new coordination artifact outside the payload; never overwrite."""
    p = Path(path)
    if p.resolve().is_relative_to(Path(root).resolve()):
        _fail('OUTPUT_INSIDE_PAYLOAD')
    data = _json(value)
    try:
        with p.open('xb') as stream:
            stream.write(data)
    except FileExistsError:
        _fail('OUTPUT_EXISTS')
    except OSError:
        _fail('OUTPUT_WRITE_FAILED')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest='command', required=True)
    prepare = sub.add_parser('prepare-unsigned')
    prepare.add_argument('--payload', required=True, type=Path)
    prepare.add_argument('--targets', required=True, type=Path)
    prepare.add_argument('--expected-subject')
    prepare.add_argument('--output', required=True, type=Path)
    verify = sub.add_parser('verify-sealing-candidate')
    verify.add_argument('--payload', required=True, type=Path)
    verify.add_argument('--plan', required=True, type=Path)
    verify.add_argument('--signtool', required=True, type=Path)
    verify.add_argument('--powershell', required=True, type=Path)
    verify.add_argument('--output', required=True, type=Path)
    args = ap.parse_args(argv)
    try:
        if args.command == 'prepare-unsigned':
            value = prepare_unsigned(args.payload, _decode(args.targets.read_bytes()), args.expected_subject)
            status = 'UNSIGNED_PREPARATION'
            count = len(value['targets'])
        else:
            value = verify_sealing_candidate(args.payload, _decode(args.plan.read_bytes()), args.signtool, args.powershell)
            status = value['status']
            count = len(value['signed_targets'])
        write_new_json(args.output, value, args.payload)
        print(json.dumps({'status': status, 'application_targets': count,
                          'signed_product_accepted': False, 'windows_first_launch_accepted': False}))
        return 0
    except PreparationError as exc:
        print(json.dumps({'status': 'REFUSED', 'code': exc.code}), file=sys.stderr)
        return 1
    except (OSError, ValueError, UnicodeError):
        print(json.dumps({'status': 'REFUSED', 'code': 'INPUT_FILE_INVALID'}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
