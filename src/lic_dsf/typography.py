"""Exact redistributable font assets, independent of installed system fonts."""
from pathlib import Path
from matplotlib import font_manager

FONT_FOLDER = Path(__file__).parent / 'fonts'
FONT_FAMILY = 'LICDSF Bundled Inter'

def font_properties(family='Inter', size=10, weight='normal', **kwargs):
    serif = family == 'IBM Plex Serif'
    bold = weight in ('bold', 'semibold', 'demibold', 600, 700)
    name = 'IBMPlexSerif-SemiBold.otf' if serif else ('Inter-SemiBold.otf' if bold else 'Inter-Regular.otf')
    return font_manager.FontProperties(fname=str(FONT_FOLDER / name), size=size, weight=weight, **kwargs)

def register_fonts():
    # Default axis/tick/text artists use a private family name whose only entries
    # point to these exact package files. Explicit measurements use fname above.
    for weight, name in [('normal', 'Inter-Regular.otf'), ('bold', 'Inter-SemiBold.otf')]:
        entry = font_manager.FontEntry(fname=str(FONT_FOLDER / name), name=FONT_FAMILY,
                                       style='normal', variant='normal', weight=weight, stretch='normal')
        if not any(e.name == entry.name and e.weight == entry.weight and e.fname == entry.fname
                   for e in font_manager.fontManager.ttflist):
            font_manager.fontManager.ttflist.append(entry)
    font_manager.fontManager._findfont_cached.cache_clear()
