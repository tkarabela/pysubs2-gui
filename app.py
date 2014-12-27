import sys
import glob
import os.path
from PyQt4.QtGui import QApplication
from PyQt4.QtCore import QTranslator
from pysubs2gui import MainWindow

if __name__ == "__main__":
    translators = {}
    for path in glob.glob("i18n/*.qm"):
        path, _ = os.path.splitext(path)
        lang = os.path.basename(path)
        translator = QTranslator()
        translator.load(path)
        translators[lang] = translator

    app = QApplication(sys.argv)
    window = MainWindow(None, app, translators)
    window.show()
    sys.exit(app.exec_())
