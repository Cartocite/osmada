from django.test import TestCase

from .models import ActionReport
from osmdata.models import Action


class ActionReportTest(TestCase):
    fixtures = ['test_filters.json']  # Versailles Chantier

    def test_find_main_tag(self):
        action = Action.objects.first()
        operator_sncf = action.new.tags.get(k="operator", v="SNCF")
        railway_station = action.new.tags.get(k="railway", v="station")

        self.assertEqual(
            ActionReport.find_main_tag(action, ['operator=SNCF']),
            operator_sncf)

        self.assertEqual(
            ActionReport.find_main_tag(action, ['operator=*']),
            operator_sncf)

        self.assertEqual(
            ActionReport.find_main_tag(action, ['foo=bar']),
            None)

        self.assertEqual(
            ActionReport.find_main_tag(action, []),
            None)

        self.assertEqual(
            ActionReport.find_main_tag(
                action, ['railway=station', 'operator=*']),
            railway_station)

        self.assertEqual(
            ActionReport.find_main_tag(
                action, ['operator=*', 'railway=station']),
            operator_sncf)

    def test_is_tag_action(self):
        action = Action.objects.first()

        self.assertTrue(ActionReport.is_tag_action(action))
        action.new.tags.get(k='name:ko').delete()
        self.assertFalse(ActionReport.is_tag_action(action))

    def test_added_tags(self):
        action = Action.objects.first()
        name_ko = action.new.tags.get(k='name:ko')

        self.assertEqual(ActionReport.added_tags(action), [name_ko])

        name_ko.delete()
        self.assertEqual(ActionReport.added_tags(action), [])


    def test_removed_tags(self):
        action = Action.objects.first()
        self.assertEqual(ActionReport.removed_tags(action), [])
        action.new.tags.get(k='name').delete()
        old_name = action.old.tags.get(k='name')

        self.assertEqual(ActionReport.removed_tags(action), [old_name])


    def test_modified_tags(self):
        action = Action.objects.first()
        self.assertEqual(ActionReport.modified_tags(action), ([], []))

        # change the name on the new version
        action.new.tags.filter(k='name').update(v='niou')
        old_name = action.old.tags.get(k='name')
        new_name = action.new.tags.get(k='name')

        self.assertEqual(ActionReport.modified_tags(action),
                         ([old_name], [new_name]))
