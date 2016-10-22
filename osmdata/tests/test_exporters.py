from django.test import TestCase

from ..exporters import AdiffExporter, CSVExporter
from ..models import Action

class ExporterTests(TestCase):
    fixtures = ['test_filters.json'] #  Versailles Chantier

    def test_adiff_export(self):
        """Rough test"""
        exporter = AdiffExporter()
        out = exporter.run(Action.objects)

        self.assertEqual(out.count('<action'), 1)
        self.assertEqual(out.count('</action>'), 1)

        self.assertEqual(out.count('<old>'), 1)
        self.assertEqual(out.count('<new>'), 1)

    def test_csv_export(self):
        """Rough test"""
        exporter = CSVExporter()
        out = exporter.run(Action.objects)

        header, line1 = out.split('\n')

        self.assertEqual(
            header,
            'id,version,timestamp,changeset,user,uid,action_type')

        self.assertEqual(
            header,
            '3497428295,6,2016-09-10 14:41:56+00:00,42060502,Eunjeung Yu,4540825,modify')
