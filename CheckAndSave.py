from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from MyWizardPage import MyWizardPage
from fontTools.designspaceLib import AxisDescriptor
from PyQt5.QtCore import Qt, pyqtSlot, QPoint
from PyQt5 import QtGui
from fontTools.varLib.interpolatable import test
from fontTools.ufoLib import UFOReader
from os.path import basename, dirname, commonpath
from waitingspinnerwidget import QtWaitingSpinner

from enum import IntEnum


class Status(IntEnum):
    NONE = -1
    OK = 0
    WARN = 1
    ERROR = 2


class TestRunner(QObject):
    signalStatus = pyqtSignal(object)

    def __init__(self, glyphsets, names, parent=None):
        super(self.__class__, self).__init__(parent)
        self.glyphsets = glyphsets
        self.names = names

    @pyqtSlot()
    def start(self):
        print("Test called")
        self.problems = test(self.glyphsets, names=self.names)
        print("Test done")
        self.signalStatus.emit(self.problems)


class CheckAndSave(MyWizardPage):
    def __init__(self, parent=None):
        super(QWizardPage, self).__init__(parent)
        self.setTitle("Checking it's OK...")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.parent = parent
        self.status = Status.NONE

    def initializePage(self):
        self.clearLayout()
        self.designspace = self.parent.designspace
        fonts = [UFOReader(x.path) for x in self.designspace.sources]
        names = [
            basename(x.filename).rsplit(".", 1)[0] for x in self.designspace.sources
        ]
        glyphsets = [font.getGlyphSet() for font in fonts]

        self.layout.addWidget(QLabel("Checking for compatibility errors..."))
        spinner = QtWaitingSpinner(self)
        self.layout.addWidget(spinner)

        self.worker = TestRunner(glyphsets, names)
        self.worker_thread = QThread()
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker.start)
        self.worker.signalStatus.connect(self.show_results)
        spinner.start()
        self.worker_thread.start()
        self.parent.setButtonLayout(
            [
                QWizard.Stretch,
                QWizard.BackButton,
                QWizard.CustomButton1,
                QWizard.NextButton,
            ]
        )

        self.parent.setButtonText(QWizard.CustomButton1, "Save")
        self.parent.setOption(QWizard.HaveCustomButton1, True)
        self.parent.button(QWizard.CustomButton1).clicked.connect(self.saveDesignspace)
        self.parent.button(QWizard.CustomButton1).setEnabled(False)

    def show_results(self, problems):
        self.clearLayout()
        self.problems = problems
        self.status = self.cleanProblems()
        if not self.problems:
            self.layout.addWidget(QLabel("Everything looks good! Let's save it now..."))
            self.parent.button(QWizard.CustomButton1).setEnabled(True)

        else:
            if self.status == Status.WARN:
                self.layout.addWidget(
                    QLabel("It'll work, but there were a few warnings")
                )
            elif self.status == Status.ERROR:
                self.layout.addWidget(QLabel("There were some errors you need to fix"))

            self.sourcesScroll = QScrollArea()
            self.problemsWidget = QTableWidget()
            self.problemsWidget.setColumnCount(3)
            self.problemsWidget.setHorizontalHeaderLabels(
                ["Glyph", "Status", "Message"]
            )
            self.sourcesScroll.setSizePolicy(
                QSizePolicy.Expanding, QSizePolicy.Expanding
            )
            self.problemsWidget.horizontalHeader().setStretchLastSection(True)
            for k in self.problems.keys():
                for v in self.problems[k]:
                    rowPosition = self.problemsWidget.rowCount()
                    self.problemsWidget.insertRow(rowPosition)
                    self.problemsWidget.setItem(rowPosition, 0, QTableWidgetItem(k))
                    self.problemsWidget.setItem(
                        rowPosition, 1, QTableWidgetItem(v["status"])
                    )
                    self.problemsWidget.setItem(
                        rowPosition, 2, QTableWidgetItem(v["message"])
                    )
            self.sourcesScroll.setWidget(self.problemsWidget)
            self.sourcesScroll.setWidgetResizable(True)
            self.layout.addWidget(self.sourcesScroll)

            if self.status == Status.WARN:
                self.parent.button(QWizard.CustomButton1).setEnabled(True)
        self.completeChanged.emit()

    def saveDesignspace(self):
        if not self.parent.designspace_file:
            filename = QFileDialog.getSaveFileName(
                self,
                "Save File",
                directory=commonpath(
                    [dirname(x.filename) for x in self.designspace.sources]
                ),
                filter="Designspace files (*.designspace)",
            )
            if not filename:
                return
            self.parent.designspace_file = filename[0]
        self.parent.dirty = False
        self.designspace.write(self.parent.designspace_file)
        self.completeChanged.emit()

    def isComplete(self):
        print(self.status, self.parent.dirty)
        return (
            self.status == Status.OK or self.status == Status.WARN
        ) and not self.parent.dirty

    def cleanProblems(self):
        status = Status.OK
        if not self.problems:
          return status
        keys = list(self.problems.keys())
        for (
            k
        ) in (
            keys
        ):  # We do this malarkey because we can't alter an OrderDict while iterating
            newproblems = []
            for p in self.problems[k]:
                if p["type"] == "node_count":
                    status = Status.ERROR
                    p["status"] = "ERROR"
                    p[
                        "message"
                    ] = "Node count differs in path %i: %i in %s, %i in %s" % (
                        p["path"],
                        p["value_1"],
                        p["master_1"],
                        p["value_2"],
                        p["master_2"],
                    )
                if p["type"] == "path_count":
                    status = Status.ERROR
                    p["status"] = "ERROR"
                    p["message"] = "Path count differs: %i in %s, %i in %s" % (
                        p["value_1"],
                        p["master_1"],
                        p["value_2"],
                        p["master_2"],
                    )
                if p["type"] == "missing":
                    status = Status.ERROR
                    p["status"] = "ERROR"
                    p["message"] = "Glyph was missing in master %s" % p["master"]
                if p["type"] == "node_incompatibility":
                    status = Status.ERROR
                    p["status"] = "ERROR"
                    p[
                        "message"
                    ] = "Node %o incompatible in path %i: %s in %s, %s in %s" % (
                        p["node"],
                        p["path"],
                        p["value_1"],
                        p["master_1"],
                        p["value_2"],
                        p["master_2"],
                    )
                if p["type"] == "contour_order":
                    status = max(status, Status.WARN)
                    p["status"] = "WARN"
                    p["message"] = "Contour order differs: %s in %s, %s in %s" % (
                        p["value_1"],
                        p["master_1"],
                        p["value_2"],
                        p["master_2"],
                    )
                if p["type"] == "high_cost":
                    continue
                    # status = max(status, Status.WARN)
                    # p[
                    #     "message"
                    # ] = "Interpolation has high cost: cost of %s to %s = %i, threshold %i" % (
                    #     p["master_1"],
                    #     p["master_2"],
                    #     p["value_1"],
                    #     p["value_2"],
                    # )

                newproblems.append(p)
            if not newproblems:
                del self.problems[k]
            else:
                self.problems[k] = newproblems
        return status
