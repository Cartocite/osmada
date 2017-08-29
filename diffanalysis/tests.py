from django.test import TestCase, override_settings

from osmdata.models import Action

from .models import ActionReport
from .exporters import AnalyzedCSVExporter


class ActionReportTest(TestCase):
    fixtures = ['test_filters.json', 'test_filters_2.json']

    def test_find_single_main_tag(self):
        ar = ActionReport(action=Action.objects.first())

        self.assertEqual(
            ar._find_main_tag(['operator=SNCF']),
            'operator=SNCF')

        self.assertEqual(
            ar._find_main_tag(['operator=*']),
            'operator=SNCF')

        self.assertEqual(
            ar._find_main_tag(['foo=bar']),
            None)

        self.assertEqual(
            ar._find_main_tag([]),
            None)

        self.assertEqual(
            ar._find_main_tag(['railway=station', 'operator=*']),
            'railway=station')

        self.assertEqual(
            ar._find_main_tag(['operator=*', 'railway=station']),
            'operator=SNCF')

    def test_find_multirule_main_tag(self):
        ar = ActionReport(action=Action.objects.first())

        self.assertEqual(
            ar._find_main_tag(['operator=SNCF,foo=bar']),
            None)

        self.assertEqual(
            ar._find_main_tag(['operator=SNCF,railway=*']),
            'operator=SNCF,railway=station')

        self.assertEqual(
            ar._find_main_tag(['railway=*,operator=SNCF']),
            'operator=SNCF,railway=station')

    def test_is_tag_action(self):
        modify_tag_action = Action.objects.filter(type="modify").first()

        modify_ar = ActionReport(action=modify_tag_action)

        self.assertTrue(modify_ar._compute_is_tag_action())

        # Remove the only tag modification
        modify_tag_action.new.tags.get(k='name:ko').delete()
        self.assertFalse(modify_ar._compute_is_tag_action())

        create_action = Action.objects.filter(type="create").first()
        create_ar = ActionReport(action=create_action)
        self.assertFalse(create_ar._compute_is_tag_action())

    def test_modify_action_added_tags(self):
        action = Action.objects.filter(type="modify").first()
        ar = ActionReport(action=action)

        name_ko = action.new.tags.get(k='name:ko')

        self.assertEqual(ar._compute_added_tags(), [name_ko])
        name_ko.delete()
        self.assertEqual(ar._compute_added_tags(), [])

    def test_create_action_added_tags(self):
        ar = ActionReport(action=Action.objects.filter(type="create").first())
        self.assertEqual(len(ar._compute_added_tags()), 2)

    def test_modify_action_removed_tags(self):
        action = Action.objects.first()
        ar = ActionReport(action=action)
        self.assertEqual(ar._compute_removed_tags(), [])
        action.new.tags.get(k='name').delete()
        old_name = action.old.tags.get(k='name')

        self.assertEqual(ar._compute_removed_tags(), [old_name])

    def test_create_action_removed_tags(self):
        ar = ActionReport(action=Action.objects.filter(type='create').first())
        self.assertEqual(ar._compute_removed_tags(), [])

    def test_modify_action_modified_tags(self):
        action = Action.objects.first()
        ar = ActionReport(action=action)
        self.assertEqual(ar._compute_modified_tags(), ([], []))

        # change the name on the new version
        action.new.tags.filter(k='name').update(v='niou')
        old_name = action.old.tags.get(k='name')
        new_name = action.new.tags.get(k='name')

        self.assertEqual(ar._compute_modified_tags(),
                         ([old_name], [new_name]))

    def test_create_action_modified_tags(self):
        action = Action.objects.filter(type='create').first()
        ar = ActionReport(action=action)

        self.assertEqual(
            ar._compute_modified_tags(),
            ([], list(action.new.tags.all())))


class ActionReportGeometricTests(TestCase):
    fixtures = ['test_geometric_action.json']  # Avenue du président Keneddy

    def test_is_geometric_action(self):
        relation_modify_action_report = ActionReport(action=Action.objects.get(pk=43))
        way_modify_action_report = ActionReport(action=Action.objects.get(pk=44))
        way_create_action_report = ActionReport(action=Action.objects.get(pk=30))

        self.assertFalse(
            relation_modify_action_report._compute_is_geometric_action())
        self.assertTrue(way_modify_action_report._compute_is_geometric_action())
        self.assertTrue(way_create_action_report._compute_is_geometric_action())


class ActionReportManagerTest(TestCase):
    fixtures = ['test_filters.json']

    def test_create_report_instance(self):
        ar = ActionReport.objects.create_for_action(Action.objects.first())
        self.assertIsNotNone(ar)
        # Individual fields content are tested through methods in prev tests.

    def test_get_or_create_report_instance(self):
        ar = ActionReport.objects.get_or_create_for_action(Action.objects.first())
        self.assertIsNotNone(ar)
        ar2 = ActionReport.objects.get_or_create_for_action(Action.objects.first())
        self.assertEqual(ar, ar2)


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
