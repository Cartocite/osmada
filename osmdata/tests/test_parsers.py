import datetime

from django.test import TestCase

from ..parsers import (
    AbstractXMLParser, ActionParser, AdiffParser, BoundsParser,
    FileFormatError, RelationParser, NodeParser, WayParser, zulu_tz)
from ..models import (
    Action, Bounds, Diff, Node, Relation, RelationMember, Way, WayNode)
from .utils import minidom_parse_fragment, parse_test_data


class AdiffParserTest(TestCase):
    def test_adiff_parser(self):
        test_data = parse_test_data('create_action.osm')
        adiff_node = test_data.getElementsByTagName('osm')[0]

        parser = AdiffParser(adiff_node)
        diff = parser.parse()
        self.assertIsInstance(diff, Diff)
        self.assertEqual(diff.actions.count(), 1)

    def test_invalid_root_tag_parser(self):
        with self.assertRaises(FileFormatError):
            test_data = minidom_parse_fragment('<h1>lol</h1>')
            AdiffParser(test_data).parse()

class AbstractXMLParserTest(TestCase):
    def test_get_existing_model(self):
        self.assertEqual(AbstractXMLParser.get_parser('node'), NodeParser)

    def test_get_nonexisting_model(self):
        with self.assertRaises(FileFormatError):
            AbstractXMLParser.get_parser('freakynode')


class OSMElementsParserTest(TestCase):
    def test_bounds_parser(self):
        element = minidom_parse_fragment(
            '<bounds minlat="48.9683122" minlon="2.1936305" maxlat="48.9684299" maxlon="2.1937721"/>')

        bounds_parser = BoundsParser(element)
        bounds = bounds_parser.parse()
        # FIXME: this refresh may not be necessary if the parser does input typing
        bounds.refresh_from_db()
        self.assertIsInstance(bounds, Bounds)
        self.assertEqual(
            [bounds.minlat, bounds.minlon, bounds.maxlat, bounds.maxlon],
            [48.9683122, 2.1936305, 48.9684299, 2.1937721])

    def test_osmelement_parser(self):
        # Done here with nodes as example, but this part is generic osm element parsing
        element = minidom_parse_fragment("""
          <node id="3497428295" lat="48.7954702" lon="2.1355157" version="6" timestamp="2016-09-10T14:41:56Z" changeset="42060502" uid="4540825" user="Eunjeung Yu"></node>""")
        node_parser = NodeParser(element)
        node = node_parser.parse()
        # FIXME: this refresh may not be necessary if the parser does input typing
        node.refresh_from_db()
        self.assertIsInstance(node, Node)
        self.assertEqual(
            [node.osmid, node.lat, node.lon, node.version, node.timestamp,
             node.changeset, node.uid, node.user],
            [3497428295, 48.7954702, 2.1355157, 6,
             datetime.datetime(2016, 9, 10, 14, 41, 56, tzinfo=zulu_tz),
             42060502, 4540825, "Eunjeung Yu"])

    def test_node_parser_tags(self):
        element = minidom_parse_fragment("""
          <node id="3497428295" lat="48.7954702" lon="2.1355157" version="6" timestamp="2016-09-10T14:41:56Z" changeset="42060502" uid="4540825" user="Eunjeung Yu">
            <tag k="name" v="Versailles Chantiers"/>
          </node>
        """)
        node_parser = NodeParser(element)
        node = node_parser.parse()

        self.assertEqual(node.tags.count(), 1)
        self.assertEqual([node.tags.all()[0].k, node.tags.all()[0].v],
                         ["name", "Versailles Chantiers"])

    def test_way_parser(self):
        element = minidom_parse_fragment("""
          <way id="444967525" version="1" timestamp="2016-09-29T20:39:04Z" changeset="42528786" uid="677099" user="Yann_L">
            <bounds minlat="48.8874273" minlon="2.3140091" maxlat="48.8874563" maxlon="2.3140648"/>
            <nd ref="4424244203" lat="48.8874563" lon="2.3140540"/>
            <nd ref="4424244201" lat="48.8874414" lon="2.3140648"/>
          </way>
        """)
        way_parser = WayParser(element)
        way = way_parser.parse()
        self.assertIsInstance(way, Way)
        self.assertIsInstance(way.bounds, Bounds)
        self.assertIsInstance(way.nodes.first(), Node)
        self.assertEqual(WayNode.objects.filter(way=way).count(), 2)
        first_wn, second_wn = WayNode.objects.all()

        self.assertEqual([first_wn.node.osmid, first_wn.order], [4424244203, 0])
        self.assertEqual([second_wn.node.osmid, second_wn.order], [4424244201, 1])

    def test_way__parser_missing_bounds(self):
        # bounds are considered optional
        element = minidom_parse_fragment("""
          <way id="444967525" version="1" timestamp="2016-09-29T20:39:04Z" changeset="42528786" uid="677099" user="Yann_L">
            <nd ref="4424244203" lat="48.8874563" lon="2.3140540"/>
            <nd ref="4424244201" lat="48.8874414" lon="2.3140648"/>
          </way>
        """)
        way_parser = WayParser(element)
        way = way_parser.parse()



