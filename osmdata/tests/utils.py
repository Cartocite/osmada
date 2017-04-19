import os
from xml.dom.minidom import parse, parseString

def get_test_file_path(filename):
    """ Build full absolute path from test_data file name

    :param filename: bare file name (ex: "test_file.osm")
    :returns: absolute path to the file
    """

    return os.path.join(os.path.abspath(os.path.dirname(__file__)), 'test_data', filename)

def parse_test_data(filename):
    return parse(get_test_file_path(filename))

def minidom_parse_fragment(fragment):
    # Just so that minidom is happy with a full document
    doc_str = '<?xml version="1.0" encoding="UTF-8"?>\n{}'.format(fragment)
    return parseString(doc_str).childNodes[0]
