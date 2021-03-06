from __future__ import unicode_literals

from django.db.models import TextField, CharField, Value as V
from django.db.models.functions import (
    Coalesce, Concat, Lower, Upper, Length, Substr,
)
from django.test import TestCase
from django.utils import six, timezone

from .models import Author, Article


lorem_ipsum = """
    Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod
    tempor incididunt ut labore et dolore magna aliqua."""


class FunctionTests(TestCase):

    def test_coalesce(self):
        Author.objects.create(name='John Smith', alias='smithj')
        Author.objects.create(name='Rhonda')
        authors = Author.objects.annotate(display_name=Coalesce('alias', 'name'))

        self.assertQuerysetEqual(
            authors.order_by('name'), [
                'smithj',
                'Rhonda',
            ],
            lambda a: a.display_name
        )

        with self.assertRaisesMessage(ValueError, 'Coalesce must take at least two expressions'):
            Author.objects.annotate(display_name=Coalesce('alias'))

    def test_coalesce_mixed_values(self):
        a1 = Author.objects.create(name='John Smith', alias='smithj')
        a2 = Author.objects.create(name='Rhonda')
        ar1 = Article.objects.create(
            title="How to Django",
            text=lorem_ipsum,
            written=timezone.now(),
        )
        ar1.authors.add(a1)
        ar1.authors.add(a2)

        # mixed Text and Char
        article = Article.objects.annotate(
            headline=Coalesce('summary', 'text', output_field=TextField()),
        )

        self.assertQuerysetEqual(
            article.order_by('title'), [
                lorem_ipsum,
            ],
            lambda a: a.headline
        )

    def test_concat(self):
        Author.objects.create(name='Jayden')
        Author.objects.create(name='John Smith', alias='smithj', goes_by='John')
        Author.objects.create(name='Margaret', goes_by='Maggie')
        Author.objects.create(name='Rhonda', alias='adnohR')

        authors = Author.objects.annotate(joined=Concat('alias', 'goes_by'))
        self.assertQuerysetEqual(
            authors.order_by('name'), [
                '',
                'smithjJohn',
                'Maggie',
                'adnohR',
            ],
            lambda a: a.joined
        )

        with self.assertRaisesMessage(ValueError, 'Concat must take at least two expressions'):
            Author.objects.annotate(joined=Concat('alias'))

    def test_concat_many(self):
        Author.objects.create(name='Jayden')
        Author.objects.create(name='John Smith', alias='smithj', goes_by='John')
        Author.objects.create(name='Margaret', goes_by='Maggie')
        Author.objects.create(name='Rhonda', alias='adnohR')

        authors = Author.objects.annotate(
            joined=Concat('name', V(' ('), 'goes_by', V(')'), output_field=CharField()),
        )

        self.assertQuerysetEqual(
            authors.order_by('name'), [
                'Jayden ()',
                'John Smith (John)',
                'Margaret (Maggie)',
                'Rhonda ()',
            ],
            lambda a: a.joined
        )

    def test_concat_mixed_char_text(self):
        Article.objects.create(title='The Title', text=lorem_ipsum, written=timezone.now())
        article = Article.objects.annotate(
            title_text=Concat('title', V(' - '), 'text', output_field=TextField()),
        ).get(title='The Title')
        self.assertEqual(article.title + ' - ' + article.text, article.title_text)

        # wrap the concat in something else to ensure that we're still
        # getting text rather than bytes
        article = Article.objects.annotate(
            title_text=Upper(Concat('title', V(' - '), 'text', output_field=TextField())),
        ).get(title='The Title')
        expected = article.title + ' - ' + article.text
        self.assertEqual(expected.upper(), article.title_text)

    def test_lower(self):
        Author.objects.create(name='John Smith', alias='smithj')
        Author.objects.create(name='Rhonda')
        authors = Author.objects.annotate(lower_name=Lower('name'))

        self.assertQuerysetEqual(
            authors.order_by('name'), [
                'john smith',
                'rhonda',
            ],
            lambda a: a.lower_name
        )

        Author.objects.update(name=Lower('name'))
        self.assertQuerysetEqual(
            authors.order_by('name'), [
                ('john smith', 'john smith'),
                ('rhonda', 'rhonda'),
            ],
            lambda a: (a.lower_name, a.name)
        )

    def test_upper(self):
        Author.objects.create(name='John Smith', alias='smithj')
        Author.objects.create(name='Rhonda')
        authors = Author.objects.annotate(upper_name=Upper('name'))

        self.assertQuerysetEqual(
            authors.order_by('name'), [
                'JOHN SMITH',
                'RHONDA',
            ],
            lambda a: a.upper_name
        )

        Author.objects.update(name=Upper('name'))
        self.assertQuerysetEqual(
            authors.order_by('name'), [
                ('JOHN SMITH', 'JOHN SMITH'),
                ('RHONDA', 'RHONDA'),
            ],
            lambda a: (a.upper_name, a.name)
        )

    def test_length(self):
        Author.objects.create(name='John Smith', alias='smithj')
        Author.objects.create(name='Rhonda')
        authors = Author.objects.annotate(
            name_length=Length('name'),
            alias_length=Length('alias'))

        self.assertQuerysetEqual(
            authors.order_by('name'), [
                (10, 6),
                (6, None),
            ],
            lambda a: (a.name_length, a.alias_length)
        )

        self.assertEqual(authors.filter(alias_length__lte=Length('name')).count(), 1)

    def test_substr(self):
        Author.objects.create(name='John Smith', alias='smithj')
        Author.objects.create(name='Rhonda')
        authors = Author.objects.annotate(name_part=Substr('name', 5, 3))

        self.assertQuerysetEqual(
            authors.order_by('name'), [
                ' Sm',
                'da',
            ],
            lambda a: a.name_part
        )

        authors = Author.objects.annotate(name_part=Substr('name', 2))
        self.assertQuerysetEqual(
            authors.order_by('name'), [
                'ohn Smith',
                'honda',
            ],
            lambda a: a.name_part
        )

        # if alias is null, set to first 5 lower characters of the name
        Author.objects.filter(alias__isnull=True).update(
            alias=Lower(Substr('name', 1, 5)),
        )

        self.assertQuerysetEqual(
            authors.order_by('name'), [
                'smithj',
                'rhond',
            ],
            lambda a: a.alias
        )

    def test_substr_start(self):
        Author.objects.create(name='John Smith', alias='smithj')
        a = Author.objects.annotate(
            name_part_1=Substr('name', 1),
            name_part_2=Substr('name', 2),
        ).get(alias='smithj')

        self.assertEqual(a.name_part_1[1:], a.name_part_2)

        with six.assertRaisesRegex(self, ValueError, "'pos' must be greater than 0"):
            Author.objects.annotate(raises=Substr('name', 0))
