from django.test import TestCase

from ..filters import IgnoreUsers, IgnoreElementsCreation, IgnoreElementsModification, IgnoreKeys
from ..models import Action
from diffanalysis.models import ActionReport


class AbstractFilterTestcase(TestCase):
    def assertFilterCount(self,_filter, expected_count):
        filtered_qs = _filter.filter(Action.objects)
        return self.assertEqual(filtered_qs.count(), expected_count)


class TestIgnoreUsers(AbstractFilterTestcase):
    fixtures = ['test_filters.json']  # Versailles Chantier

    def test_empty_list(self):
        self.assertFilterCount(IgnoreUsers([]), 1)

    def test_ignored_new_user(self):
        self.assertFilterCount(IgnoreUsers(['foo', 'Eunjeung Yu']), 0)

    def test_ignored_old_user(self):
        """ Old user of an item should not be taken into account for that
        filter
        """
        self.assertFilterCount(IgnoreUsers(['foo', 'overflorian']), 1)


class TestIgnoreElementsCreation(AbstractFilterTestcase):
    fixtures = ['test_filters_2.json']  # Pont Cadinet

    def test_non_present_tag(self):
        self.assertFilterCount(IgnoreElementsCreation("non=existent"), 3)

    def test_noncreate_tag(self):
        self.assertFilterCount(IgnoreElementsCreation("access=no"), 3)

    def test_modify_tag(self):
        self.assertFilterCount(IgnoreElementsCreation("shop=newsagent"), 2)

    def test_modify_wrong_val(self):
        self.assertFilterCount(IgnoreElementsCreation("shop=coffee"), 3)

    def test_modify_tag_wildcard_value(self):
        self.assertFilterCount(IgnoreElementsCreation("shop=*"), 2)


class TestIgnoreModifiedTags(AbstractFilterTestcase):
    fixtures = ['test_filters_2.json']  # Pont Cadinet

    def test_non_present_tag(self):
        self.assertFilterCount(IgnoreElementsModification("non=existent"), 3)

    def test_create_tag(self):
        self.assertFilterCount(IgnoreElementsModification("access=no"), 2)

    def test_modify_wrong_val(self):
        self.assertFilterCount(IgnoreElementsModification("access=hello"), 3)

    def test_modify_tag_wildcard_value(self):
        self.assertFilterCount(IgnoreElementsModification("access=*"), 2)


class TestIgnoredKeys(AbstractFilterTestcase):
    fixtures = ['test_filters.json']  # Pont Cadinet

    def setUp(self):
        # This filter requires the ActionReports
        for action in Action.objects.all():
            ActionReport.objects.get_or_create_for_action(action)

    def test_empty_list(self):
        self.assertFilterCount(IgnoreKeys([]), 1)

    def test_non_present_tag(self):
        self.assertFilterCount(IgnoreKeys(['shop']), 1)

    def test_non_present_tags(self):
        self.assertFilterCount(IgnoreKeys(['shop', 'name']), 1)

    def test_present_tag(self):
        self.assertFilterCount(IgnoreKeys(['name:ko']), 0)
