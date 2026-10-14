"""Verify this test package and open a local upload-first workspace."""
from pathlib import Path,PurePosixPath
import hashlib,json,os,platform,runpy,struct,sys


# Windows Explorer can add these to any folder; they are not package files.
EXPLORER_FILES={'thumbs.db','desktop.ini'}


def verify_payload(root):
    print('Checking package files...',flush=True)
    manifest=json.loads((root/'FILE-MANIFEST.json').read_text(encoding='utf-8'))
    expected={entry['path']:entry for entry in manifest}
    if len(expected)!=len(manifest):raise ValueError('Package manifest contains duplicate paths.')
    listed=set(expected)|{'FILE-MANIFEST.json'}
    actual=set()
    for p in root.rglob('*'):
        if p.is_symlink():raise ValueError('Package contains an unexpected linked path.')
        name=p.relative_to(root).as_posix()
        if p.is_file() and (name in listed or p.name.lower() not in EXPLORER_FILES):actual.add(name)
    if listed-actual:raise ValueError('A package file is missing or changed. Extract a fresh complete copy.')
    extra=sorted(actual-listed)
    if extra:
        more=f' and {len(extra)-5} more' if len(extra)>5 else ''
        raise ValueError('This folder holds files that are not part of the package: '+', '.join(extra[:5])+more+'. Move these out of this folder, then start again.')
    for name,entry in expected.items():
        parts=PurePosixPath(name).parts
        if name.startswith('/') or '\\' in name or '..' in parts or ':' in name:raise ValueError('Package inventory contains an invalid path.')
        data=(root/name).read_bytes()
        if len(data)!=entry['bytes'] or hashlib.sha256(data).hexdigest()!=entry['sha256']:raise ValueError('A package file is missing or changed. Extract a fresh complete copy.')


def main():
    if os.name!='nt' or platform.system()!='Windows' or platform.machine().upper() not in {'AMD64','X86_64'} or struct.calcsize('P')!=8:
        raise ValueError('This test package requires 64-bit Windows on x64 hardware.')
    if sys.version_info[:3]!=(3,13,15):raise ValueError('Use the Python runtime included in this package.')
    root=Path(__file__).resolve().parent
    verify_payload(root)
    from lic_dsf.engine import engine_identity
    identity=engine_identity();package=json.loads((root/'PACKAGE-INFO.json').read_text(encoding='utf-8'))
    if identity['core_sha256']!=package['core_sha256'] or identity['engine_revision']!=package['engine_revision']:
        raise ValueError('The calculation runtime does not match the package identity.')
    if '--verify-only' in sys.argv:
        print('Package files and runtime identity match. Windows workflow checks remain separate.');return
    local=os.environ.get('LOCALAPPDATA')
    if not local:raise ValueError('The Windows local application-data folder is unavailable.')
    data=(Path(local)/'Teal Insights'/'LIC-DSF Scenario Tool').resolve()
    if data.is_relative_to(root) or any((parent/'.git').exists() for parent in (data,*data.parents)):
        raise ValueError('Saved work must be outside this package and Git repositories.')
    data.mkdir(parents=True,exist_ok=True)
    os.environ['MPLCONFIGDIR']=str(data/'cache'/'matplotlib')
    os.environ['PYTHONDONTWRITEBYTECODE']='1'
    os.environ['PYTHONUTF8']='1'
    sys.argv=['lic_dsf.app','--data-dir',str(data/'workspace'),'--port','0','--open-browser','--calculation-lock',str(data/'calculation.lock')]
    runpy.run_module('lic_dsf.app',run_name='__main__')


if __name__=='__main__':
    try:main()
    except Exception as error:
        print('The local workspace could not start: '+str(error),file=sys.stderr)
        raise SystemExit(1)
