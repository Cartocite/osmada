from __future__ import unicode_literals

from django.db import models


class Bounds(models.Model):
    minlat = models.FloatField()
    minlon = models.FloatField()
    maxlat = models.FloatField()
    maxlon = models.FloatField()


class OSMElement(models.Model):
    SUBTYPES = ('node', 'relation', 'way')

    osmid = models.PositiveIntegerField(null=True)
    version = models.PositiveIntegerField(null=True)
    timestamp = models.DateTimeField(null=True)
    uid = models.PositiveIntegerField(null=True)
    user = models.CharField(blank=True, max_length=255)
    changeset = models.PositiveIntegerField(null=True)
    bounds = models.OneToOneField(Bounds, null=True)

    def specialized(self):
        return getattr(self, self.type())

    def type(self):
        for i in self.SUBTYPES:
            if hasattr(self, i):
                return i
        raise ValueError('{} must be of one of those subtypes {}'.format(self, self.SUBTYPES))

    def __str__(self):
        return '<{} id="{}">'.format(self.__class__.__name__, self.osmid)

class Tag(models.Model):
    element = models.ForeignKey(OSMElement, related_name='tags')
    k = models.CharField(max_length=255)
    v = models.CharField(max_length=255)

    def __str__(self):
        return '{}={}'.format(self.k, self.v)

class Node(OSMElement):
    lat = models.FloatField() # FIXME ; could be validated better
    lon = models.FloatField()


class Way(OSMElement):
    nodes = models.ManyToManyField(Node, through='WayNode')


class WayNode(models.Model):
    way = models.ForeignKey(Way)
    node = models.ForeignKey(Node)
    order = models.PositiveIntegerField()


class Relation(OSMElement):
    members = models.ManyToManyField(
        OSMElement, through='RelationMember', related_name='parent_relation')


class RelationMember(models.Model):
    relation = models.ForeignKey(Relation)
    element = models.ForeignKey(OSMElement, related_name='related_element')
    order = models.PositiveIntegerField()
    role = models.CharField(max_length=255, blank=True)


class Action(models.Model):
    type = models.CharField(
        max_length=10, choices=(
            ('delete', 'delete'),
            ('modify', 'modify'),
            ('create', 'create')))

    new = models.OneToOneField(OSMElement, related_name='new_for', null=True)
    old = models.OneToOneField(OSMElement, related_name='old_for', null=True)

class Diff(models.Model):
    actions = models.ManyToManyField(Action)
    import_date = models.DateTimeField(auto_now_add=True)
