import codecs
from six import text_type
from PyQt4.QtCore import QObject

# ----------------------------------------------------------------------------------------------------------------------

def is_valid_encoding(s):
    """
    >>> is_valid_encoding("UTF-8")
    True
    >>> is_valid_encoding("xyz")
    False
    """
    try:
        codecs.lookup(s)
        return True
    except LookupError:
        return False


ENCODINGS = ["UTF-8"] + \
            ["Windows-125%d" % i for i in range(9)] + \
            ["ISO-8859-%d" % i for i in range(1, 17) if i not in (11,12)]


def scroll_to_bottom(listWidget):
    listWidget.scrollToItem(listWidget.item(listWidget.count() - 1))

class UnicodeTrMixin(object):
    def tr(self, *args):
        return text_type(QObject.tr(self, *args))
