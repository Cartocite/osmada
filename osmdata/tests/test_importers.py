import tempfile

from django.test import TestCase

from ..importers import AdiffImporter, ImporterError
from .utils import get_test_file_path


class ImporterTests(TestCase):
    def setUp(self):
        self.f = tempfile.NamedTemporaryFile()

    def tearDown(self):
        self.f.close()

    def test_open_nonexistent_file(self):
        with self.assertRaises(ImporterError):
            importer = AdiffImporter()
            importer.run('/tmp/do-not-exist-1234')

    def test_open_valid_file(self):
        importer = AdiffImporter()
        # We barely check there is no error
        self.assertIsNotNone(importer.run(get_test_file_path('create_action.osm')))

    def test_open_inexistant_file(self):
        with self.assertRaises(ImporterError):
            importer = AdiffImporter()
            importer.run(get_test_file_path('i-do-not-exist.osm'))

    def test_open_invalid_data_file(self):
        with self.assertRaises(ImporterError):
            importer = AdiffImporter()
            importer.run(get_test_file_path('invalid_action.osm'))
