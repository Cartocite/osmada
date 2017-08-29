from django.conf import settings
from django.db import models
from django.db.models import Q

from osmdata.models import Action, Tag, OSMElement


class ActionReportManager(models.Manager):
    def get_or_create_for_action(self, action):
        try:
            return action.report
        except ActionReport.DoesNotExist:
            return self.create_for_action(action)

    def create_for_action(self, action):
        """ Instantiate and save a new ActionReport for a given Action

        :type action: Action
        :rtype ActionReport:
        """
        ar = ActionReport(action=action)
        ar.main_tag = ar._find_main_tag(settings.TAGS_IMPORTANCE)
        ar.is_tag_action = ar._compute_is_tag_action()
        ar.is_geometric_action = ar._compute_is_geometric_action()

        # Save before populating the many-to-many (which require pk to be set)
        ar.save()

        ar.added_tags.set(ar._compute_added_tags())
        ar.removed_tags.set(ar._compute_removed_tags())

        old_modified_tags, new_modified_tags = ar._compute_modified_tags()
        ar.modified_tags_old.set(old_modified_tags)
        ar.modified_tags_new.set(new_modified_tags)
        return ar


class ActionReport(models.Model):
    """ Results of costly analysis on Action instances
    """
    action = models.OneToOneField(Action, related_name='report')

    main_tag = models.CharField(max_length=100)
    is_tag_action = models.BooleanField()
    is_geometric_action = models.BooleanField()

    added_tags = models.ManyToManyField(Tag, related_name='added_on_reports')
    removed_tags = models.ManyToManyField(Tag, related_name='removed_on_reports')
    modified_tags_old = models.ManyToManyField(Tag, related_name='modified_old_on_reports')
    modified_tags_new = models.ManyToManyField(Tag, related_name='modified_new_on_reports')

    objects = ActionReportManager()

    def _find_main_tag(self, tag_importance):
        """
        :param tags_importance: ordered list giving tag patterns giving
           precedence for (most important first). Each pattern can be a
           compound form.
           ex: ``["railway=station,operator=SNCF", man_made=tower]``.
        :return: the main tag (tag pattern of the list which won), or None
        :rtype str:
        """
        new_tags = Tag.objects.filter(element=self.action.new)
        old_tags = Tag.objects.filter(element=self.action.old)

        # We try first the new tags and then the old tags
        for taglist in old_tags, new_tags:
            for tag_pattern in tag_importance:
                tag_pattern_rules = Tag.split_tag_pattern(tag_pattern)

                 # first rule as a basis
                full_filter = Q(**Tag.parse_tag_pattern(tag_pattern_rules[0]))

                # OR-add the other
                for rule in tag_pattern_rules[1:]:
                    full_filter = full_filter | Q(**Tag.parse_tag_pattern(rule))

                #import ipdb;ipdb.set_trace()
                relevant_tags = taglist.filter(full_filter)
                # If all pattern rules got matched
                if relevant_tags.count() >= len(tag_pattern_rules):
                    # Order by key to have deterministic tags order in the tag pattern
                    return ','.join([str(t) for t in relevant_tags.order_by('k')])

        return None

    def _compute_is_tag_action(self):
        if self.action.type == self.action.CREATE:
            return False
        else:
            old = self.action.old
            new = self.action.new
            return old.tags_dict() != new.tags_dict()

    def _compute_is_geometric_action(self):
        element_type = self.action.new.type()

        if self.action.type in (self.action.CREATE, self.action.DELETE):
            return True

        else:
            if element_type == OSMElement.NODE:
                return (
                    (self.action.new.node.lat != self.action.old.node.lat) or
                    (self.action.new.node.lon != self.action.old.node.lon))

            elif element_type == OSMElement.WAY:
                return self.action.old.way.nodes_list() != self.action.new.way.nodes_list()

            elif element_type == OSMElement.RELATION:
                return False # FIXME: According to the meaning of what is a geometric self.action

    def _compute_added_tags(self):
        new_tags = self.action.new.tags_dict()

        if self.action.type == self.action.CREATE:
            return list(self.action.new.tags.all())
        else:
            old_tags = self.action.old.tags_dict()

            return [self.action.new.tags.get(k=i)
                    for i in new_tags if i not in old_tags]

    def _compute_removed_tags(self):
        new_tags = self.action.new.tags_dict()
        if self.action.type == self.action.CREATE:
            return []
        else:
            old_tags = self.action.old.tags_dict()

            return [self.action.old.tags.get(k=i)
                    for i in old_tags if i not in new_tags]

    def _compute_modified_tags(self):
        if self.action.type == self.action.CREATE:
            return [], list(self.action.new.tags.all())
        else:
            old_tags = self.action.old.tags_dict()

            old_versions = []
            new_versions = []

            for new_tag in self.action.new.tags.all():
                if new_tag.k in old_tags and old_tags[new_tag.k] != new_tag.v:
                    new_versions.append(new_tag)
                    old_versions.append(self.action.old.tags.get(k=new_tag.k))

            return old_versions, new_versions
