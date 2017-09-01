from django.conf import settings

from osmdata.exporters import CSVExporter

from .models import ActionReport

class AnalyzedCSVExporter(CSVExporter):
    """ Enhance CSVExporter adding some fields from diffanalysis module
    """

    def get_header_row(self):
        return super().get_header_row() + (
            'main_tag', 'is_geometric_action', 'is_tag_action',
            'added_tags', 'removed_tags', 'modified_tags', 'version_delta')

    @staticmethod
    def str_list(l):
        """ Produce a list of str given a list of anything
        """
        return [str(i) for i in l]

    def get_row(self, action):
        ar = ActionReport.objects.get_or_create_for_action(action)
        return super().get_row(action) + (
            ar.main_tag,
            ar.is_geometric_action,
            ar.is_tag_action,
            self.str_list(ar.added_tags.all()),
            self.str_list(ar.removed_tags.all()),
            [self.str_list(i.all())
             for i in [ar.modified_tags_old, ar.modified_tags_new]],
            ar.version_delta,
        )
