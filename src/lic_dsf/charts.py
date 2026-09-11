"""Two presentation views over saved LIC-DSF results; no calculation engine calls.

PNG is a six-panel overview. PDF adds a large, standalone page per indicator.
The summary helper is the accessible full-precision companion to either view.
Requires matplotlib; uses its freely distributed DejaVu Sans font.
"""
from __future__ import annotations

import io
import math
import re
import textwrap
import threading
from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP
from .chart_context import validate_chart_context
from .rationale import rationale_entries

# Indicator order follows the supported external four-panel and public two-panel subset.
METRICS = (
    ('ext_pv_gdp', 'PV of PPG external debt-to-GDP ratio', 'percent of GDP', 'CI Summary!I11'),
    ('ext_pv_exports', 'PV of PPG external debt-to-exports ratio', 'percent of exports', 'CI Summary!I10'),
    ('ext_ds_exports', 'PPG external debt service-to-exports ratio', 'percent of exports', 'CI Summary!I13'),
    ('ext_ds_revenue', 'PPG external debt service-to-revenue ratio', 'percent of revenue', 'CI Summary!I14'),
    ('public_pv_gdp', 'PV of total public debt-to-GDP ratio', 'percent of GDP', 'CI Summary!L9'),
    ('public_pv_revenue', 'PV of total public debt-to-revenue ratio', 'percent of revenue', None),
)
COLORS = {'navy': '#143E5A', 'cyan': '#0094BC', 'gray': '#5C6770',
          'ink': '#2A2A2A', 'line': '#D4D0CA', 'ivory': '#FAFAF7'}
_RENDER_LOCK = threading.RLock()
VIEW_NAMES = {'standard': 'Standard LIC-DSF', 'briefing': 'Policy briefing'}
OFFICIAL_EXAMPLE_SHA = '3a0a0b80c7cbc95ac953f25ecae0b437129d669ceb8aeefb54ab86dc8727ea86'
ILLUSTRATIVE_DISCLOSURE = ('Ghana-labelled sample is purely illustrative; '
                           'it is not an official Ghana forecast or DSA.')
ERRORS = {'#NULL!', '#DIV/0!', '#VALUE!', '#REF!', '#NAME?', '#NUM!', '#N/A',
          '#GETTING_DATA', '#SPILL!', '#CALC!', '#BLOCKED!', '#CONNECT!'}
SCOPE = ('Six supported indicators at sampled workbook years. Historical and tailored stress tests '
         'and public debt service/revenue are not included.')


def _numeric(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _tenths(value):
    """Round half up on the exact binary value, matching JavaScript's toFixed(1) in the app."""
    return str(Decimal(abs(value)).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP))


def _number(value, digits=2, plus=False):
    """Fixed decimals with a typographic minus; an explicit plus only when asked."""
    text = f'{abs(value):.{digits}f}'
    if value < 0 and float(text) != 0: return '\u2212' + text
    if plus and value > 0 and float(text) != 0: return '+' + text
    return text


def _value(value):
    if value is None or _numeric(value) or isinstance(value, str) and value in ERRORS:
        return value
    raise ValueError('A chart value is neither finite, missing, nor a supported error class.')


def _label(value, fallback):
    if value is None or value == '': return fallback
    if not isinstance(value, str) or not 1 <= len(value) <= 40:
        raise ValueError('Use a share label of 1 to 40 characters.')
    if re.search(r'[\x00-\x1f/\\]|https?:|file:|[A-Za-z]:', value):
        raise ValueError('Share labels must not contain paths, links or control characters.')
    return value


def _evidence(result):
    e = result.get('evidence', {})
    if (e.get('saved_cache') == 'mismatch' or e.get('calculation') == 'review_required'
            or e.get('dynamic_reference_check') == 'review_required' or e.get('exact_excel') in ('failed', 'mismatch')):
        return 'Review required'
    if e.get('exact_excel') in ('passed', 'verified'):
        return 'Exact Excel comparison recorded'
    return 'Exact Excel comparison pending'


def _source(metric, role, supplied):
    sheet = 'Output 3-1 Stress-external' if metric.startswith('ext_') else 'Output 3-2 Stress-public'
    if supplied is None: return None
    if not isinstance(supplied, str) or not re.fullmatch(re.escape(sheet) + r'![A-Z]{1,3}[1-9][0-9]*', supplied):
        raise ValueError('Unexpected output source-cell reference.')
    return supplied


