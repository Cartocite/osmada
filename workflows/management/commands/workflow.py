from xml.dom.minidom import parse
from django.core.management.base import BaseCommand, CommandError

from ...parsers import AdiffParser, FileFormatError


class Command(BaseCommand):
    help = 'Execute a workflow, as defined in settings'

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('workflow_name')
        parser.add_argument('input_path')

    def handle(self, adiff_path, workflow_name, *args, **options):
        dom = parse(adiff_path)

        try:
            diff_parser = AdiffParser(dom.documentElement)
            diff = diff_parser.parse()
        except FileFormatError as e:
            raise CommandError(e)

        print('Created {}'.format(diff))
