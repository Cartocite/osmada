from django.conf import settings
from django.db import models

from osmdata.models import Tag


class ActionReport():
    @classmethod
    def create_from_action(cls, action):
        cls.find_main_tag(action)

    @classmethod
    def find_main_tag(cls, action, tags_importance):
        """
        :type action: Action
        :param tags_importance: ordered list giving tags precedence for (most
          important first)
        """
        new_tags = Tag.objects.filter(element=action.new)
        old_tags = Tag.objects.filter(element=action.old)

        # FIXME: could be optimised with a SQL ORDER BY CASE...

        # We try first the new tags and then the old tags
        for taglist in new_tags, old_tags:
            for tag_pattern in tags_importance:
                relevant_tags = taglist.filter(
                    **Tag.parse_tag_pattern(tag_pattern))
                if relevant_tags.exists():
                    return relevant_tags.first()

        return None

    @classmethod
    def is_tag_action(cls, action):
        old = action.old
        new = action.new
        return old.tags_dict() != new.tags_dict()

    @classmethod
    def added_tags(cls, action):
        old_tags = action.old.tags_dict()
        new_tags = action.new.tags_dict()

        return [action.new.tags.get(k=i)
                for i in new_tags if i not in old_tags]

    @classmethod
    def removed_tags(cls, action):
        old_tags = action.old.tags_dict()
        new_tags = action.new.tags_dict()

        return [action.old.tags.get(k=i)
                for i in old_tags if i not in new_tags]

    @classmethod
    def modified_tags(cls, action):
        old_tags = action.old.tags_dict()

        old_versions = []
        new_versions = []

        for new_tag in action.new.tags.all():
            if new_tag.k in old_tags and old_tags[new_tag.k] != new_tag.v:
                new_versions.append(new_tag)
                old_versions.append(action.old.tags.get(k=new_tag.k))

        return old_versions, new_versions
