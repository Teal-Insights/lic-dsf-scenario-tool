"""Finish named public resources and known generated links; no deployment."""
from pathlib import Path
import hashlib
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]


def local_tooltips(site):
    """Retain bundled tooltips, but never acquire missing code from a CDN."""
    path = site / 'tooltips.js'
    data = path.read_bytes()
    marker = '// LIC-DSF docs: use local Tippy only; native titles remain the fallback.\n'
    digest = hashlib.sha256(data).hexdigest()
    if digest == '4c2cef272a58ca8edaedee77fa473d85d697eb6c701773aa30596a56b218a962':
        return
    if digest != '2c2ea9795a9b9b067f72b29bf391e9767dfe925e864848b455beab54fac71076':
        raise SystemExit('Great Docs tooltip source changed; review the local-only adapter.')
    text = data.decode('utf-8')
    text = re.sub(r'^    (?:popperUrl|tippyUrl):.*\n', '', text, flags=re.MULTILINE)
    start = text.index('  function loadScript(url) {')
    end = text.index('\n  /**', start)
    text = text[:start] + text[end:]
    start = text.index('  function loadTippy() {')
    end = text.index('\n  /**', start)
    text = text[:start] + '''  function loadTippy() {
    tippyReady = Boolean(window.tippy);
    return Promise.resolve();
  }
''' + text[end:]
    path.write_text(marker + text, encoding='utf-8')


