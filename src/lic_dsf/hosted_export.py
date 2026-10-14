"""Bounded, disposable renderer process; request and output are never logged."""
import json
from pathlib import Path
import resource
import sys

def main(directory):
    resource.setrlimit(resource.RLIMIT_CPU, (50, 55))
    resource.setrlimit(resource.RLIMIT_FSIZE, (32 * 1024 * 1024,) * 2)
    if sys.platform == 'linux':
        resource.setrlimit(resource.RLIMIT_AS, (2 * 1024 ** 3,) * 2)
    directory = Path(directory)
    request = json.loads((directory / 'request.json').read_text(encoding='utf-8'))
    from .worker import start_guard
    start_guard(request, directory)
    comparison, data = request['comparison'], request['data']
    fmt = data.get('format', 'json')
    if fmt == 'zip':
        from .briefing_pack import render_pack
        body, ctype, name = render_pack(comparison), 'application/zip', 'lic-dsf-briefing-packet.zip'
    elif fmt == 'xlsx':
        from .briefing_pack import tables, workbook_bytes
        body, ctype, name = workbook_bytes(tables(comparison), comparison), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'scenario-tables.xlsx'
    elif data.get('metric') is not None:
        from .charts import render_indicator
        body = render_indicator(comparison, data['metric'], data.get('view'), fmt)
        ctype, name = ('image/svg+xml' if fmt == 'svg' else 'image/png'), 'scenario-chart.' + fmt
    else:
        from .charts import render_comparison
        body = render_comparison(comparison, view=data.get('view'), format=fmt)
        ctype, name = ('image/png' if fmt == 'png' else 'application/pdf'), 'scenario-comparison.' + fmt
    (directory / 'body').write_bytes(body)
    (directory / 'meta.json').write_text(json.dumps([ctype, name]), encoding='utf-8')

if __name__ == '__main__':
    main(sys.argv[1])
