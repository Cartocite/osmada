import re

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
    RE_TAG_PATTERN = re.compile(r'(?P<key>.+)=(?P<value>.+)')

    def __init__(self, pattern):
        """
        :param pattern: a sql pattern to match on tag name
        """
        self.key, self.value = self.split_tag_patterns(pattern)

    @classmethod
    def split_tag_patterns(cls, osm_pattern):
        """
        :param osm_pattern: osm-style patterns like 'amenity=bench' or "highway=*"
        :return: couple of key and value pattern
        """
        m = cls.RE_TAG_PATTERN.match(osm_pattern)
        if m:
            key, value = m.group('key'), m.group('value')
            if value != '*':
                return key, value
            else:
                return key, None
        else:
            raise ValueError('Invalid tag pattern : "{}"'.format(
                osm_pattern))


class AbstractIgnoreTags(AbstractTagFilter):
    def filter(self, qs):
        if self.value:
            return qs.exclude(
                type=self.ACTION,
                new__tags__k=self.key,
                new__tags__v=self.value)
        else:
            return qs.exclude(type=self.ACTION, new__tags__k=self.key)


class IgnoreNewTags(AbstractIgnoreTags):
    """ Filter to ignore creation of elements with some tags
    """
    ACTION = 'create'


class IgnoreChangedTags(AbstractIgnoreTags):
    """ Filter to ignore changes on elements with some given tags
    """
    ACTION = 'modify'
