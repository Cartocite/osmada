from django.test import TestCase

from ..exporters import AdiffExporter
from ..models import Action

class AdiffExporterTest(TestCase):
    fixtures = ['test_filters.json'] #  Versailles Chantier

    def test_export(self):
        """Rough test"""
        exporter = AdiffExporter()
        out = exporter.run(Action.objects)

        self.assertEqual(out.count('<action'), 1)
        self.assertEqual(out.count('</action>'), 1)

        self.assertEqual(out.count('<old>'), 1)
        self.assertEqual(out.count('<new>'), 1)
        open('/tmp/test.xml', 'w').write(out)
