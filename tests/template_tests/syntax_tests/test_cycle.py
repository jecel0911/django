import warnings

from django.template import TemplateSyntaxError
from django.test import SimpleTestCase
from django.utils.deprecation import RemovedInDjango20Warning

from ..utils import setup


class CycleTagTests(SimpleTestCase):

    @setup({'cycle01': '{% cycle a %}'})
    def test_cycle01(self):
        with self.assertRaises(TemplateSyntaxError):
            self.engine.get_template('cycle01')

    @setup({'cycle02': '{% cycle a,b,c as abc %}{% cycle abc %}'})
    def test_cycle02(self):
        output = self.engine.render_to_string('cycle02')
        self.assertEqual(output, 'ab')

    @setup({'cycle03': '{% cycle a,b,c as abc %}{% cycle abc %}{% cycle abc %}'})
    def test_cycle03(self):
        output = self.engine.render_to_string('cycle03')
        self.assertEqual(output, 'abc')

    @setup({'cycle04': '{% cycle a,b,c as abc %}{% cycle abc %}{% cycle abc %}{% cycle abc %}'})
    def test_cycle04(self):
        output = self.engine.render_to_string('cycle04')
        self.assertEqual(output, 'abca')

    @setup({'cycle05': '{% cycle %}'})
    def test_cycle05(self):
        with self.assertRaises(TemplateSyntaxError):
            self.engine.get_template('cycle05')

    @setup({'cycle06': '{% cycle a %}'})
    def test_cycle06(self):
        with self.assertRaises(TemplateSyntaxError):
            self.engine.get_template('cycle06')

    @setup({'cycle07': '{% cycle a,b,c as foo %}{% cycle bar %}'})
    def test_cycle07(self):
        with self.assertRaises(TemplateSyntaxError):
            self.engine.get_template('cycle07')

    @setup({'cycle08': '{% cycle a,b,c as foo %}{% cycle foo %}{{ foo }}{{ foo }}{% cycle foo %}{{ foo }}'})
    def test_cycle08(self):
        output = self.engine.render_to_string('cycle08')
        self.assertEqual(output, 'abbbcc')

    @setup({'cycle09': '{% for i in test %}{% cycle a,b %}{{ i }},{% endfor %}'})
    def test_cycle09(self):
        output = self.engine.render_to_string('cycle09', {'test': list(range(5))})
        self.assertEqual(output, 'a0,b1,a2,b3,a4,')

    @setup({'cycle10': "{% cycle 'a' 'b' 'c' as abc %}{% cycle abc %}"})
    def test_cycle10(self):
        output = self.engine.render_to_string('cycle10')
        self.assertEqual(output, 'ab')

    @setup({'cycle11': "{% cycle 'a' 'b' 'c' as abc %}{% cycle abc %}{% cycle abc %}"})
    def test_cycle11(self):
        output = self.engine.render_to_string('cycle11')
        self.assertEqual(output, 'abc')

    @setup({'cycle12': "{% cycle 'a' 'b' 'c' as abc %}{% cycle abc %}{% cycle abc %}{% cycle abc %}"})
    def test_cycle12(self):
        output = self.engine.render_to_string('cycle12')
        self.assertEqual(output, 'abca')

    @setup({'cycle13': "{% for i in test %}{% cycle 'a' 'b' %}{{ i }},{% endfor %}"})
    def test_cycle13(self):
        output = self.engine.render_to_string('cycle13', {'test': list(range(5))})
        self.assertEqual(output, 'a0,b1,a2,b3,a4,')

    @setup({'cycle14': '{% cycle one two as foo %}{% cycle foo %}'})
    def test_cycle14(self):
        output = self.engine.render_to_string('cycle14', {'one': '1', 'two': '2'})
        self.assertEqual(output, '12')

    @setup({'cycle15': '{% for i in test %}{% cycle aye bee %}{{ i }},{% endfor %}'})
    def test_cycle15(self):
        output = self.engine.render_to_string('cycle15', {'test': list(range(5)), 'aye': 'a', 'bee': 'b'})
        self.assertEqual(output, 'a0,b1,a2,b3,a4,')

    @setup({'cycle16': '{% cycle one|lower two as foo %}{% cycle foo %}'})
    def test_cycle16(self):
        output = self.engine.render_to_string('cycle16', {'one': 'A', 'two': '2'})
        self.assertEqual(output, 'a2')

    @setup({'cycle17': "{% cycle 'a' 'b' 'c' as abc silent %}"
                       "{% cycle abc %}{% cycle abc %}{% cycle abc %}{% cycle abc %}"})
    def test_cycle17(self):
        output = self.engine.render_to_string('cycle17')
        self.assertEqual(output, '')

    @setup({'cycle18': "{% cycle 'a' 'b' 'c' as foo invalid_flag %}"})
    def test_cycle18(self):
        with self.assertRaises(TemplateSyntaxError):
            self.engine.get_template('cycle18')

    @setup({'cycle19': "{% cycle 'a' 'b' as silent %}{% cycle silent %}"})
    def test_cycle19(self):
        output = self.engine.render_to_string('cycle19')
        self.assertEqual(output, 'ab')

    @setup({'cycle20': '{% cycle one two as foo %} &amp; {% cycle foo %}'})
    def test_cycle20(self):
        output = self.engine.render_to_string('cycle20', {'two': 'C & D', 'one': 'A & B'})
        self.assertEqual(output, 'A &amp; B &amp; C &amp; D')

    @setup({'cycle21': '{% filter force_escape %}'
                       '{% cycle one two as foo %} & {% cycle foo %}{% endfilter %}'})
    def test_cycle21(self):
        output = self.engine.render_to_string('cycle21', {'two': 'C & D', 'one': 'A & B'})
        self.assertEqual(output, 'A &amp;amp; B &amp; C &amp;amp; D')

    @setup({'cycle22': "{% for x in values %}{% cycle 'a' 'b' 'c' as abc silent %}{{ x }}{% endfor %}"})
    def test_cycle22(self):
        output = self.engine.render_to_string('cycle22', {'values': [1, 2, 3, 4]})
        self.assertEqual(output, '1234')

    @setup({'cycle23': "{% for x in values %}"
                       "{% cycle 'a' 'b' 'c' as abc silent %}{{ abc }}{{ x }}{% endfor %}"})
    def test_cycle23(self):
        output = self.engine.render_to_string('cycle23', {'values': [1, 2, 3, 4]})
        self.assertEqual(output, 'a1b2c3a4')

    @setup({
        'cycle24': "{% for x in values %}"
                   "{% cycle 'a' 'b' 'c' as abc silent %}{% include 'included-cycle' %}{% endfor %}",
        'included-cycle': '{{ abc }}',
    })
    def test_cycle24(self):
        output = self.engine.render_to_string('cycle24', {'values': [1, 2, 3, 4]})
        self.assertEqual(output, 'abca')

    @setup({'cycle25': '{% cycle a as abc %}'})
    def test_cycle25(self):
        output = self.engine.render_to_string('cycle25', {'a': '<'})
        self.assertEqual(output, '&lt;')

    @setup({'cycle26': '{% load cycle from future %}{% cycle a b as ab %}{% cycle ab %}'})
    def test_cycle26(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RemovedInDjango20Warning)
            output = self.engine.render_to_string('cycle26', {'a': '<', 'b': '>'})
        self.assertEqual(output, '&lt;&gt;')

    @setup({'cycle27': '{% load cycle from future %}'
                       '{% autoescape off %}{% cycle a b as ab %}{% cycle ab %}{% endautoescape %}'})
    def test_cycle27(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RemovedInDjango20Warning)
            output = self.engine.render_to_string('cycle27', {'a': '<', 'b': '>'})
        self.assertEqual(output, '<>')

    @setup({'cycle28': '{% load cycle from future %}{% cycle a|safe b as ab %}{% cycle ab %}'})
    def test_cycle28(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RemovedInDjango20Warning)
            output = self.engine.render_to_string('cycle28', {'a': '<', 'b': '>'})
        self.assertEqual(output, '<&gt;')
