import xml.dom.minidom


from .models import (
    Action, Diff, Node, Relation, RelationMember, Tag, Way, WayNode)


class FileFormatError(Exception):
    pass

def getFirstNontextChild(element):
    for i in element.childNodes:
        if not isinstance(i, xml.dom.minidom.Text):
            return i

class AbstractXMLParser:
    ELEMENT_TYPES = {
        'node': Node,
        'way': Way,
        'relation': Relation,
    }


    def __init__(self, node):
        self.node = node

    def _dict_fetch(self, _dict, str_name):
        """ Given a str name, returns the matching parser
        """
        try:
            klass = _dict[str_name]
        except KeyError:
            raise FileFormatError(
                'Unknown member type : "{}"'.format(str_name))
        return klass

    def get_model(self, str_name):
        """ Given a str name, returns the matching model
        """
        return self._dict_fetch(self.ELEMENT_TYPES, str_name)

    def get_parser(self, str_name):
        """ Given a str name, returns the matching model
        """
        return self._dict_fetch(PARSER_MAP, str_name)

    def transform(self, node, name=None):
        """"Given a node/way/relation, creates a Django object in db

        :return: the db object.
        """
        klass = self.get_parser(node.localName)
        return klass(node).parse()



class RelationMemberParser(AbstractXMLParser):
    def __init__(self, node, relation, order):
        self.node = node
        self.relation = relation
        self.order = order

    def parse(self):
        _type = self.node.attributes['type'].value


        # FIXME: factorize ? modify & use transform()
        if _type == 'node':
            parser = NodeParser(self.node)
        elif _type == 'way':
            parser = WayParser(self.node)
        elif _type == 'relation':
            parser = RelationParser(self.node)
        else:
            raise FileFormatError('Unknown member type : "{}"'.format(_type))
        element = parser.parse()

        return RelationMember.objects.create(
            relation=self.relation,
            element=element,
            order=self.order,
            role=self.node.attributes['role'].value)


class AbstractOSMElementParser(AbstractXMLParser):
    def mk_tags(self):
        pass

    def parse_tags(self, element):
        """
        :param element: the element the tags refer to.
        :type element: OSMElement
        """
        tags = []
        for tag_el in self.node.getElementsByTagName('tag'):
            tags.append(Tag.objects.create(
                element=element,
                k=tag_el.attributes['k'].value,
                v=tag_el.attributes['v'].value,
            ))
        return tags

    def get_basic_attributes(self):
        """ Return shared attributes for all OSM data types

        Can handle both plain version of objects (with an "id" attribute) and nested versions (with a "ref" attribute).
        """
        osmid_key = None
        for key in ('id', 'ref'):
            if key in self.node.attributes:
                osmid_key = key
                break

        if osmid_key is None:
            return {}
        else:
            return {
                'osmid': self.node.attributes[osmid_key].value,
            }

class RelationParser(AbstractOSMElementParser):
    def parse(self):
        relation =  Relation.objects.create(**self.get_basic_attributes())

        for index, node in enumerate(self.node.getElementsByTagName('member')):
            member_parser = RelationMemberParser(node, relation, index)
            member_parser.parse()
        self.parse_tags(relation)
        return relation


class NodeParser(AbstractOSMElementParser):
    def parse(self):
        node = Node.objects.create(
            lat=self.node.attributes['lat'].value,
            lon=self.node.attributes['lon'].value,
            **self.get_basic_attributes())

        self.parse_tags(node)
        return node


class WayParser(AbstractOSMElementParser):
    def parse(self):
        way = Way.objects.create(**self.get_basic_attributes())

        for index, nd in enumerate(self.node.getElementsByTagName('nd')):

            parser = NodeParser(nd)
            node = parser.parse()
            WayNode.objects.create(way=way, node=node, order=index)
        self.parse_tags(way)
        return way


class ActionParser(AbstractXMLParser):
    def parse_element(self, element_node):
        # A old/new tag contains one and only one child element
        try:
            klass = self.get_model(element_node.localName)
        except IndexError:
            raise FileFormatError('old/new tags must have a child node')

        else:
            print(klass)
            #return klass.objects.create(osmid=element_node.attributes['id'])
    def _get_old_new(self):
        for i in ('old', 'new'):
            try:
                tag = self.node.getElementsByTagName(i)[0]
            except IndexError:
                tag = None  # case where there is no « old » (creation)
            yield getFirstNontextChild(tag)

    def parse(self):
        new, old = None, None

        action_type = self.node.attributes['type'].value

        if action_type == 'create':
            new = self.transform(getFirstNontextChild(self.node))

        elif action_type == 'modify':
            old_tag, new_tag = self._get_old_new()
            if old_tag:
                old = self.transform(old_tag)

            if new_tag:
                new = self.transform(new_tag)

        elif action_type == 'delete':
            old_tag, _ = self._get_old_new()

            old = self.transform(old_tag)

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


PARSER_MAP = {
    'node': NodeParser,
    'way': WayParser,
    'relation': RelationParser,
}
