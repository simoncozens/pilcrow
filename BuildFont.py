from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from MyWizardPage import MyWizardPage
from fontmake.font_project import FontProject
from waitingspinnerwidget import QtWaitingSpinner
import os, sys, subprocess

def open_file(filename):
    if sys.platform == "win32":
        os.startfile(filename)
    else:
        opener = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.call([opener, filename])

class FontmakeRunner(QObject):
    signalStatus = pyqtSignal(int, str)

    def __init__(self, designspace_file, fontmake_args, parent=None):
        super(self.__class__, self).__init__(None)
        self.designspace_file = designspace_file
        self.fontmake_args = fontmake_args

    @pyqtSlot()
    def start(self):
        try:
            print(self.designspace_file, self.fontmake_args)
            FontProject().run_from_designspace(self.designspace_file, **self.fontmake_args)
        except Exception as e:
            print(e)
            self.signalStatus.emit(1, str(e))
        else:
            print("OK")
            self.signalStatus.emit(0, "")


class BuildFont(MyWizardPage):
    def __init__(self, parent=None):
        super(QWizardPage, self).__init__(parent)
        self.setTitle("Building the font...")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.parent = parent

    def build(self):
        self.fontmake_args["output"] = []
        if self.gen_vfont.isChecked():
            self.fontmake_args["output"].append("variable")
        if len(self.designspace.instances):
            self.fontmake_args["output"].append("otf")
            self.fontmake_args["output"].append("ttf")

        self.fontmake_args["output_dir"] = os.path.dirname(self.designspace_file)
        if self.autohint.isChecked():
            self.fontmake_args["autohint"] = True

        self.buildlabel = QLabel("Building...")
        self.layout.addWidget(self.buildlabel)
        self.spinner = QtWaitingSpinner(self)
        self.layout.addWidget(self.spinner)

        self.worker = FontmakeRunner(self.designspace_file, self.fontmake_args)
        self.worker_thread = QThread()
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker.start)
        self.worker.signalStatus.connect(self.show_results)
        self.spinner.start()
        self.worker_thread.start()

    def show_results(self, status, error_message):
        self.buildlabel.hide()
        self.spinner.stop()
        if status == 0:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setText("Variable font created successfully")
            msg.setWindowTitle("Success!")
            msg.setStandardButtons(QMessageBox.Ok)
            self.saved = True
            if self.fontmake_args["output_dir"]:
               open_file(self.fontmake_args["output_dir"])
        else:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Variable font creation failed")
            msg.setWindowTitle("Error!")
            msg.setDetailedText(error_message)
            msg.setStandardButtons(QMessageBox.Ok)
            self.saved = False
        msg.exec_()
        self.completeChanged.emit()

    def isComplete(self):
        return self.saved


    def initializePage(self):
        self.clearLayout()
        self.designspace_file = self.parent.designspace_file
        self.designspace = self.parent.designspace
        self.saved = False

        self.fontmake_args = {'output_dir': None}
        self.autohint = QCheckBox("Run ttfautohint", checked=True)
        self.layout.addWidget(self.autohint)

        self.gen_vfont = QCheckBox("Create a variable font (not just named instances)", checked=True)
        if self.designspace.instances:
            self.layout.addWidget(self.gen_vfont)

        self.parent.setButtonLayout([
            QWizard.Stretch,QWizard.BackButton,QWizard.CustomButton1,QWizard.FinishButton
        ])
        self.parent.setButtonText(QWizard.CustomButton1, "Build")
        self.parent.setOption(QWizard.HaveCustomButton1, True)
        self.parent.button(QWizard.CustomButton1).clicked.connect(self.build)