def comparison_summary(comparison):
    """Return neutral labels, full-precision rows, source cells and evidence.

    Private names, notes, raw engine records, source paths and internal IDs are
    deliberately not copied. Invalid/missing points are preserved, never zeroed.
    The caller owns source input details and the associated reasoning export.
    """
    runs = comparison.get('runs', [])
    if not 1 <= len(runs) <= 4: raise ValueError('Select one to four saved scenarios.')
    sha = comparison.get('workbook_sha256')
    if not isinstance(sha, str) or not re.fullmatch(r'[0-9a-f]{64}', sha): raise ValueError('Workbook identity required.')
    version = comparison.get('format')
    if 'format' in comparison and version not in ('lic-dsf-comparison-v1', 'lic-dsf-comparison-v2', 'lic-dsf-comparison-v3'):
        raise ValueError('Unsupported comparison format.')
    if version in ('lic-dsf-comparison-v2', 'lic-dsf-comparison-v3') and 'chart_context' not in comparison:
        raise ValueError('Chart context is required for this comparison format.')
    context = validate_chart_context(comparison['chart_context'] if 'chart_context' in comparison else
                                     {'workbook_sha256': sha, 'label': None, 'revision': 0}, sha)
    ids = [r['scenario_id'] for r in runs]
    if len(set(ids)) != len(ids) or comparison.get('comparator_id') not in ids:
        raise ValueError('Select one comparator from the saved scenarios.')
    comparator_index = ids.index(comparison['comparator_id'])
    labels = [_label(r.get('share_label'), f'Scenario {i+1}') for i,r in enumerate(runs)]
    if len(set(labels)) != len(labels) or 'Reference baseline' in labels:
        raise ValueError('Use distinct share labels, separate from Reference baseline.')
    indexes=[];statuses=[];assumptions=[]
    metric_map={m[0]:m for m in METRICS}
    thresholds=None
    for run,label in zip(runs,labels):
        if version == 'lic-dsf-comparison-v3' and 'shared_rationale' not in run:
            raise ValueError('Shared explanations are required for this comparison format.')
        result=run['result']
        if result.get('workbook_sha256')!=sha: raise ValueError('All charts must share one workbook baseline.')
        idx={}
        for p in result.get('points',[]):
            metric=p.get('metric');year=p.get('year')
            if metric not in metric_map or not isinstance(year,int) or isinstance(year,bool) or not 1900<=year<=2200:
                raise ValueError('Unsupported metric or workbook year.')
            if p.get('units')!=metric_map[metric][2]:raise ValueError('Metric units differ from the supported contract.')
            key=(metric,year)
            if key in idx:raise ValueError('Duplicate metric-year point.')
            idx[key]={role:_value(p.get(role)) for role in ('reference_baseline','as_supplied_customized','scenario')}
            cells=p.get('source_cells',{})
            idx[key]['source_cells']={role:_source(metric,role,cells.get(role)) for role in ('reference_baseline','customized')}
        if not idx:raise ValueError('No points to chart.')
        indexes.append(idx);statuses.append(_evidence(result))
        t={m[0]:_value(result.get('thresholds',{}).get(m[0])) for m in METRICS}
        if thresholds is not None and t!=thresholds:raise ValueError('Thresholds differ across saved results.')
        thresholds=t
        definition=result.get('scenario') or {}
        paths=definition.get('delta_paths',{})
        allowed_rows={'11','13','15','17','20','22','24','28','30','32','34','36','38'}
        if (not isinstance(paths,dict) or any(str(k) not in allowed_rows or not isinstance(v,list) or len(v)>21 or any(not _numeric(x) for x in v) for k,v in paths.items())):
            raise ValueError('Saved delta paths must contain finite supported inputs.')
        nonzero=sum(1 for path in paths.values() for v in path if _numeric(v) and v!=0)
        terms=definition.get('terms')
        assumptions.append({'scenario':label,'nonzero_delta_entries':nonzero,
                            'shared_explanations':rationale_entries(definition,run.get('shared_rationale',{})),
                            'delta_paths':{str(k):list(v) for k,v in paths.items()},
                            'financing_terms':{k:v for k,v in (terms or {}).items() if k in ('rate','grace_years','maturity_years') and _numeric(v)} or 'As supplied in workbook'})
    keys=sorted(set.union(*(set(x) for x in indexes)),key=lambda k:([m[0] for m in METRICS].index(k[0]),k[1]))
    rows=[]
    for key in keys:
        # Missing point geometry becomes a gap; conflicting baseline channels are refused.
        available=[idx[key] for idx in indexes if key in idx]
        reference=available[0]['reference_baseline'];supplied=available[0]['as_supplied_customized']
        if any(p['reference_baseline']!=reference or p['as_supplied_customized']!=supplied for p in available):
            raise ValueError('Saved runs have inconsistent reference or as-supplied channels.')
        values=[idx.get(key,{}).get('scenario') for idx in indexes];comp=values[comparator_index]
        rows.append({'metric':key[0],'year':key[1],'units':metric_map[key[0]][2],
                     'reference_baseline':reference,'as_supplied_customized':supplied,
                     'scenarios':dict(zip(labels,values)),
                     'differences':{label:(v-comp if _numeric(v) and _numeric(comp) else None) for label,v in zip(labels,values)},
                     'threshold':thresholds[key[0]],'threshold_source':metric_map[key[0]][3],
                     'source_cells':deepcopy(available[0]['source_cells'])})
    evidence=[{'scenario':label,'status':status} for label,status in zip(labels,statuses)]
    provenance={'kind':'official_illustrative_template' if sha==OFFICIAL_EXAMPLE_SHA else 'user_supplied_workbook',
                'disclosure':ILLUSTRATIVE_DISCLOSURE if sha==OFFICIAL_EXAMPLE_SHA else None}
    return {'labels':labels,'comparator':labels[comparator_index], 'rows':rows,'provenance':provenance,
            'chart_context':context,
            'evidence':evidence,'assumptions':assumptions,'coverage':SCOPE,
            'year_convention':'Workbook year labels; sampled observations only.',
            'interpretation':'Calculated differences are descriptive; they are not causal effects or official risk ratings.'}


