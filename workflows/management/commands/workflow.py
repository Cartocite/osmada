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
        try:
            workflow_spec = settings.WORKFLOWS[workflow_name]
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

        sys.stderr.write('[1] Importing "{}"...'.format(input_path))
        sys.stderr.flush()
        diff = workflow.run_import(input_path)
        sys.stderr.write('OK, imported as "{}"\n'.format(diff))

        sys.stderr.write('[2] Computing data for each <action>')
        sys.stderr.flush()
        workflow.make_action_reports()
        sys.stderr.write('OK\n')

        sys.stderr.write('[3] Patching data…\n')
        for patch_description in workflow.apply_data_patches():
            sys.stderr.write('  - Applying {}\n'.format(patch_description))

        sys.stderr.write('OK\n')

        sys.stderr.write('[4] Filtering ({} filters)...\n'.format(
            len(workflow.filters)))

        # FIXME: a count() on each loop run is good for debug but may be
        # bad for performance.
        initial_count = workflow.diff.actions.count()
        for _filter, qs in workflow.iter_filters():
            sys.stderr.write('  - {} ran, {}/{} kept\n'.format(
                _filter.__class__.__name__, qs.count(), initial_count))

        sys.stderr.write('[5] Writing output...\n')

        print(workflow.write_output())
