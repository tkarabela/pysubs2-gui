#!/usr/bin/env python

import os

from PyQt4.QtGui import QDialog, QListWidgetItem, QColor
from PyQt4.QtCore import QThread, pyqtSignal, pyqtSlot
import errno
import pysubs2

from .ui.processdialog import Ui_ProcessDialog
from .misc import scroll_to_bottom, UnicodeTrMixin

# ----------------------------------------------------------------------------------------------------------------------

class Worker(QThread):
    fileProcessed = pyqtSignal(unicode, object) # filename, exception-or-output-filename
    startedProcessingFile = pyqtSignal(unicode) # filename

    def __init__(self, processor, input_files):
        QThread.__init__(self)
        self.running = True
        self.input_files = input_files
        self.processor = processor

    @pyqtSlot()
    def stopProcessing(self):
        self.running = False

    def run(self):
        for path in self.input_files:
            if not self.running:
                return

            self.startedProcessingFile.emit(path)
            try:
                rv = self.processor.process_path(path)
            except Exception as exc:
                rv = exc

            self.fileProcessed.emit(path, rv)

# ----------------------------------------------------------------------------------------------------------------------

class ProcessDialog(UnicodeTrMixin, QDialog, Ui_ProcessDialog):
    def __init__(self, parent=None, processor=None, input_paths=None):
        super(ProcessDialog, self).__init__(parent)
        self.setupUi(self)

        self.n = len(input_paths)
        self.processed = 0
        self.processed_ok = 0

        self.progressBar.setMaximum(self.n)
        self.progressBar.setValue(0)

        self.processor = processor
        self.worker = Worker(processor, input_paths)

        self.button.clicked.connect(self.worker.stopProcessing)
        self.worker.startedProcessingFile.connect(self.startedProcessingFile)
        self.worker.fileProcessed.connect(self.fileProcessed)
        self.worker.finished.connect(self.finishedProcessing)

        self.worker.start()

    def startedProcessingFile(self, path):
        self.logList.addItem(self.tr("processing %s...") % path)
        scroll_to_bottom(self.logList)

    def fileProcessed(self, path, rv):
        if isinstance(rv, Exception):
            try:
                raise rv
            except IOError as exc:
                if exc.errno == errno.ENOENT:
                    msg = "ERROR: File doesn't exist"
                else:
                    msg = "ERROR: %s" % os.strerror(exc.errno)
            except UnicodeDecodeError:
                msg = "ERROR: Cannot read file using %s encoding" % self.processor.input_encoding
            except UnicodeEncodeError:
                msg = "ERROR: Cannot write file using %s encoding (try setting output encoding to UTF-8)" % self.processor.output_encoding
            except pysubs2.FormatAutodetectionError:
                msg = "ERROR: Unknown subtitle format (malformed file?)"
            except Exception as exc:
                msg = "ERROR: %r" % exc
        else:
            msg = None
            self.processed_ok += 1

        self.processed += 1
        self.progressBar.setValue(self.progressBar.value() + 1)

        if msg:
            item = QListWidgetItem(msg)
            item.setForeground(QColor("darkred" if msg.startswith("ERROR") else "darkgreen"))
            self.logList.addItem(item)
            scroll_to_bottom(self.logList)

    def finishedProcessing(self):
        self.button.clicked.disconnect(self.worker.stopProcessing)
        self.button.setText("OK")
        self.button.clicked.connect(self.accept)

        self.logList.addItem("")

        skipped = self.n - self.processed
        errors = self.n - self.processed_ok - skipped

        if errors == 0 and skipped == 0:
            self.logList.addItem(self.tr("All done."))
        else:
            self.logList.addItem(self.tr("Finished (%d done, %d failed, %d skipped).") % (self.processed_ok, errors, skipped))

        scroll_to_bottom(self.logList)