def _series(summary,metric):
    rows=[r for r in summary['rows'] if r['metric']==metric]
    return rows,[r['year'] for r in rows]


def _focus(summary, rows):
    # Deterministic audience comparison: first selected non-comparator, latest common
    # numeric observation. Never select the biggest movement or infer an annual peak.
    label=next((s for s in summary['labels'] if s!=summary['comparator']),None)
    if label is None:return None
    for row in reversed(rows):
        diff=row['differences'][label]
        if _numeric(diff):return label,row,diff
    return None


SAMPLED_NOTE='Sampled points; connecting lines are visual guides. Gaps preserve missing/error values.'


def _footnote(summary, metric, full=True):
    meta=next(m for m in METRICS if m[0]==metric)
    rows,_=_series(summary,metric);threshold=rows[0]['threshold'] if rows else None
    source=(f'{"Benchmark" if metric.startswith("public_") else "Threshold"}: {threshold:g}; {meta[3]}.'
            if _numeric(threshold) else 'No threshold available for this indicator.')
    return source+(' '+SAMPLED_NOTE if full else '')


def _title(summary,metric,briefing):
    rows,_=_series(summary,metric);focus=_focus(summary,rows)
    if not briefing or focus is None:return next(m[1] for m in METRICS if m[0]==metric)
    label,row,diff=focus
    if any(e['status']=='Review required' for e in summary['evidence']):return 'This comparison needs numerical review'
    if abs(diff)<0.05:return f'{label} is within 0.1 pp of {summary["comparator"]} in {row["year"]}'
    unit=next(m[2] for m in METRICS if m[0]==metric).replace('percent ','')
    direction='above' if diff>0 else 'below'
    return f'{label} is {_tenths(diff)} pp {unit} {direction} {summary["comparator"]} in {row["year"]}'


