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
