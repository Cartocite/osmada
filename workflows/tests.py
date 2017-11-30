from django.test import TestCase

from diffanalysis.models import ActionReport
import osmdata
from osmdata.filters import IgnoreUsers, IgnoreElementsCreation, IgnoreElementsModification, AbstractActionFilter
from osmdata.importers import AdiffImporter
from osmdata.exporters import CSVExporter
from osmdata.models import Diff
from osmdata.tests.utils import get_test_file_path

from .models import WorkFlow

class TestWorkFlow(TestCase):
    fixtures = ['test_filters.json']  # Versailles Chantier

    def test_workflow_from_settings(self):
        ok_workflow = {
                'import': 'osmdata.importers.AdiffImporter',
                'export' : 'osmdata.exporters.CSVExporter',
                'filters': [
                    ('osmdata.filters.IgnoreUsers', [['jm']]),
                    ('osmdata.filters.IgnoreElementsCreation', ['amenity=waterbasket']),
                    ('osmdata.filters.IgnoreElementsModification', ['amenity=waterbasket']),
                ]
        }
        wf = WorkFlow.from_settings('gare_standard', ok_workflow)

        self.assertEqual(wf.name, 'gare_standard')
        self.assertEqual(wf.ImporterClass, AdiffImporter)
        self.assertEqual(wf.ExporterClass, CSVExporter)
        self.assertEqual(len(wf.filters), 3)
        self.assertIsInstance(wf.filters[0], IgnoreUsers)
        self.assertIsInstance(wf.filters[1], IgnoreElementsCreation)
        self.assertIsInstance(wf.filters[2], IgnoreElementsModification)

    def test_invalid_workflow_from_settings(self):
        missing_export = {'import': 'osmdata.importers.AdiffImporter'}
        missing_import = {'export' : 'osmdata.exporters.CSVExporter'}
        with self.assertRaises(ValueError):
            WorkFlow.from_settings('a', missing_export)
        with self.assertRaises(ValueError):
            WorkFlow.from_settings('a', missing_import)

    def test_run_import(self):
        wf = WorkFlow(
            name='test',
            importer=osmdata.importers.AdiffImporter,
            exporter=osmdata.exporters.CSVExporter)

        wf.run_import(get_test_file_path('create_action.osm'))

    def test_iter_filters_w_filter(self):
        # pretty stupid : it keeps the first
        class _KeepFirstFilter(AbstractActionFilter):
            def __init__(self):
                pass

            def filter(self, qs):
                return qs.all()[:1]

        wf = WorkFlow(
            name='test',
            importer=osmdata.importers.AdiffImporter,
            exporter=osmdata.exporters.CSVExporter,

        )
        wf.filters = [_KeepFirstFilter()]
        wf.diff = Diff.objects.first()
        result = list(wf.iter_filters())
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0][0], _KeepFirstFilter)
        self.assertEqual(list(result[0][1]), list(wf.diff.actions.all()[:1]))


    def test_iter_filters_wo_filter(self):
        wf = WorkFlow(
            name='test',
            importer=osmdata.importers.AdiffImporter,
            exporter=osmdata.exporters.CSVExporter)
        wf.diff = Diff.objects.first()
        result = list(wf.iter_filters())
        self.assertEqual(result, [])

    def test_iter_filters_wo_diff(self):
        wf = WorkFlow(
            name='test',
            importer=osmdata.importers.AdiffImporter,
            exporter=osmdata.exporters.CSVExporter)

        with self.assertRaises(ValueError):
            list(wf.iter_filters())

    def test_output(self):
        class _CounterExporter:
            def run(self, action_qs):
                return action_qs.count()

        wf = WorkFlow(
            name='test',
            importer=osmdata.importers.AdiffImporter,
            exporter=_CounterExporter)

        wf.diff = Diff.objects.first()
        wf.out_qs = wf.diff.actions

        self.assertEqual(wf.write_output(), 1)

    def test_make_actionreports(self):
        wf = WorkFlow(
            name='test',
            importer=osmdata.importers.AdiffImporter,
            exporter=osmdata.exporters.CSVExporter)

        wf.diff = Diff.objects.first()
        wf.make_action_reports()

        self.assertEqual(ActionReport.objects.count(), wf.diff.actions.count())
