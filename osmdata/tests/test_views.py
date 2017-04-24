from django.test import TestCase

class ViewsTest(TestCase):
    fixtures = ['test_filters.json']  # Versailles Chantier

    def test_diff_detail(self):
        response = self.client.get('/osmdata/diff/2')
        # test is succint because most of the logic is already tested in
        # exporters
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<osm', response.content)
        # test some (quite random) strings that are supposed to be present in
        # output, as it seems that a HTTP 200 is returned, even in case of
        # TemplateSyntaxError.
        self.assertIn(b'visible="true"', response.content)
        self.assertIn(b'fr:Gare de Versailles-Chantiers', response.content)
