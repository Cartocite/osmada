from xml.dom.minidom import parse

from .parsers import AdiffParser, FileFormatError

class ImporterError(Exception):
    pass

class AbstractImporter:  # pragma: no cover
    def __init__(self, path):
        """
        :param path: a path to fetch the resource (URL, file path…)
        """
        raise NotImplemented

    def run(self):
        """ Blocking function processing the import
        :rtype: .models.Diff
        """
        raise NotImplemented


class AdiffImporter(AbstractImporter):
    """ Imports an XML adiff file into database

    See https://wiki.openstreetmap.org/wiki/Overpass_API/Augmented_Diffs
    """

    def __init__(self, path):
        self.path = path

    def run(self):
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
