import os.path


def flat_file_list(path):
    """ Parses a flat file into a list

    Considers that there is one value per line. Empty lines are ignored,
    carriage returns are stripped.

    :param path: the flat file path. If the path is relative, will be relative
                 to osmada folder
    :return: a list of str

    """

    if not os.path.isabs(path):
        path = os.path.join(os.path.dirname(__file__), path)

    wo_crlf = (i.rstrip('\n') for i in open(path).readlines())

    # filter out empty lines
    return [i for i in wo_crlf if i]
