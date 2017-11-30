from django.utils.module_loading import import_string


from diffanalysis.models import ActionReport
from osmdata.patchers import FixRemoveOperationMetadata


class WorkFlow:
    """ Complete Import-Filter-Export cycle

    a WorkFlow instance holds all the step and internal state for a diff
    processing. steps are :

    1. Load diff data from an external source into DB.
    2. Apply one or several filters
    3. Output as string in a given format

    """

    def __init__(self, name, importer, exporter):
        self.name = name
        self.ImporterClass = importer
        self.ExporterClass = exporter
        self.filters = []
        self.diff = None

    def add_filter(self, _filter):
        """
        :param _filter: the filter instance
        """
        self.filters.append(_filter)

    def run_import(self, path):
        """ Import an external resource into db using the importer

        The `path` nature depends on the importer class.
        :param path: the path (file path, url…) to fetch
        :return: the created diff model instance
        :rtype: Diff
        """
        importer = self.ImporterClass(path)
        self.diff = importer.run()
        return self.diff

    def make_action_reports(self):
        """ Make an ActionReport for each Action of the queryset

        This operation is costly, but the result might be used by some
        filters.
        """
        for action in self.diff.actions.all():
            ActionReport.objects.get_or_create_for_action(action)

    def iter_filters(self):
        """ Iteratively apply filters on diff

        :yield: filter obj and queryset at each iteration
        """
        if self.diff is None:
            raise ValueError("You should import data first")

        self.out_qs = self.diff.actions.select_related('report')
        for _filter in self.filters:
            self.out_qs = _filter.filter(self.out_qs)
            yield _filter, self.out_qs

    def write_output(self):
        return self.ExporterClass().run(self.out_qs)

    def apply_data_patches(self):
        """ That step modifies the data in database

        This is mainly intended for workarounds
        """
        # Make it configurable ?
        patches = [FixRemoveOperationMetadata]
        for PatchClass in patches:
            patch = PatchClass()
            yield patch.description
            patch.patch(self.diff.actions)

    @classmethod
    def from_settings(cls, name, spec):
        """
        Use a setting spec dict to configure a workflow.

        The setting_spec dict requires the following fields :
          - import: the importer class (as dotted path str)
          - export: the exporter class (as dotted path str)
          - filters: a list of filter spec

        The filter spec is a 2-uplet :
          1. the filter class (as dotted path str)
          2. an optional list of argument to be passed to the filter
          constructor

        Ex of setting spec:
        {
          'import': 'osmdata.importers.AdiffImporter',
          'export' : 'osmdata.exporters.CSVExporter',
          'filters': [
            ('osmdata.filters.IgnoreUsers', [['jm']]),
            ('osmdata.filters.IgnoreElementsCreation', ['amenity=waterbasket']),
            ('osmdata.filters.IgnoreElementsModification', ['amenity=waterbasket']),
        }

        :param name: The workflow name you choose
        :param setting_spec: a dict specifying the workflow spec (see above).
        :rtype: Diff
        """
        try:
            ImporterClass = import_string(spec['import'])
            ExporterClass = import_string(spec['export'])
        except KeyError:
            raise ValueError(
                '"import" and "export" keys are required in workflow spec.')

        workflow = cls(name, ImporterClass, ExporterClass)

        for klass_path, args in spec.get('filters', []):
            Klass = import_string(klass_path)
            workflow.add_filter(Klass(*args))

        return workflow
