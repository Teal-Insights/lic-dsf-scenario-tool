"""Wrapping parity and bounded packet-local cache; real bundled Agg fonts."""
import unittest
from unittest.mock import patch
import matplotlib
matplotlib.use('Agg')
from matplotlib.backends.backend_agg import RendererAgg
from lic_dsf.charts import _header_lines, _PACKET_WRAP_CACHE
from lic_dsf.typography import font_properties
from lic_dsf import briefing_pack


def original_wrap(text, renderer, font, width):
    lines=[]
    while text:
        if renderer.get_text_width_height_descent(text,font,ismath=False)[0] <= width:
            lines.append(text);break
        end=1
        while end<len(text) and renderer.get_text_width_height_descent(text[:end+1],font,ismath=False)[0]<=width:
            end+=1
        boundary=text.rfind(' ',0,end+1)
        if boundary>0:end=boundary+1
        lines.append(text[:end]);text=text[end:]
    return lines or ['']


class WrapOptimizationTests(unittest.TestCase):
    def setUp(self):
        self.renderer=RendererAgg(1200,880,100)

    def test_ascii_pair_advances_in_bundled_fonts(self):
        chars=[chr(c) for c in range(32,127)]
        for family,weight in [('Inter','normal'),('Inter','bold'),('IBM Plex Serif','bold')]:
            font=font_properties(family=family,weight=weight,size=10)
            singles={c:self.renderer.get_text_width_height_descent(c,font,ismath=False)[0] for c in chars}
            for first in chars:
                for second in chars:
                    pair=self.renderer.get_text_width_height_descent(first+second,font,ismath=False)[0]
                    self.assertGreaterEqual(pair,singles[first],(family,weight,first+second))

    def test_ascii_kerning_spaces_long_words_exact_original(self):
        texts=['','x','AVATAR To WA fi ffi',' leading  double   spaces trailing ',
               'supercalifragilisticexpialidocious'*3,'GDP growth 0.05% in 2030-2044',
               'W'*130,'i'*130,'spaces     '*12]
        for family,weight in [('Inter','normal'),('Inter','bold'),('IBM Plex Serif','bold')]:
            for size in (7.7,10,21):
                font=font_properties(family=family,weight=weight,size=size)
                for text in texts:
                    for width in (0,.1,10,30,75,150,600):
                        self.assertEqual(_header_lines(text,self.renderer,font,width),original_wrap(text,self.renderer,font,width))

    def test_unicode_negative_advance_counterexample_keeps_original(self):
        # Actual bundled-font negative prefix advance: unrestricted binary changes wrapping.
        text='\u2014,\u032e\u0304T\u030c\u0302\u0315i\u0312\u0331\u2014\u0326\u0309\u03153 \u030c\u0315iV3\u030ci\u0327'
        font=font_properties(family='IBM Plex Serif',weight='bold',size=10)
        before=self.renderer.get_text_width_height_descent(text[:9],font,ismath=False)[0]
        after=self.renderer.get_text_width_height_descent(text[:10],font,ismath=False)[0]
        self.assertLess(after,before)
        for width in (after-.001,after,after+.001,before):
            self.assertEqual(_header_lines(text,self.renderer,font,width),original_wrap(text,self.renderer,font,width))
        for value in ('e\u0301 a\u0308 n\u0303','\u0301\u0308abc','x\t y\n z','Café naïve São Tomé'):
            for width in (0,20,45,100):
                self.assertEqual(_header_lines(value,self.renderer,font,width),original_wrap(value,self.renderer,font,width))

    def test_cache_copies_bounds_and_font_dpi_keys(self):
        cache={};token=_PACKET_WRAP_CACHE.set(cache)
        try:
            font=font_properties(size=10)
            with patch.object(self.renderer,'get_text_width_height_descent',wraps=self.renderer.get_text_width_height_descent) as measure:
                first=_header_lines('Private synthetic heading',self.renderer,font,80);count=measure.call_count
                first[0]='changed caller list'
                again=_header_lines('Private synthetic heading',self.renderer,font,80)
                self.assertNotEqual(again[0],'changed caller list');self.assertEqual(measure.call_count,count)
                changed=font.copy();changed.set_size(11)
                _header_lines('Private synthetic heading',self.renderer,changed,80)
                self.assertGreater(measure.call_count,count)
            _header_lines('Private synthetic heading',RendererAgg(1200,880,200),font,80)
            self.assertEqual(len(cache),3)
            _header_lines('x'*4097,self.renderer,font,100000)
            self.assertEqual(len(cache),3)
            for i in range(270):_header_lines('Bounded label '+str(i),self.renderer,font,1000)
            self.assertEqual(len(cache),256)
        finally:_PACKET_WRAP_CACHE.reset(token)

    def test_packet_scope_resets_on_success_failure_and_nested_context(self):
        seen=[]
        def render(comparison):
            current=_PACKET_WRAP_CACHE.get();self.assertEqual(current,{})
            current['sentinel']=comparison;seen.append(current);return b'packet'
        self.assertIsNone(_PACKET_WRAP_CACHE.get())
        with patch.object(briefing_pack,'_render_pack',side_effect=render):
            self.assertEqual(briefing_pack.render_pack('visitor A'),b'packet')
            self.assertEqual(briefing_pack.render_pack('visitor B'),b'packet')
        self.assertIsNot(seen[0],seen[1]);self.assertIsNone(_PACKET_WRAP_CACHE.get())
        outer={'outer':True};token=_PACKET_WRAP_CACHE.set(outer)
        try:
            with patch.object(briefing_pack,'_render_pack',side_effect=ValueError('synthetic rendering failure')):
                with self.assertRaises(ValueError):briefing_pack.render_pack('failure')
            self.assertIs(_PACKET_WRAP_CACHE.get(),outer)
        finally:_PACKET_WRAP_CACHE.reset(token)

if __name__=='__main__':unittest.main()
