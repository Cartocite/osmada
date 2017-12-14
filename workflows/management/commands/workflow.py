import logging

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from ...models import WorkFlow


logger = logging.getLogger(__name__)


class LoggedCommandError(CommandError):
    def __init__(self, msg, *args, **kwargs):
        super().__init__(msg, *args, **kwargs)
        logger.error(self)


class Command(BaseCommand):
    help = 'Execute a workflow, as defined in settings, outputs on stdout'

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('workflow_name')
        parser.add_argument('input_path')
        parser.add_argument(
            '--output-paths', nargs="*", default=[],
            help="The path of the output file(s) to import, if you omit that" +
            "argument the output(s) will be printed on standard output")

    def _validate_output_paths(self, workflow, output_paths):
        outputs = [step for step in workflow.steps
                   if step.type == step.STEP_EXPORT]
        # If nothing is provided, let's bind all outputs to stdout
        if output_paths == []:
            output_paths = ['/dev/stdout' for i in outputs]
        if len(outputs) != len(output_paths):
            raise LoggedCommandError(
                'You must provide exactly one output path per Exporter in your workflow')
        return output_paths

    def handle(self, workflow_name, input_path, output_paths, *args, **options):
        # Build a workflow index, by name
        workflows = {
            workflow['name']: workflow for workflow in settings.WORKFLOWS
        }

        try:
            workflow_spec = workflows[workflow_name]
        except KeyError:
            raise LoggedCommandError('Workflow "{}" does not exist'.format(
                workflow_name))

        logger.debug('[0] Parsing workflow "{}"...'.format(workflow_name))
        try:
            workflow = WorkFlow.from_settings(workflow_name, workflow_spec)
        except (KeyError, ImportError) as e:
            raise LoggedCommandError(
                'An error occured during workflow parsing : "{}"'.format(e))
        else:
            logger.debug('[0] OK\n')

        output_paths = self._validate_output_paths(workflow, output_paths)

        logger.info('[1] Running workflow {}…'.format(workflow_name))
        workflow.run(input_path, output_paths)
        logger.info('[1] OK')
