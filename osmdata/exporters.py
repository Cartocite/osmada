import datetime

from django.template.loader import render_to_string


class AbstractExporter:
    pass

class CSVExporter(AbstractExporter):
    pass


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
