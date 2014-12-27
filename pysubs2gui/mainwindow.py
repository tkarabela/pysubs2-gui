#!/usr/bin/env python

from __future__ import unicode_literals, division

import platform
import locale

import os.path
from PyQt4.QtGui import QMainWindow, QMessageBox, QDropEvent, QDragEnterEvent, QFileDialog
from PyQt4.QtCore import pyqtSlot
from six import text_type as _str
import pysubs2

from .ui.mainwindow import Ui_MainWindow
from .processor import Processor
from .processdialog import ProcessDialog
from .misc import ENCODINGS, UnicodeTrMixin
from .snippets import CODE_SNIPPETS

# ----------------------------------------------------------------------------------------------------------------------

class MainWindow(UnicodeTrMixin, QMainWindow, Ui_MainWindow):
    def __init__(self, parent, app, translators):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)

        self.app = app
        self.translators = translators
        self.currentTranslator = None
        self.installTranslator(locale.getdefaultlocale()[0])

        self.actionAbout.triggered.connect(self.about)
        self.actionEnglish.triggered.connect(lambda: self.installTranslator("en_US"))
        self.actionCesky.triggered.connect(lambda: self.installTranslator("cs_CZ"))

        self.removeSelectedButton.clicked.connect(self.removeSelectedInputFiles)
        self.addFilesButton.clicked.connect(self.addFiles)

        self.snippetsCombo.addItems(CODE_SNIPPETS.keys())
        self.loadSnippetButton.clicked.connect(self.loadSnippet)

        self.versionLabel.setText(_str(self.versionLabel.text()).format(python_ver=platform.python_version(),
                                                                        pysubs2_ver=pysubs2.VERSION))

        self.inputEncodingCombo.addItems(ENCODINGS)
        self.outputEncodingCombo.addItems(ENCODINGS)
        self.inputEncodingLabel.linkActivated.connect(self.showEncodingHelp)
        self.outputEncodingLabel.linkActivated.connect(self.showEncodingHelp)

        self.outputDirectoryButton.clicked.connect(self.setOutputDirectory)
        self.styleFileButton.clicked.connect(self.setStyleFile)

        self.outputFormatCombo.currentIndexChanged.connect(self.toogleOutputFramerateSpinbox)

        self.startBasicButton.clicked.connect(self.runBasic)
        self.startAdvancedButton.clicked.connect(self.runAdvanced)

        for label, fmt in [("SubStation Alpha (*.ass)", "ass"),
                           ("SubRip (*.srt)", "srt"),
                           ("MicroDVD (*.sub)", "microdvd")]:
            self.outputFormatCombo.insertItem(999, label, fmt)

        self.outputFormatCombo.setCurrentIndex(0)

    def installTranslator(self, lang):
        if self.currentTranslator:
            self.app.removeTranslator(self.currentTranslator)

        if lang in self.translators:
            self.currentTranslator = self.translators[lang]
            self.app.installTranslator(self.currentTranslator)
            self.retranslateUi(self)
        else:
            print("Error - lang", lang, "unknown!")

    def getInputPaths(self):
        return [_str(self.inputFileList.item(i).text()) for i in range(self.inputFileList.count())]

    def getOutputFormat(self):
        if self.changeFormatGroup.isChecked():
            return self.outputFormatCombo.itemData(self.outputFormatCombo.currentIndex())
        else:
            return None

    def getInputEncoding(self):
        return _str(self.inputEncodingCombo.currentText())

    def runBasic(self):
        input_encoding = self.getInputEncoding()

        if self.changeEncodingGroup.isChecked():
            output_encoding = self.outputEncodingCombo.currentText()
        else:
            output_encoding = input_encoding

        processor = Processor(input_encoding, output_encoding)

        if self.shiftTimesGroup.isChecked():
            delta = pysubs2.time.timestamp_to_ms(pysubs2.time.TIMESTAMP.match(self.shiftTimesEdit.text()).groups())
            delta *= (-1)**self.shiftTimesBackwardRadio.isChecked()
            processor.add_step(lambda subs: subs.shift(ms=delta))
        if self.transformFramerateGroup.isChecked():
            in_fps = self.transformFramerateInputSpinbox.value()
            out_fps = self.transformFramerateOutputSpinbox.value()
            processor.add_step(lambda subs: subs.transform_framerate(in_fps, out_fps))
        if self.importStylesGroup.isChecked():
            raise NotImplementedError("XXX")
        if self.useOutputDirectoryRadio.isChecked():
            processor.output_dir = self.outputDirectoryEdit.text()
        if self.changeFormatGroup.isChecked():
            processor.output_format = self.getOutputFormat()
            processor.output_fps = self.outputEncodingFramerateSpinbox.value()

        ProcessDialog(self, processor, self.getInputPaths()).exec_()

    def runAdvanced(self):
        self.runBasic()

    @pyqtSlot(QDropEvent)
    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = _str(url.toLocalFile())
            if os.path.isfile(path):
                self.inputFileList.addItem(path)

    @pyqtSlot(QDragEnterEvent)
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()

    def setOutputDirectory(self):
        dirname = QFileDialog.getExistingDirectory(self,
                                                   caption=self.tr("Select Output Directory"),
                                                   options=QFileDialog.ShowDirsOnly)

        self.outputDirectoryEdit.setText(dirname)

    def setStyleFile(self):
        filename, _ = QFileDialog.getOpenFileName(self,
                                                  caption=self.tr("Select SubStation File With Styles"),
                                                  filter=self.tr("SubStation files (*.ass *.ssa);;All files (*.*)"))

        self.styleFileEdit.setText(filename)

    def toogleOutputFramerateSpinbox(self):
        enabled = "MicroDVD" in self.outputFormatCombo.currentText()
        self.outputEncodingFramerateSpinbox.setEnabled(enabled)

    def loadSnippet(self):
        snippet_name = self.snippetsCombo.currentText()
        snippet = CODE_SNIPPETS[snippet_name]
        self.snippetEdit.setText(snippet)

    def removeSelectedInputFiles(self):
        for item in self.inputFileList.selectedItems():
            self.inputFileList.takeItem(self.inputFileList.indexFromItem(item).row())

    def addFiles(self):
        filenames, _ = QFileDialog.getOpenFileNames(self,
                                                    caption=self.tr("Select Subtitle Files"),
                                                    filter=self.tr("Subtitle files (*.ass *.ssa *.srt *.sub);;All files (*.*)"))

        self.inputFileList.addItems(filenames)

    def showEncodingHelp(self):
        QMessageBox.information(self, self.tr("Encoding Help"), self.tr("XXX"))

    def about(self):
        QMessageBox.about(self, self.tr("About pysubs2-gui"), self.tr("XXX"))
