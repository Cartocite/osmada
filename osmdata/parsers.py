import datetime
import xml.dom.minidom

import pytz

from .models import (
    Action, Bounds, Diff, Node, OSMElement, Relation,
    RelationMember, Tag, Way, WayNode)


class FileFormatError(Exception):
    pass

zulu_tz = pytz.timezone('Zulu')
def parse_iso8601(s):
    return zulu_tz.localize(datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ" ))

def getFirstNontextChild(element):
    """ Return the first non-text child

    :param element: the parent element to search in
    :type element: xml.dom.minidom.Element
    :rtype: xml.dom.minidom.Element
    :return: The first child element which is not a text node
    """
    for i in element.childNodes:
        if not isinstance(i, xml.dom.minidom.Text):
            return i


class AbstractXMLParser:
    """ Base class for Adiff XML node parsers
    """
    # See at the end of the file for definition of :
    # PARSER_MAP = {...}

    def __init__(self, node):
        self.node = node


    @staticmethod
    def _dict_fetch(_dict, str_name):
        """ Given a str name, returns the matching parser
        """
        try:
            klass = _dict[str_name]
        except KeyError:
            raise FileFormatError(
                'Unknown member type : "{}"'.format(str_name))
        return klass

    @classmethod
    def get_parser(cls, str_name):
        """ Given a str name, returns the matching model
        """
        return cls._dict_fetch(cls.PARSER_MAP, str_name)

    def transform(self, node, name=None):
        """"Given a node/way/relation, creates a Django object in db

        :return: the db object.
        """
        klass = self.get_parser(node.localName)
        return klass(node).parse()

    def parse(self):
        """ Parse the XML node and retuns a model instance

        Can recurse, on sub-nodes calling other parsers, only the top-level
        node(s) is/are returned.

        :rtype: a OSMElement or a list of OSMElement
        """
        raise NotImplemented  # pragma: no cover


class RelationMemberParser(AbstractXMLParser):
    """ <member> parser
    """
    def __init__(self, node, relation, order):
        self.node = node
        self.relation = relation
        self.order = order

    def parse(self):
        _type = self.node.attributes['type'].value

        ParserClass = self.get_parser(_type)
        parser = ParserClass(self.node)
        element = parser.parse()

        return RelationMember.objects.create(
            relation=self.relation,
            element=element,
            order=self.order,
            role=self.node.attributes['role'].value)


class BoundsParser(AbstractXMLParser):
    BOUNDS_ATTRS = ('minlat', 'minlon', 'maxlat', 'maxlon')

    def parse(self):
        attrs = {k:self.node.attributes[k].value for k in self.BOUNDS_ATTRS}
        return Bounds.objects.create(**attrs)


class AbstractOSMElementParser(AbstractXMLParser):
    """ Base class for XML nodes representing OSM elements

    Possible elements are way, node or relation
    """
    def parse_tags(self, element):
        """ Parse the elements tags (if any)

        - parse elements
        - create the tags in db and links them to the element in db.

        :param element: the element the tags refer to.
        :type element: OSMElement
        :return the created tags
        :rtype list of Tag:
        """
        tags = []
        for tag_el in self.node.getElementsByTagName('tag'):
            tags.append(Tag.objects.create(
                element=element,
                k=tag_el.attributes['k'].value,
                v=tag_el.attributes['v'].value,
            ))
        return tags

    def parse_bounds(self):
        """ Parse the <bounds> (if any)
        """
        # No more than 1 bounds
        try:
            bounds_tag = self.node.getElementsByTagName('bounds')[0]
        except IndexError:
            pass  # optional
        else:
            parser = BoundsParser(bounds_tag)
            return parser.parse()

    def get_basic_attributes(self):
        """ Return shared attributes for all OSM data types

        Can handle both plain version of objects (with an "id" attribute) and
        nested versions (with a "ref" attribute).

        :rtype: dict
        """
        osmid_key = None
        for key in ('id', 'ref'):
            if key in self.node.attributes:
                osmid_key = key
                break

        attrs = {}
        if osmid_key is not None:
            attrs['osmid'] = self.node.attributes[osmid_key].value

        # Handle optional attrs
        for i in ('version', 'uid', 'user', 'changeset', 'visible'):
            if i in self.node.attributes:
                attrs[i] = self.node.attributes[i].value
                if i == 'visible': # boolean
                    attrs[i] = True if (attrs[i] == 'true') else False

        if 'timestamp' in self.node.attributes:
            attrs['timestamp'] = parse_iso8601(self.node.attributes['timestamp'].value)

        return attrs

class RelationParser(AbstractOSMElementParser):
    """ <relation> parser
    """

    def parse(self):
        relation =  Relation.objects.create(
            bounds=self.parse_bounds(),
            **self.get_basic_attributes())

        for index, node in enumerate(self.node.getElementsByTagName('member')):
            member_parser = RelationMemberParser(node, relation, index)
            member_parser.parse()
        self.parse_tags(relation)
        return relation


class NodeParser(AbstractOSMElementParser):
    """ <node>, <nd> or <member type="node"> parser
    """

    def parse(self):
        lat = self.node.getAttribute('lat') or None
        lon = self.node.getAttribute('lon') or None

        node = Node.objects.create(
            lat=lat,
            lon=lon,
            **self.get_basic_attributes())
        self.parse_tags(node)
        return node

class WayParser(AbstractOSMElementParser):
    """ <way> or <member type="relation"> parser
    """

    def parse(self):
        way = Way.objects.create(
            bounds=self.parse_bounds(),
            **self.get_basic_attributes())

        for index, nd in enumerate(self.node.getElementsByTagName('nd')):

            parser = NodeParser(nd)
            node = parser.parse()
            WayNode.objects.create(way=way, node=node, order=index)
        self.parse_tags(way)
        return way


# Here to avoid cyclic dependecies
AbstractXMLParser.PARSER_MAP = {
    OSMElement.NODE: NodeParser,
    OSMElement.WAY: WayParser,
    OSMElement.RELATION: RelationParser,
}


class ActionParser(AbstractXMLParser):
    """ <action> parser
    """
    def _get_old_new(self):
        for i in ('old', 'new'):
            try:
                tag = self.node.getElementsByTagName(i)[0]
            except IndexError:
                raise FileFormatError('There must be a {} tag'.format(i))
            yield getFirstNontextChild(tag)

    def parse(self):
        new, old = None, None

        action_type = self.node.attributes['type'].value

        if action_type == Action.CREATE:
            new = self.transform(getFirstNontextChild(self.node))

        elif action_type in (Action.MODIFY, Action.DELETE):
            old_tag, new_tag = self._get_old_new()
            if old_tag:
                old = self.transform(old_tag)

            if new_tag:
                new = self.transform(new_tag)
                # removal from a relation, adiff mark them as "delete" also. Only
                # difference in adiff, is that the <new> osm element has visible=true for a
                # remove and visible=false for a delete.
                if action_type == Action.DELETE and new.visible:
                    action_type = Action.REMOVE
        else:
            raise FileFormatError("{} is an unknown action type".format(
                action_type))

        return Action.objects.create(
            new=new, old=old, type=action_type)


class AdiffParser(AbstractXMLParser):
    def parse(self):
        if self.node.tagName != 'osm':
            raise FileFormatError('That does not look like an adiff file…')

        diff = Diff.objects.create()

        actions = []
        for action in self.node.getElementsByTagName("action"):
            action_parser = ActionParser(action)
            actions.append(action_parser.parse())

        diff.actions.set(actions)
        return diff
