from django.test import TestCase

from ..models import Tag, OSMElement

class TestTag(TestCase):
    def setUp(self):
        self.element = OSMElement.objects.create()

    def test_osmtag_match(self):
        tag = Tag.objects.create(element=self.element, k='foo', v='bar')

        self.assertTrue(tag.match('foo=bar'))
        self.assertTrue(tag.match('foo=*'))

        self.assertFalse(tag.match('foo=zoom'))
        self.assertFalse(tag.match('zoom=bar'))


class TestOSMElement(TestCase):
    def setUp(self):
        self.element = OSMElement.objects.create()

    def test_tags_dict(self):
        self.assertEqual(self.element.tags_dict(), {})

        Tag.objects.create(element=self.element, k='foo', v='bar')
        self.assertEqual(self.element.tags_dict(), {'foo': 'bar'})