def _panel(ax,summary,metric,view,large=False,heading=True):
    import numpy as np
    rows,years=_series(summary,metric);briefing=view=='briefing';meta=next(m for m in METRICS if m[0]==metric)
    size=12 if large else 9
    ax.set_facecolor('white')
    if heading:
        ax.set_title(textwrap.fill(_title(summary,metric,briefing),65 if large else 46),loc='left',fontsize=17 if large else 12,fontweight='bold',pad=25 if briefing else 12,color=COLORS['ink'])
        if briefing:ax.text(0,1.03,textwrap.fill(meta[1],85 if large else 58),transform=ax.transAxes,fontsize=size-1,color=COLORS['gray'])
    ax.set_ylabel(meta[2],fontsize=size,color=COLORS['gray']);ax.set_xlabel('Workbook year',fontsize=size,color=COLORS['gray'])
    if not rows:
        ax.text(.5,.5,'No saved observations',ha='center',transform=ax.transAxes);return
    series=[('Reference baseline',[r['reference_baseline'] for r in rows],COLORS['navy'],'-', 'o')]
    styles=['--','-.',':',(0,(5,1,1,1))];markers=['s','D','^','v'];others=iter(['#8A8A8A','#B0B7BC','#6B7280'])
    focus=_focus(summary,rows);focus_label=focus[0] if focus else None
    for i,label in enumerate(summary['labels']):
        # Colour means the same in both views: focus case cyan, comparator gray, further cases muted.
        color=COLORS['cyan'] if label==focus_label else COLORS['gray'] if label==summary['comparator'] else next(others,'#8A8A8A')
        series.append((label,[r['scenarios'][label] for r in rows],color,styles[i],markers[i]))
    endings=[]
    for label,values,color,style,marker in series:
        values=[v if _numeric(v) else np.nan for v in values]
        ax.plot(years,values,label=label,color=color,linestyle=style,marker=marker,markersize=4 if not large else 6,linewidth=(2.6 if label==focus_label and briefing else 1.4),alpha=1 if briefing else .9)
        if briefing:
            valid=[(year,value) for year,value in zip(years,values) if _numeric(value)]
            if valid:
                end_year,end_value=valid[-1]
                end_label=f'{label}: {_number(end_value)}' if end_year==max(years) else f'{label}: {_number(end_value)} ({end_year})'
                endings.append([end_value,end_label,color,end_year])
    threshold=rows[0]['threshold'];threshold_name='Benchmark' if metric.startswith('public_') else 'Threshold'
    if _numeric(threshold):
        # Drawn within the observed year span so displaced endpoint labels cannot appear
        # to name it, and named on the chart so the reader need not find the footnote.
        ax.plot([min(years),max(years)],[threshold,threshold],color='#444444',ls=(0,(5,4)),lw=1.2)
        # Standard view: label at the right end (no endpoint labels there); briefing view: left end, clear of its endpoint labels.
        ax.text(max(years) if not briefing else min(years),threshold,f'{threshold_name} {threshold:g}',fontsize=size-1,color='#444444',va='bottom',ha='right' if not briefing else 'left',bbox={'facecolor':'white','edgecolor':'none','pad':1})
    nums=[v for _,vs,_,_,_ in series for v in vs if _numeric(v)]+([threshold] if _numeric(threshold) else [])
    lo=min([0]+nums);hi=max([1]+nums);span=hi-lo
    ax.set_ylim(lo-.04*span,hi+(.38 if briefing else .16)*span)
    ax.set_xticks(years);ax.set_xticklabels([str(y) for y in years],fontsize=size-1)
    ax.tick_params(axis='y',labelsize=size-1,colors=COLORS['gray']);ax.grid(axis='y',color='#E5E7EB',linewidth=.65)
    for spine in ('top','right'):ax.spines[spine].set_visible(False)
    for spine in ('left','bottom'):ax.spines[spine].set_color(COLORS['line'])
    width=max(years)-min(years) or 1
    ax.set_xlim(min(years)-width*.03,max(years)+width*(.43 if briefing else .03))
    if briefing:
        # Separate label positions in display space; leaders preserve their data anchors.
        endings.sort(key=lambda e:e[0])
        from matplotlib.font_manager import FontProperties
        label_font=FontProperties(family='DejaVu Sans',size=size-1)
        label_x=max(years)+width*.065
        label_width=ax.get_window_extent().x1-ax.transData.transform((label_x,0))[0]-4
        wrapped=['\n'.join(_header_lines(e[1],ax.figure.canvas.get_renderer(),label_font,label_width)) for e in endings]
        low,high=ax.get_ylim()
        units_per_pixel=(high-low)/ax.get_window_extent().height
        heights=[(text.count('\n')+1)*(size-1)*1.3*ax.figure.dpi/72*units_per_pixel for text in wrapped]
        padding=4*ax.figure.dpi/72*units_per_pixel
        positions=[]
        for i,(value,label,color,end_year) in enumerate(endings):
            floor=low+heights[i]/2+padding if i==0 else positions[-1]+(heights[i-1]+heights[i])/2+padding
            positions.append(max(value,floor))
        shift=max(0,(positions[-1]+heights[-1]/2+padding if positions else low)-high)
        positions=[position-shift for position in positions]
        for (value,label,color,end_year),position,text in zip(endings,positions,wrapped):
            ax.annotate(text,(end_year,value),xytext=(max(years)+width*.065,position),fontsize=size-1,color=COLORS['navy'] if color==COLORS['cyan'] else COLORS['gray'],va='center',bbox={'facecolor':'white','edgecolor':'none','pad':1.5},arrowprops={'arrowstyle':'->','color':color,'lw':1,'shrinkA':3,'shrinkB':3})
        if focus and not any(e['status']=='Review required' for e in summary['evidence']):
            label,row,diff=focus
            from matplotlib.font_manager import FontProperties
            font=FontProperties(family='DejaVu Sans',size=size-1)
            heading_text=f'{label} versus {summary["comparator"]}'
            wrapped=_header_lines(heading_text,ax.figure.canvas.get_renderer(),font,ax.get_window_extent().width*.97)
            annotation=ax.text(.01,.96,'\n'.join(wrapped)+f'\n{row["year"]}: {_number(diff,plus=True)} percentage points',transform=ax.transAxes,va='top',fontproperties=font,parse_math=False,usetex=False,color=COLORS['navy'],bbox={'facecolor':'white','edgecolor':'none','alpha':.85})
            annotation.set_gid('comparison-annotation')
    elif large:
        # A detail page carries its own legend under the axes, clear of the data and the threshold line.
        from matplotlib.font_manager import FontProperties
        font=FontProperties(family='DejaVu Sans',size=size-1)
        handles,labels=ax.get_legend_handles_labels()
        width=ax.get_window_extent().width/max(1,len(handles))-(size-1)*4*ax.figure.dpi/72
        labels=['\n'.join(_header_lines(label,ax.figure.canvas.get_renderer(),font,width)) for label in labels]
        ax.legend(handles,labels,loc='upper left',bbox_to_anchor=(0,-.09),prop=font,frameon=False,ncol=len(handles))
    ax.text(0,-.24 if large else -.20,textwrap.fill(_footnote(summary,metric,full=large),120 if large else 85),transform=ax.transAxes,fontsize=9 if large else 7.7,color=COLORS['gray'],va='top')


