from django.test import TestCase, override_settings

from osmdata.models import Action

from .models import ActionReport
from .exporters import AnalyzedCSVExporter

class ActionReportTest(TestCase):
    fixtures = ['test_filters.json', 'test_filters_2.json']

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
        modify_tag_action = Action.objects.filter(type="modify").first()

        self.assertTrue(ActionReport.is_tag_action(modify_tag_action))

        modify_tag_action.new.tags.get(k='name:ko').delete()  # Remove the only tag modification
        self.assertFalse(ActionReport.is_tag_action(modify_tag_action))

        create_action = Action.objects.filter(type="create").first()
        self.assertFalse(ActionReport.is_tag_action(create_action))

    def test_modify_action_added_tags(self):
        action = Action.objects.filter(type="modify").first()
        name_ko = action.new.tags.get(k='name:ko')

        self.assertEqual(ActionReport.added_tags(action), [name_ko])

        name_ko.delete()
        self.assertEqual(ActionReport.added_tags(action), [])

    def test_create_action_added_tags(self):
        action = Action.objects.filter(type="create").first()

        self.assertEqual(len(ActionReport.added_tags(action)), 2)

    def test_modify_action_removed_tags(self):
        action = Action.objects.first()
        self.assertEqual(ActionReport.removed_tags(action), [])
        action.new.tags.get(k='name').delete()
        old_name = action.old.tags.get(k='name')

        self.assertEqual(ActionReport.removed_tags(action), [old_name])

    def test_create_action_removed_tags(self):
        action = Action.objects.filter(type='create').first()
        self.assertEqual(ActionReport.removed_tags(action), [])

    def test_modify_action_modified_tags(self):
        action = Action.objects.first()
        self.assertEqual(ActionReport.modified_tags(action), ([], []))

        # change the name on the new version
        action.new.tags.filter(k='name').update(v='niou')
        old_name = action.old.tags.get(k='name')
        new_name = action.new.tags.get(k='name')

        self.assertEqual(ActionReport.modified_tags(action),
                         ([old_name], [new_name]))

    def test_create_action_modified_tags(self):
        action = Action.objects.filter(type='create').first()

        self.assertEqual(ActionReport.modified_tags(action), ([], list(action.new.tags.all())))


class ActionReportGeometricTests(TestCase):
    fixtures = ['test_geometric_action.json']  # Avenue du président Keneddy

    def test_is_geometric_action(self):
        relation_modify_action = Action.objects.get(pk=43)
        way_modify_action = Action.objects.get(pk=44)

        way_create_action = Action.objects.get(pk=30)

        self.assertFalse(ActionReport.is_geometric_action(relation_modify_action))

        self.assertTrue(ActionReport.is_geometric_action(way_modify_action))

        self.assertTrue(ActionReport.is_geometric_action(way_create_action))


@override_settings(TAGS_IMPORTANCE=['railway=*'])
class ExporterTests(TestCase):
    fixtures = ['test_filters.json'] #  Versailles Chantier

    def test_csv_export(self):
        """Rough test"""
        exporter = AnalyzedCSVExporter()
        out = exporter.run(Action.objects)

        header, line1 = out.strip().splitlines()

        self.assertIn(
            'main_tag,is_geometric_action,is_tag_action,added_tags,removed_tags,modified_tags',
            header)
        self.assertIn(
            'railway=station,False,True,[\'name:ko=베르사유 샹티에역\'],[],"[[], []]"',
            line1)
