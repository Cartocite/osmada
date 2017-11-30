import datetime

from django.test import TestCase
import pytz

from ..patchers import FixRemoveOperationMetadata
from osmdata.models import Action


class TestFixRemoveOperationMetadata(TestCase):
    # From Sevran Beaudoutes (removing all un-needed data, keeping only our
    # interesting case)
    fixtures = ['test_patchers']

    def test_heuristic_ok(self):
        remove_action =  Action.objects.get(type=Action.REMOVE)

        # Before
        self.assertEqual(remove_action.new.user, 'overflorian')
        self.assertEqual(
            remove_action.new.timestamp,
            datetime.datetime(2016, 6, 1, 8, 15, 46, tzinfo=pytz.utc))
        self.assertEqual(remove_action.new.changeset, 39705062)

        patcher = FixRemoveOperationMetadata()
        patcher.patch(Action.objects.all())


        remove_action =  Action.objects.get(type=Action.REMOVE)  # refresh
        # After
        self.assertEqual(remove_action.new.user, 'johnparis')
        self.assertEqual(
            remove_action.new.timestamp,
            datetime.datetime(2017, 11, 22, 11, 53, 31, tzinfo=pytz.utc))
        self.assertEqual(remove_action.new.changeset, 53999449)

    def test_heuristic_ko(self):
        # Compared to previous test, we remove the action on relation, so that
        # the heuristic wont find it.
        Action.objects.get(new__relation__isnull=False).delete()

        patcher = FixRemoveOperationMetadata()
        patcher.patch(Action.objects.all())

        remove_action =  Action.objects.get(type=Action.REMOVE)
        # After
        self.assertEqual(remove_action.new.user, '')
        self.assertIsNone(remove_action.new.timestamp)
        self.assertIsNone(remove_action.new.changeset)
