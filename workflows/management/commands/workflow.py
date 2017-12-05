import sys

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from ...models import WorkFlow


class Command(BaseCommand):
    help = 'Execute a workflow, as defined in settings, outputs on stdout'

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('workflow_name')
        parser.add_argument('input_path')

    def handle(self, workflow_name, input_path, *args, **options):
        # Build a workflow index, by name
        workflows = {
            workflow['name']: workflow for workflow in settings.WORKFLOWS
        }

        try:
            workflow_spec = workflows[workflow_name]
        except KeyError:
            raise CommandError('Workflow "{}" does not exist'.format(
                workflow_name))

        sys.stderr.write('[0] Parsing workflow "{}"...'.format(workflow_name))
        try:
            workflow = WorkFlow.from_settings(workflow_name, workflow_spec)
        except (KeyError, ImportError) as e:
            raise CommandError(
                'An error occured during workflow parsing : "{}"'.format(e))
        sys.stderr.write('OK\n')

        sys.stderr.write('[1] Running workflow…')
        sys.stderr.flush()
        workflow.run(input_path)
        sys.stderr.write('OK')
