from django.conf import settings

from osmdata.exporters import CSVExporter

from .models import ActionReport

class AnalyzedCSVExporter(CSVExporter):
    """ Enhance CSVExporter adding some fields from diffanalysis module
    """

    def get_header_row(self):
        return super().get_header_row() + (
            'main_tag', 'is_geometric_action', 'is_tag_action',
            'added_tags', 'removed_tags', 'modified_tags')

    @staticmethod
    def str_list(l):
        """ Produce a list of str given a list of anything
        """
        return [str(i) for i in l]

    def get_row(self, action):
        return super().get_row(action) + (
            ActionReport.find_main_tag(action, settings.TAGS_IMPORTANCE),
            ActionReport.is_geometric_action(action),
            ActionReport.is_tag_action(action),
            self.str_list(ActionReport.added_tags(action)),
            self.str_list(ActionReport.removed_tags(action)),
            [self.str_list(i) for i in ActionReport.modified_tags(action)],
        )