def truthful_generated_skill(site):
    """Keep generated skills usable without advertising an unpublished package."""
    import html
    import json

    base = 'https://teal-insights.github.io/lic-dsf-scenario-tool/'
    copies = ('skill.md', '.well-known/skills/default/SKILL.md',
              '.well-known/agent-skills/lic-dsf-scenario-tool/SKILL.md')
    originals = [(site / name).read_text(encoding='utf-8') for name in copies]
    if len(set(originals)) != 1:
        raise SystemExit('Generated skill copies differ; review the build output.')
    original = originals[0]
    old_install = '```bash\npip install lic-dsf-scenario-tool\n```'
    new_install = ('Use the [source installation guide](' + base +
                   'user-guide/source-installation.html).\n'
                   'No PyPI installation is currently offered.\n')
    replacements = [(old_install, new_install),
                    ('[llms.txt](llms.txt)', '[llms.txt](' + base + 'llms.txt)'),
                    ('[llms-full.txt](llms-full.txt)',
                     '[llms-full.txt](' + base + 'llms-full.txt)')]
    already_finished = new_install in original
    if not already_finished and original.count(old_install) != 1:
        raise SystemExit('Generated skill installation changed; review the build output.')
    corrected = original
    for old, new in replacements:
        corrected = corrected.replace(old, new)
    if 'pip install lic-dsf-scenario-tool' in corrected:
        raise SystemExit('Unreviewed package installation remains in the generated skill.')

    page = site / 'skills.html'
    page_text = page.read_text(encoding='utf-8')
    pattern = r'<code class="sourceCode markdown">(.*?)</code>'
    matches = list(re.finditer(pattern, page_text, re.DOTALL))
    matching = [m for m in matches if html.unescape(re.sub(r'<[^>]*>', '', m.group(1))).strip()
                == original.strip()]
    if len(matching) != 1:
        raise SystemExit('Generated skill HTML differs from its text; review the build output.')
    match = matching[0]
    # Preserve numbered self-link anchors, avoiding stale syntax-highlighted text.
    lines = corrected.rstrip('\n').split('\n')
    code = '<code class="sourceCode markdown">' + '\n'.join(
        f'<span id="cb1-{n}"><a href="#cb1-{n}" aria-hidden="true" tabindex="-1"></a>'
        + html.escape(line) + '</span>' for n, line in enumerate(lines, 1)) + '</code>'
    page_text = page_text[:match.start()] + code + page_text[match.end():]

    search_path = site / 'search.json'
    search = json.loads(search_path.read_text(encoding='utf-8'))
    entries = [entry for entry in search if entry.get('href') == 'skills.html']
    if len(entries) != 1:
        raise SystemExit('Expected one generated skill search record.')
    entry = entries[0]
    if not already_finished and entry.get('text', '').count(old_install) != 1:
        raise SystemExit('Generated skill search text changed; review the build output.')
    for old, new in replacements:
        entry['text'] = entry['text'].replace(old, new)
    if 'pip install lic-dsf-scenario-tool' in entry['text']:
        raise SystemExit('Unreviewed package installation remains in search.')
    # Validate every representation before writing any corrected file.
    for name in copies:
        (site / name).write_text(corrected, encoding='utf-8')
    page.write_text(page_text, encoding='utf-8')
    search_path.write_text(json.dumps(search, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    site = ROOT / 'great-docs/_site'
    local_tooltips(site)
    truthful_generated_skill(site)
    resources = {
        'schemas/scenario-file-v1.schema.json': 'schemas/scenario-file-v1.schema.json',
        'schemas/scenario-v1.schema.json': 'schemas/scenario-v1.schema.json',
        'schemas/comparison-v3.schema.json': 'schemas/comparison-v3.schema.json',
        'docs/template-source.json': 'user-guide/template-source.json',
        'docs/dependency-audit.json': 'user-guide/dependency-audit.json',
        'src/lic_dsf/ida21.py': 'src/lic_dsf/ida21.py',
    }
    website_licenses = ('licenses/OFL-Inter.txt', 'licenses/OFL-Plex.txt', 'licenses/anchorjs-LICENSE.txt', 'licenses/autocomplete-LICENSE.txt', 'licenses/bootstrap-LICENSE.txt', 'licenses/bootstrap-icons-LICENSE.txt', 'licenses/clipboard-LICENSE.txt', 'licenses/fuse-LICENSE.txt', 'licenses/great-docs-LICENSE.txt', 'licenses/headroom-LICENSE.txt', 'licenses/htm-LICENSE.txt', 'licenses/jetbrains-mono-LICENSE.txt', 'licenses/lucide-LICENSE.txt', 'licenses/popper-LICENSE.txt', 'licenses/preact-LICENSE.txt', 'licenses/quarto-LICENSE.txt', 'licenses/tippy-LICENSE.txt')
    resources.update({name: name for name in website_licenses})
    for source, target in resources.items():
        original = ROOT / source
        if original.is_symlink() or not original.is_file():
            raise SystemExit(f'Missing or linked public resource: {source}')
        destination = site / target
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(original, destination)
    # Supply the advertised plain-text collection from authored public guides.
    guides = sorted((ROOT / 'docs').glob('*.md'))
    if any(p.is_symlink() for p in guides):
        raise SystemExit('Linked guide is not an admissible documentation input.')
    (site / 'llms-full.txt').write_text('\n\n'.join(
        p.read_text(encoding='utf-8') for p in guides), encoding='utf-8')
    for name in ('contributing.html', 'code-of-conduct.html'):
        path = site / name
        if not path.exists():
            continue
        text = path.read_text(encoding='utf-8')
        for old, new in [('SECURITY.md', 'user-guide/security.html'),
                         ('CONTRIBUTING.md', 'contributing.html'),
                         ('CODE_OF_CONDUCT.md', 'code-of-conduct.html')]:
            text = text.replace(f'href="{old}"', f'href="{new}"')
        path.write_text(text, encoding='utf-8')
    # The generator's API index points to anchors omitted by its page template.
    for path in (site / 'reference').glob('*.html'):
        if path.stem == 'index' or not re.fullmatch(r'[A-Za-z_]\w*', path.stem):
            continue
        anchor = 'lic_dsf.' + path.stem
        text = path.read_text(encoding='utf-8')
        if f'id="{anchor}"' not in text:
            marker = '<header id="title-block-header"'
            if marker not in text:
                raise SystemExit(f'Expected reference header missing: {path.name}')
            text = text.replace(marker, f'<span id="{anchor}"></span>\n' + marker, 1)
            path.write_text(text, encoding='utf-8')
    print('Finished named public resources and generated policy/API links.')


if __name__ == '__main__':
    main()
