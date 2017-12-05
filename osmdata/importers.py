from xml.dom.minidom import parse

from .parsers import AdiffParser, FileFormatError


class ImporterError(Exception):
    pass


class AbstractImporter:  # pragma: no cover
    def run(self, path):
        """ Blocking function processing the import

        :param path: a path to fetch the resource (URL, file path…)
        :rtype: .models.Diff
        """
        raise NotImplemented


class AdiffImporter(AbstractImporter):
    """ Imports an XML adiff file into database

    See https://wiki.openstreetmap.org/wiki/Overpass_API/Augmented_Diffs
    """

    def run(self, path):
        self.path = path
        try:
            dom = parse(self.path)
        except OSError as e:
            raise ImporterError(
                "Error opening {} : {}".format(self.path, e))

        try:
            diff_parser = AdiffParser(dom.documentElement)
            diff = diff_parser.parse()
        except FileFormatError as e:
            raise ImporterError(e)

        return diff
