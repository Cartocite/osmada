from django.test import TestCase

from diffanalysis.models import ActionReport
import osmdata
from osmdata.filters import IgnoreUsers, IgnoreElementsCreation, IgnoreElementsModification, AbstractActionFilter
from osmdata.importers import AdiffImporter
from osmdata.exporters import CSVExporter
from osmdata.models import Diff
from osmdata.tests.utils import get_test_file_path

from .models import Step, WorkFlow

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
        } # TO BE DELETED
        ok_workflow = {
            'name': 'test-wf',
            'flow': [
                {'type': 'import', 'class': 'osmdata.importers.AdiffImporter'},
                {'type': 'filter', 'class': 'osmdata.filters.IgnoreUsers', 'params': ['jm']} ,
                {'type': 'filter', 'class': 'osmdata.filters.IgnoreElementsCreation', 'params': ['amenity=wastebasket']} ,
                {'type': 'filter', 'class': 'osmdata.filters.IgnoreElementsModification', 'params': ['amenity=wastebasket']} ,
                {'type': 'export', 'class': 'osmdata.exporters.CSVExporter'}
            ]
        }
        wf = WorkFlow.from_settings('gare_standard', ok_workflow)

        self.assertEqual(wf.name, 'gare_standard')
        self.assertEqual(len(wf.steps), 5)
        self.assertIsInstance(wf.steps[0].instance, AdiffImporter)
        self.assertIsInstance(wf.steps[1].instance, IgnoreUsers)
        self.assertIsInstance(wf.steps[2].instance, IgnoreElementsCreation)
        self.assertIsInstance(wf.steps[3].instance, IgnoreElementsModification)
        self.assertIsInstance(wf.steps[4].instance, CSVExporter)

    def test_invalid_workflow_from_settings(self):
        with self.assertRaises(ValueError, msg='missing name'):
            WorkFlow.from_settings('a', {'flow': []})

        with self.assertRaises(ValueError, msg='missing flow'):
            WorkFlow.from_settings('a', {'name': 'foo'})

        with self.assertRaises(ValueError, msg='unknown key'):
            WorkFlow.from_settings('a', {
                'name': 'foo', 'flow': [], 'bar': 'zut'
            })

        with self.assertRaises(ValueError, msg='wrong step type'):
            WorkFlow.from_settings('a', {
                'name': 'foo', 'flow': [
                    {'type': 'zut', 'class': 'osmdata.exporters.CSVExporter'},
                ]
            })

        with self.assertRaises(ValueError, msg='inexistant step class'):
            WorkFlow.from_settings('a', {
                'name': 'foo',
                'flow': [{'type': 'exporter', 'class': 'osmdata.exporters.No'}]
            })

    def test_run_empty(self):
        wf = WorkFlow(
            name='test',
            steps=[]
        )
        wf.run([get_test_file_path('create_action.osm')], ['/dev/null'])

    def test_run_import(self):
        wf = WorkFlow(
            name='test',
            steps=[
                Step(Step.STEP_IMPORT, osmdata.importers.AdiffImporter, [])
            ]
        )
        self.assertEqual(Diff.objects.count(), 1)
        self.assertEqual(ActionReport.objects.count(), 0)

        wf.run([get_test_file_path('create_action.osm')], ['/dev/null'])

        self.assertEqual(Diff.objects.count(), 2)
        # Check that action reports have been made
        self.assertEqual(ActionReport.objects.count(), 1)

    def test_output(self):
        class _CounterExporter:
            def run(self, action_qs):
                return action_qs.count()

        wf = WorkFlow(
            name='test',
            steps=[
                Step(Step.STEP_IMPORT, osmdata.importers.AdiffImporter, []),
                Step(Step.STEP_EXPORT, _CounterExporter, [])
            ]
        )
        wf.run([get_test_file_path('create_action.osm')], ['/dev/null'])
        self.assertEqual(wf.last_step_output, 1)

    def test_filter_filter_in(self):
        wf = WorkFlow(
            name='test',
            steps=[
                Step(Step.STEP_IMPORT, osmdata.importers.AdiffImporter, []),
                Step(Step.STEP_FILTER, osmdata.filters.IgnoreUsers,
                     [["DoNotExist"]])
            ]
        )
        wf.run([get_test_file_path('create_action.osm')], ['/dev/null'])
        self.assertEqual(wf.last_step_output.count(), 1)

    def test_filter_filter_out(self):
        wf = WorkFlow(
            name='test',
            steps=[
                Step(Step.STEP_IMPORT, osmdata.importers.AdiffImporter, []),
                Step(Step.STEP_FILTER, osmdata.filters.IgnoreUsers, [["Yann_L"]])
            ]
        )
        wf.run([get_test_file_path('create_action.osm')], ['/dev/null'])
        self.assertEqual(wf.last_step_output.count(), 0)