class RelationParserTest(TestCase):
    def test_relation_simple_members_parser(self):
        element = minidom_parse_fragment("""
          <relation id="3995957" version="6" timestamp="2016-04-18T11:22:55Z" changeset="38664682" uid="15908" user="cantece">
            <bounds minlat="48.3939579" minlon="2.7619426" maxlat="48.3946877" maxlon="2.7667246"/>
            <member type="node" ref="3571536293" role="" lat="48.3943179" lon="2.7640013"/>
          </relation>
        """)
        relation_parser = RelationParser(element)
        relation = relation_parser.parse()
        self.assertIsInstance(relation, Relation)
        self.assertEqual(relation.members.count(), 1)

        first_member = relation.members.first()
        self.assertIsInstance(first_member, RelationMember)
        self.assertEqual(first_member.role, '')
        self.assertEqual(first_member.element.osmid, Node.objects.first().osmid)


class ActionParserTest(TestCase):
    def test_create_action_parser(self):
        test_data = parse_test_data('create_action.osm')
        action_node = test_data.getElementsByTagName('action')[0]

        parser = ActionParser(action_node)
        action = parser.parse()

        self.assertIsInstance(action, Action)
        self.assertEqual(action.type, Action.CREATE)
        self.assertIsInstance(action.new, Way)
        self.assertIsNone(action.old)

    def test_modify_action_parser(self):
        test_data = parse_test_data('modify_action.osm')
        action_node = test_data.getElementsByTagName('action')[0]

        parser = ActionParser(action_node)
        action = parser.parse()

        self.assertIsInstance(action, Action)
        self.assertEqual(action.type, Action.MODIFY)
        self.assertIsInstance(action.new, Node)

        self.assertEqual(action.type, Action.MODIFY)
        self.assertIsInstance(action.new, Node)
        self.assertIsInstance(action.old, Node)

    def test_modify_action_parser_missing_oldnew(self):
        test_data = parse_test_data('modify_action.osm')
        action_node = test_data.getElementsByTagName('action')[0]
        action_node.removeChild(action_node.getElementsByTagName('new')[0])

        with self.assertRaises(FileFormatError):
            ActionParser(action_node).parse()

        test_data = parse_test_data('modify_action.osm')
        action_node = test_data.getElementsByTagName('action')[0]
        action_node.removeChild(action_node.getElementsByTagName('old')[0])

        with self.assertRaises(FileFormatError):
            ActionParser(action_node).parse()


    def test_delete_action_parser(self):
        test_data = parse_test_data('delete_action.osm')
        action_node = test_data.getElementsByTagName('action')[0]

        parser = ActionParser(action_node)
        action = parser.parse()
        self.assertIsInstance(action, Action)
        self.assertEqual(action.type, Action.DELETE)
        self.assertIsInstance(action.new, Node)
        self.assertIsInstance(action.old, Node)

    def test_invalid_action_parser(self):
        test_data = parse_test_data('invalid_action.osm')
        action_node = test_data.getElementsByTagName('action')[0]

        with self.assertRaises(FileFormatError):
            ActionParser(action_node).parse()
