import logging

from django.utils.module_loading import import_string


from diffanalysis.models import ActionReport
from osmdata.models import Action
from osmdata.patchers import FixRemoveOperationMetadata

logger = logging.getLogger(__name__)


class Step:
    STEP_FILTER = 'filter'
    STEP_IMPORT = 'import'
    STEP_EXPORT = 'export'

    STEP_TYPES = [STEP_FILTER, STEP_IMPORT, STEP_EXPORT]

    def __init__(self, step_type, step_class, step_params):
        if step_type not in self.STEP_TYPES:
            raise ValueError('Unknown step type : {}'.format(step_type))
        self.type = step_type
        self.instance = step_class(*step_params)


def reversed_copy(l):
    # We use those list as stack so we want to reverse them.
    l_stack = l.copy()
    l_stack.reverse()
    return l_stack


class WorkFlow:
    """Complete Import-Filter-Export cycle

    A workflow instance holds a succession of several of those steps, in any
    order :

    - import (from files)
    - export in some format (to file or to stdout)
    - filtering (non destructive, data is always kept, but not handed to the
      next step(s))
    """

    def __init__(self, name, steps):
        self.name = name
        self.steps = steps
        self.diff = None

    def run(self, input_paths, output_paths):
        qs = Action.objects.none()
        diff = None
        self.last_step_output = None

        output_paths_stack = reversed_copy(output_paths)
        input_paths_stack = reversed_copy(input_paths)

        for step in self.steps:
            logger.debug('Running step {}'.format(step.instance))

            if step.type == step.STEP_IMPORT:
                input_path = input_paths_stack.pop()
                logger.info('Importing from "{}"'.format(input_path))
                logger.debug('next steps will use this data')
                diff = step.instance.run(input_path)
                # every import step overwrite any previous qs :
                qs = diff.actions
                self.last_step_output = qs
                for patch_name in self.apply_data_patches(qs):
                    logger.debug('Applying data patch {}'.format(patch_name))

                self.make_action_reports(qs)

            elif step.type == step.STEP_EXPORT:
                output_path = output_paths_stack.pop()
                logger.info('Exporting to "{}"'.format(output_path))
                output = step.instance.run(qs)
                with open(output_path, 'w') as output_fd:
                    output_fd.write(str(output))
                self.last_step_output = output

            elif step.type == step.STEP_FILTER:
                qs = step.instance.filter(qs)
                self.last_step_output = qs

    def make_action_reports(self, qs):
        """ Make an ActionReport for each Action of the queryset

        This operation is costly, but the result might be used by some
        filters.

        :type qs: an Action QuerySet
        """
        for action in qs.all():
            ActionReport.objects.get_or_create_for_action(action)

    def apply_data_patches(self, qs):
        """ That step modifies the data in database

        :type qs: an Action QuerySet
        This is mainly intended for workarounds
        """
        # Make it configurable ?
        patches = [FixRemoveOperationMetadata]
        for PatchClass in patches:
            patch = PatchClass()
            yield patch.description
            patch.patch(qs)

    @classmethod
    def from_settings(cls, name, spec):
        """Use a setting spec dict to configure a workflow.

        The setting_spec dict require only two keys :


        - 'flow', which is a list of steps, each step being a dict with
           3 keys :
            - type: the importer class (as dotted path str)
            - class: theexecutable class (as dotted path str). It can either
              relate to a Filter, an Importer or an Exporter)
            - params : a list of parameters
              passed to the Exporter/Importer/Filter
        - 'name', which is the name of your workflow

        The order of the list matters (execution order)

        Ex of setting spec:
        {
            'name': 'my-wf',
            'flow': [
                {'type': 'import', 'class', 'osmdata.importers.AdiffImporter'},
                {'type': 'filter', 'class': 'osmdata.filters.IgnoreUsers', 'params': ['jm']} ,
                {'type': 'filter', 'class': 'osmdata.filters.IgnomeElementsCreation', 'params': ['amenity=wastebasket']} ,
                {'type': 'filter', 'class': 'osmdata.filters.IgnomeElementsModification', 'params': ['amenity=wastebasket']} ,
                {'type': 'export': 'class': 'osmdata.exporters.CSVExporter'}
            ]
        }

        :param name: The workflow name you choose
        :param setting_spec: a dict specifying the workflow spec (see above).
        :rtype: Diff

        """

        if 'flow' not in spec or 'name' not in spec:
            raise ValueError(
                '"flow" and "name" keys are required in workflow spec.')
        else:
            for key in spec:
                if key not in ('flow', 'name'):
                    raise ValueError('Unknown key : "{}"'.format(key))


        name = name
        steps = []

        for step in spec['flow']:
            for i in step.keys():
                if i not in ['type', 'class', 'params']:
                    raise ValueError('Unknown key : {}'.format(i))
            try:
                step_type = step['type']
                step_class = import_string(step['class'])
            except KeyError:
                raise ValueError(
                    '"class" and "type" are required keys for each flow step')
            except ImportError:
                raise ValueError('{} does not exist'.format(step['class']))
            step_params = step.get('params', [])

            steps.append(Step(step_type, step_class, step_params))

        workflow = cls(name=name, steps=steps)

        return workflow
