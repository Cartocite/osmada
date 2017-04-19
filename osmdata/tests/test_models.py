from django.test import TestCase

from ..models import Diff, Node, OSMElement, Relation, Tag, Way

class TestTag(TestCase):
    def setUp(self):
        self.element = OSMElement.objects.create()

    def test_osmtag_match(self):
        tag = Tag.objects.create(element=self.element, k='foo', v='bar')

        self.assertTrue(tag.match('foo=bar'))
        self.assertTrue(tag.match('foo=*'))

        self.assertFalse(tag.match('foo=zoom'))
        self.assertFalse(tag.match('zoom=bar'))

    def test_parse_tag_pattern(self):
        self.assertEqual(Tag.parse_tag_pattern('a=*'), {"k": "a"})
        self.assertEqual(Tag.parse_tag_pattern('a=b'), {"k": "a", "v": "b"})

        # empty
        with self.assertRaises(ValueError):
            Tag.parse_tag_pattern('')

        # wrong format
        with self.assertRaises(ValueError):
            Tag.parse_tag_pattern('trucmuche')


class TestOSMElement(TestCase):
    def setUp(self):
        self.element = OSMElement.objects.create()

    def test_tags_dict(self):
        self.assertEqual(self.element.tags_dict(), {})

        Tag.objects.create(element=self.element, k='foo', v='bar')
        self.assertEqual(self.element.tags_dict(), {'foo': 'bar'})

    def test_specialized(self):
        way = Way.objects.create(osmid="1234")

        self.assertEqual(way, OSMElement.objects.get(osmid=way.osmid).specialized())

    def test_non_specialized(self):
        # non specialized objects should not exist
        non_specialized = OSMElement.objects.create(osmid=567)

        with self.assertRaises(ValueError):
            non_specialized.specialized()

    def test_osmelement_as_str(self):
        way = Way.objects.create(osmid="1234")
        self.assertEqual(str(way), '<Way id="1234">')


class DiffTest(TestCase):
    def test_str(self):
        diff = Diff.objects.create()
        self.assertEqual(str(diff), 'Diff #1')
