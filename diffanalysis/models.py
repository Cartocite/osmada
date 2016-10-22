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