def _latest_row(summary, metric):
    rows,_=_series(summary,metric)
    focus=_focus(summary,rows)
    if focus:return focus[1]
    return next((r for r in reversed(rows) if _numeric(r['scenarios'][summary['comparator']])),rows[-1] if rows else None)


def _dot_panel(ax,summary,metric):
    """Latest-observation overview; position conveys levels, text retains differences."""
    meta=next(m for m in METRICS if m[0]==metric);row=_latest_row(summary,metric)
    ax.set_axis_off();ax.set_xlim(0,1);ax.set_ylim(0,1)
    ax.text(0,1.06,textwrap.fill(meta[1],48),fontsize=13,fontweight='bold',color=COLORS['navy'],va='top')
    if row is None:
        ax.text(0,.65,'No saved observations',fontsize=11,color=COLORS['gray']);return
    comp=row['scenarios'][summary['comparator']]
    focus=next((label for label in summary['labels'] if label!=summary['comparator']),None)
    entries=[('Reference baseline',row['reference_baseline'],COLORS['navy'],'o')]
    entries += [(label,row['scenarios'][label],COLORS['cyan'] if label==focus else COLORS['gray'],['s','D','^','v'][i]) for i,label in enumerate(summary['labels'])]
    nums=[v for _,v,_,_ in entries if _numeric(v)]
    low=min(nums) if nums else 0;high=max(nums) if nums else 1
    span=high-low or max(abs(high)*.01,.1);low-=span*.15;high+=span*.15
    def x(value):return .43+.25*(value-low)/(high-low)
    ax.text(0,.84,f'{row["year"]}  |  {meta[2]}',fontsize=10,color=COLORS['gray'])
    ax.text(.82,.72,'Value',fontsize=9,color=COLORS['gray'],ha='right')
    ax.text(.99,.72,'Δ (pp)',fontsize=9,color=COLORS['gray'],ha='right')
    start=.65;step=.56/max(1,len(entries)-1);last=start-step*(len(entries)-1)
    if _numeric(comp):ax.plot([x(comp),x(comp)],[last-.045,start+.045],color='#AAB2B7',linestyle=':',lw=1)
    from matplotlib.font_manager import FontProperties
    label_font=FontProperties(family='DejaVu Sans',size=9.5)
    for i,(label,value,color,marker) in enumerate(entries):
        y=start-i*step
        label_lines=_header_lines(label,ax.figure.canvas.get_renderer(),label_font,ax.get_window_extent().width*.40)
        ax.text(0,y,'\n'.join(label_lines),va='center',fontproperties=label_font,parse_math=False,usetex=False,color=COLORS['navy'] if label in (focus,'Reference baseline') else COLORS['gray'])
        if _numeric(value):
            if _numeric(comp):ax.plot([x(comp),x(value)],[y,y],color=color,lw=2,alpha=.65)
            ax.scatter([x(value)],[y],s=48,color=color,marker=marker,zorder=3)
            number=_number(value)
            difference=value-comp if _numeric(comp) else None
            diff=('0.00' if difference==0 else '≈0.00' if abs(difference)<.005 else _number(difference,plus=True)) if difference is not None else 'Unavailable'
        else:number='Missing' if value is None else value;diff='Unavailable'
        ax.text(.82,y,number,fontsize=10,ha='right',va='center',color=COLORS['ink'])
        ax.text(.99,y,diff,fontsize=10,ha='right',va='center',color=COLORS['navy'] if label==focus else COLORS['gray'])
    threshold=row['threshold'];threshold_name='Benchmark' if metric.startswith('public_') else 'Threshold'
    note=(f'{threshold_name}: {threshold:g}; {row["threshold_source"]}.' if _numeric(threshold) else 'No threshold available.')
    ax.text(0,-.025,note,fontsize=8.5,color=COLORS['gray'])
    ax.text(0,-.10,'Zoomed row comparison; threshold shown as text. See Standard LIC-DSF for full range.',fontsize=8,color=COLORS['gray'],va='top',wrap=True)


