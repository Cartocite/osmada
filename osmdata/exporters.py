import csv
import datetime
import io

from django.template.loader import render_to_string


class AbstractExporter:
    pass

class CSVExporter(AbstractExporter):
    def get_header_row(self):
        return (
            'id', 'version', 'timestamp', 'changeset',
            'user', 'uid', 'action_type', 'element_type')

    def get_row(self, action):
        return (action.new.osmid, action.new.version,
                action.new.timestamp, action.new.changeset,
                action.new.user, action.new.uid, action.type,
                action.new.type())

    def run(self, actions_qs):
        out = io.StringIO()
        writer = csv.writer(out)

        writer.writerow(self.get_header_row())

        for action in actions_qs.all():
            writer.writerow(self.get_row(action))

        return out.getvalue()


class AdiffExporter(AbstractExporter):
    def run(self, actions_qs):
        """
        :param actions_qs: the actions to export as queryset
        :type actions_qs: an Action QuerySet
        :rtype: str
        """
        # That's like a diff we won't save.
        #
        # We mimick a diff so that we can
        # use the exact same template as the view.
        diff = {
            'actions': actions_qs,
            'import_date': datetime.datetime.now(),
        }

        return render_to_string(
            'osmdata/adiff/diff_detail.xml',
            {'diff': diff}
        )
