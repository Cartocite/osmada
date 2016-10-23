from django.test import TestCase

from .models import WorkFlow
from osmdata.filters import IgnoreUsers, IgnoreNewTags, IgnoreChangedTags
from osmdata.importers import AdiffImporter
from osmdata.exporters import CSVExporter

class TestWorkFlow(TestCase):
    def test_workflow_from_settings(self):
        ok_workflow = {
                'import': 'osmdata.importers.AdiffImporter',
                'export' : 'osmdata.exporters.CSVExporter',
                'filters': [
                    ('osmdata.filters.IgnoreUsers', [['jm']]),
                    ('osmdata.filters.IgnoreNewTags', ['amenity=waterbasket']),
                    ('osmdata.filters.IgnoreChangedTags', ['amenity=waterbasket']),
                ]
        }
        wf = WorkFlow.from_settings('gare_standard', ok_workflow)

        self.assertEqual(wf.name, 'gare_standard')
        self.assertEqual(wf.ImporterClass, AdiffImporter)
        self.assertEqual(wf.ExporterClass, CSVExporter)
        self.assertEqual(len(wf.filters), 3)
        self.assertIsInstance(wf.filters[0], IgnoreUsers)
        self.assertIsInstance(wf.filters[1], IgnoreNewTags)
        self.assertIsInstance(wf.filters[2], IgnoreChangedTags)
