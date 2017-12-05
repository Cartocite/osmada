from django.db.models import Q

from osmdata.models import Action, Tag


class AbstractActionFilter:  # pragma: no cover
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


class AbstractIgnoreMatchingElements(AbstractTagFilter):
    def filter(self, qs):
        return qs.exclude(type=self.ACTION, **self.filter_spec)


class IgnoreElementsCreation(AbstractIgnoreMatchingElements):
    """ Filter to ignore creation of matching elements
    """
    ACTION = Action.CREATE


class IgnoreElementsModification(AbstractIgnoreMatchingElements):
    """ Filter to ignore changes on matching elements
    """
    ACTION = Action.MODIFY


class IgnoreKeys(AbstractActionFilter):
    """ We want to totaly ignore some keys

    So just exclude the actions that are related *only* to tags change and
    *only*  to those ignored keys.
    """

    def __init__(self, ignored_keys):
        self.ignored_keys = ignored_keys
        self.re_interesting_keys = r'^(?!({})$).*'.format(
            '|'.join(ignored_keys))

    def filter(self, qs):
        # Build a regex that will match only

        # A performance improvement would be to add a field in ActionReport
        # with the list of all related tags, whatever they are
        # added/removed/deleted…

        return qs.filter(
            # Geometric actions carry more than just something about our tags
            Q(report__is_geometric_action=True) |
            # node being neither geometric nor tag (membership change)
            Q(report__is_tag_action=False) |
            # If we have a tag related action, it must be related at least to
            # one key that is outside our list
            Q(report__is_tag_action=True) & (
                Q(report__added_tags__k__iregex=self.re_interesting_keys)
                | Q(report__removed_tags__k__iregex=self.re_interesting_keys)
                | Q(report__modified_tags_old__k__iregex=self.re_interesting_keys)
                | Q(report__modified_tags_old__k__iregex=self.re_interesting_keys)
            )
        ).distinct()


class IgnoreSmallNodeMoves(AbstractActionFilter):
    def __init__(self, min_move):
        self.min_move = min_move

    def filter(self, qs):
        # generate the missing latlon, if required
        for i in Node.objects.filter(latlon__isnull=True):
            i.save()

        qs_w_distance = qs.annotate(
            move=monkeypatch.Distance(
                'old__node__latlon', 'new__node__latlon'))
        return qs_w_distance.filter(
            # Keep non-nodes or non-modification
            Q(old__node=None) | Q(new__node=None)
            # Keep zero-moves
            | Q(move=0)
            # Keep big enough moves
            | Q(move__gte=self.min_move))