def _header_lines(text, renderer, font, width):
    """Wrap literal text to its measured width without truncating characters."""
    lines=[]
    while text:
        if renderer.get_text_width_height_descent(text,font,ismath=False)[0] <= width:
            lines.append(text);break
        end=1
        while end < len(text) and renderer.get_text_width_height_descent(text[:end+1],font,ismath=False)[0] <= width:
            end+=1
        boundary=text.rfind(' ',0,end+1)
        if boundary > 0:end=boundary+1
        lines.append(text[:end]);text=text[end:]
    return lines or ['']


def _header(fig, summary, view, *, detail=False):
    """Draw the same validated source/evidence context on every exported page.

    Positions are measured in inches so the header cannot collide with plots when
    optional text wraps. The returned figure fraction is the content boundary.
    """
    from matplotlib.font_manager import FontProperties
    left=.10 if detail else .075
    renderer=fig.canvas.get_renderer();height=fig.get_figheight()
    cursor=height-.30
    def line(text, size, color, weight='normal', *, context_label=False):
        nonlocal cursor
        font=FontProperties(family='DejaVu Sans',size=size,weight=weight)
        lines=_header_lines(text,renderer,font,(.96-left)*fig.get_figwidth()*fig.dpi)
        artist=fig.text(left,cursor/height,'\n'.join(lines),fontproperties=font,
                        color=color,va='top',parse_math=False,usetex=False,linespacing=1.25)
        if context_label:artist.set_gid('chart-context-label')
        extent=artist.get_window_extent(renderer)
        cursor-=extent.height/fig.dpi+.105
    context=summary['chart_context']
    if context['label'] is not None:
        # The analyst's heading is the page title; the view name becomes a small kicker above it.
        line(VIEW_NAMES[view]+' view',10,COLORS['gray'])
        line(context['label'],15 if detail else 17,COLORS['navy'],'bold',context_label=True)
    else:
        line(VIEW_NAMES[view],18 if detail else 25,COLORS['navy'],'bold')
    line('Workbook SHA-256: '+context['workbook_sha256'][:12]+'…',10,COLORS['gray'])
    line('Selected comparator: '+summary['comparator']+' (a customized scenario) | Reference baseline retained',11,COLORS['gray'])
    status='Review required' if any(e['status']=='Review required' for e in summary['evidence']) else ('Exact Excel comparison pending' if any('pending' in e['status'] for e in summary['evidence']) else 'Exact Excel comparison recorded')
    line(status+' | '+summary['year_convention'],10,COLORS['gray'])
    if summary['provenance']['disclosure']:line(summary['provenance']['disclosure'],10,COLORS['navy'])
    if view=='briefing' and not detail:
        line('Δ: difference versus the selected comparator; ≈0.00 is nonzero but below 0.005 pp. Each panel uses its own zoomed scale; compare the numbers, not lengths across panels.',9,COLORS['gray'])
    return (cursor-(.16 if detail else .32))/height



