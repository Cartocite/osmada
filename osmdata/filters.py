from osmdata.models import Action, Tag


class AbstractActionFilter:
    def __init__(self, *args):
        """Initialization receives and stores arguments from settings
        """
        raise NotImplemented

    def filter(self, diff_qs):
        """
        :param diff_qs: the queryset to filter
        :type diff_qs: a django.db.QuerySet
        :rtype: django.db.QuerySet
        """
        raise NotImplemented


class IgnoreUsers(AbstractActionFilter):
    """ Filter to ignore a list of users
    """

    def __init__(self, users):
        """
        :param users: a list of openstreetmap usernames
        """
        self.users = users

    def filter(self, qs):
        return qs.exclude(new__user__in=(self.users))


class AbstractTagFilter(AbstractActionFilter):
    def __init__(self, pattern):
        """
        :param pattern: an osm pattern to match on tag name
        """
        self.filter_spec = {
            'new__tags__{}'.format(k): v
            for k, v in Tag.parse_tag_pattern(pattern).items()}


class AbstractIgnoreTags(AbstractTagFilter):
    def filter(self, qs):
        return qs.exclude(type=self.ACTION, **self.filter_spec)


class IgnoreNewTags(AbstractIgnoreTags):
    """ Filter to ignore creation of elements with some tags
    """
    ACTION = Action.CREATE


class IgnoreChangedTags(AbstractIgnoreTags):
    """ Filter to ignore changes on elements with some given tags
    """
    ACTION = Action.MODIFY
