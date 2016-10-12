from xml.dom.minidom import parse
from django.core.management.base import BaseCommand, CommandError

from ...parsers import AdiffParser, FileFormatError

DEBUG = True


class Command(BaseCommand):
    help = 'Import an adiff XML file into the database'

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('adiff_path')

    def handle(self, adiff_path, *args, **options):
        dom = parse(adiff_path)

        try:
            diff_parser = AdiffParser(dom.documentElement)
            diff = diff_parser.parse()
        except FileFormatError as e:
            raise CommandError(e)

        print('Created {}'.format(diff))