def _detail_layout(fig, summary, metric, view):
    """Reserve measured header, takeaway and subtitle space before the plot.

    Detail titles live in figure space: their top edge follows the evidence,
    and the axes start only after every wrapped line has been measured.
    """
    from matplotlib.font_manager import FontProperties
    height=fig.get_figheight();cursor=_header(fig,summary,view,detail=True)*height
    renderer=fig.canvas.get_renderer();width=.86*fig.get_figwidth()*fig.dpi
    entries=[(_title(summary,metric,view=='briefing'),17,'bold',COLORS['ink'],'detail-title')]
    if view=='briefing':
        entries.append((next(m[1] for m in METRICS if m[0]==metric),11,'normal',COLORS['gray'],'detail-subtitle'))
    for text,size,weight,color,gid in entries:
        font=FontProperties(family='DejaVu Sans',size=size,weight=weight)
        lines=_header_lines(text,renderer,font,width)
        artist=fig.text(.10,cursor/height,'\n'.join(lines),fontproperties=font,
                        color=color,va='top',parse_math=False,usetex=False,linespacing=1.25)
        artist.set_gid(gid)
        cursor-=artist.get_window_extent(renderer).height/fig.dpi+.12
    top=(cursor-.12)/height
    if top<=.40:raise ValueError('Chart headings leave insufficient room for the plot. Use shorter share labels.')
    return top


def _check_context_glyphs(summary):
    """Refuse an incomplete label rather than emit silent missing-glyph boxes."""
    label=summary['chart_context']['label']
    if label is None:return
    from matplotlib.font_manager import FontProperties, findfont
    from matplotlib.ft2font import FT2Font
    # Match the exact font properties used for the visible context label.
    font=FT2Font(findfont(FontProperties(family='DejaVu Sans',size=12,weight='bold'),fallback_to_default=False))
    if any(font.get_char_index(ord(char))==0 for char in label):
        raise ValueError('The chart label contains characters unavailable in the export font. '
                         'Use a label supported by DejaVu Sans.')


def _check_rationale_glyphs(summary):
    from matplotlib.font_manager import FontProperties, findfont
    from matplotlib.ft2font import FT2Font
    font = FT2Font(findfont(FontProperties(family='DejaVu Sans', size=10), fallback_to_default=False))
    for assumption in summary['assumptions']:
        for entry in assumption['shared_explanations']:
            if any(c != '\n' and font.get_char_index(ord(c)) == 0 for c in entry['text']):
                raise ValueError('A shared explanation contains characters unavailable in the PDF font. '
                                 'Use supported text or download the JSON data export to preserve those characters.')


def _rationale_pages(pdf, summary, plt, view):
    """Measured wrapping and pagination preserve every deliberately shared note."""
    from matplotlib.font_manager import FontProperties
    body_font = FontProperties(family='DejaVu Sans', size=10)
    title_font = FontProperties(family='DejaVu Sans', size=15, weight='bold')
    footer_font = FontProperties(family='DejaVu Sans', size=8)
    for assumption in summary['assumptions']:
        page = None
        cursor = floor = line_height = 0
        def new_page():
            nonlocal page, cursor, floor, line_height
            if page is not None:
                pdf.savefig(page)
                plt.close(page)
            page = plt.figure(figsize=(11.7, 8.3))
            top = _header(page, summary, view, detail=True)
            renderer = page.canvas.get_renderer()
            width = .86 * page.get_figwidth() * page.dpi
            height = page.get_figheight() * page.dpi
            title = 'Shared explanations: ' + assumption['scenario']
            title_lines = _header_lines(title, renderer, title_font, width)
            artist = page.text(.10, top, '\n'.join(title_lines), fontproperties=title_font,
                               color=COLORS['navy'], va='top', parse_math=False, linespacing=1.25)
            cursor = top - artist.get_window_extent(renderer).height / height - .025
            footer = 'Analyst-supplied explanations. Private journals are excluded. ' + SCOPE
            footer_lines = _header_lines(footer, renderer, footer_font, width)
            artist = page.text(.10, .035, '\n'.join(footer_lines), fontproperties=footer_font,
                               color=COLORS['gray'], va='bottom', parse_math=False, linespacing=1.25)
            floor = .035 + artist.get_window_extent(renderer).height / height + .035
            line_height = body_font.get_size_in_points() * 1.5 / 72 / page.get_figheight()
            if cursor - floor < 2 * line_height:
                plt.close(page)
                raise ValueError('Briefing headings leave insufficient room for explanations. Use shorter chart labels.')
            return renderer, width
        renderer, width = new_page()
        label_font = FontProperties(family='DejaVu Sans', size=10, weight='bold')
        paragraphs = []
        for entry in assumption['shared_explanations']:
            paragraphs.append((entry['label'] + (' (adjusted)' if entry['changed'] else ' (no adjustment)'), True))
            paragraphs.extend((line, False) for line in entry['text'].splitlines())
            paragraphs.append(('', False))
        if not paragraphs:
            paragraphs = [('No adjusted drivers or shared explanations in this case.', False)]
        for paragraph, bold in paragraphs:
            font = label_font if bold else body_font
            for line in _header_lines(paragraph, renderer, font, width):
                if cursor - line_height < floor:
                    renderer, width = new_page()
                page.text(.10, cursor, line, fontproperties=font, va='top',
                          color=COLORS['navy'] if bold else COLORS['ink'], parse_math=False)
                cursor -= line_height
        pdf.savefig(page)
        plt.close(page)


