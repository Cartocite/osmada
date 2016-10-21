from django.utils.module_loading import import_string


class WorkFlow:
    def __init__(self, name, importer, exporter):
        self.name = name
        self.importer = importer
        self.exporter = exporter
        self.filters = []

    def add_filter(self, _filter):
        """
        :param _filter: the filter instance
        """
        self.filters.append(_filter)

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
            ('osmdata.filters.IgnoreNewTags', ['amenity=waterbasket']),
            ('osmdata.filters.IgnoreChangedTags', ['amenity=waterbasket']),
        }

        :param name: The workflow name you choose
        :param setting_spec: a dict specifying the workflow spec (see above).
        """
        try:
            ImporterClass = import_string(spec['import'])
            ExporterClass = import_string(spec['export'])
        except KeyError:
            raise ValueError(
                '"import" and "export" keys are required in workflow spec.')
        except ImportError:
            raise

        workflow = cls(name, ImporterClass, ExporterClass)

        for klass_path, args in spec.get('filters', []):
            try:
                Klass = import_string(klass_path)
            except ImportError:
                raise
            workflow.add_filter(Klass(*args))

        return workflow