def render_comparison(comparison, view='standard', format='png'):
    """Return standalone PNG/PDF bytes. Caller owns destination and retention.

    Both views consume comparison_summary unchanged. PDF includes overview plus six
    larger pages; PNG is the complete overview. All text metadata is fixed/neutral.
    """
    if view not in VIEW_NAMES or format not in ('png','pdf'):raise ValueError('Choose standard/briefing and png/pdf.')
    summary=comparison_summary(comparison)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    result=io.BytesIO()
    with _RENDER_LOCK, matplotlib.rc_context({'font.family':'DejaVu Sans','text.usetex':False,'pdf.fonttype':42,'savefig.facecolor':'white'}):
        _check_context_glyphs(summary)
        if format == 'pdf':
            _check_rationale_glyphs(summary)
        fig,axes=plt.subplots(3,2,figsize=(14,15.5 if view=='briefing' else 13.5))
        top=_header(fig,summary,view)
        fig.subplots_adjust(left=.075,right=.96,top=top,bottom=.17,hspace=.85 if view=='briefing' else .88,wspace=.29)
        if view=='briefing':
            fig.subplots_adjust(left=.075,right=.96,top=top,bottom=.14,hspace=.45,wspace=.20)
            for ax,meta in zip(axes.flat,METRICS):_dot_panel(ax,summary,meta[0])
        else:
            for ax,meta in zip(axes.flat,METRICS):_panel(ax,summary,meta[0],view)
            # One legend for all six panels, measured so it never overlaps the header or the first row.
            from matplotlib.font_manager import FontProperties
            from matplotlib.lines import Line2D
            handles,labels=axes.flat[0].get_legend_handles_labels()
            handles.append(Line2D([],[],color='#444444',ls=(0,(5,4)),lw=1.2));labels.append('Threshold or benchmark (value shown in each panel)')
            legend=fig.legend(handles,labels,loc='upper left',bbox_to_anchor=(.075,top+.01),ncol=min(4,len(handles)),frameon=False,prop=FontProperties(family='DejaVu Sans',size=9),handlelength=2.4,columnspacing=1.6)
            fig.canvas.draw()
            legend_height=legend.get_window_extent(fig.canvas.get_renderer()).height/fig.bbox.height
            fig.subplots_adjust(left=.075,right=.96,top=top-legend_height-.015,bottom=.12,hspace=.75,wspace=.29)
        footer='Source: saved workbook stress tables. '+(SAMPLED_NOTE+' ' if view=='standard' else '')+SCOPE+' '+summary['interpretation']
        fig.text(.075,.038,textwrap.fill(footer,160),fontsize=9,color=COLORS['gray'],va='bottom')
        if format=='png':fig.savefig(result,format='png',dpi=160,metadata={'Software':'LIC-DSF chart renderer','Title':VIEW_NAMES[view]});plt.close(fig)
        else:
            metadata={'Title':VIEW_NAMES[view],'Author':None,'Subject':'Saved scenario comparison','Keywords':None,'Creator':'LIC-DSF chart renderer','Producer':'LIC-DSF chart renderer','CreationDate':None,'ModDate':None}
            with PdfPages(result,metadata=metadata) as pdf:
                pdf.savefig(fig);plt.close(fig)
                for meta in METRICS:
                    one,ax=plt.subplots(figsize=(12,10.5))
                    one.subplots_adjust(left=.10,right=.96,top=_detail_layout(one,summary,meta[0],view),bottom=.25)
                    _panel(ax,summary,meta[0],view,large=True,heading=False)
                    one.text(.10,.025,textwrap.fill('Source: saved workbook stress tables. '+SCOPE+' '+summary['interpretation'],135),fontsize=9,color=COLORS['gray']);pdf.savefig(one);plt.close(one)
                _rationale_pages(pdf, summary, plt, view)
    return result.getvalue()
