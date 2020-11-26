from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from MyWizardPage import MyWizardPage
from fontmake.font_project import FontProject
from waitingspinnerwidget import QtWaitingSpinner
import os, sys, subprocess
from uuid import uuid1


def open_file(filename):
    if sys.platform == "win32":
        os.startfile(filename)
    else:
        opener = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.call([opener, filename])


class FontmakeRunner(QObject):
    signalStatus = pyqtSignal(str, int, str)

    def __init__(self, designspace_file, fontmake_args, task_id=0, parent=None):
        super(self.__class__, self).__init__(None)
        self.designspace_file = designspace_file
        self.fontmake_args = fontmake_args
        self.task_id = task_id

    @pyqtSlot()
    def start(self):
        try:
            print(self.designspace_file, self.fontmake_args)
            FontProject().run_from_designspace(
                self.designspace_file, **self.fontmake_args
            )
        except Exception as e:
            print(e)
            self.signalStatus.emit(self.task_id, 1, str(e))
        else:
            self.signalStatus.emit(self.task_id, 0, "")


class BuildFont(MyWizardPage):
    def __init__(self, parent=None):
        super(QWizardPage, self).__init__(parent)
        self.setTitle("Building the font...")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.parent = parent

    def build(self):
        # Turns out we have to build variable and static fonts separately

        if not self.buildInstances() and not self.gen_vfont.isChecked():
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setText("Nothing to do...")
            msg.setWindowTitle("I'm bored")
            msg.setStandardButtons(QMessageBox.Ok)
            return

        self.tasks = {}

        if self.gen_vfont.isChecked():
            self.buildVfont()

        if self.buildInstances():
            self.doBuildInstances()

    def buildVfont(self):
        args = {}
        args["output"] = ["variable"]
        args["output_dir"] = os.path.dirname(self.designspace_file)
        self.addGeneralArgs(args)
        self.runTask(args)

    def addGeneralArgs(self, args):
        # Grab fontmake arguments from UI
        if self.autohint.isChecked():
            args["autohint"] = ""
        args["use_production_names"] = self.production_names.isChecked()
        args["remove_overlaps"] = self.remove_overlaps.isChecked()

    def doBuildInstances(self):
        os.chdir(os.path.dirname(self.designspace_file))
        args = {}
        args["output_dir"] = None

        args["output"] = []
        if self.instance_otfs.isChecked():
            args["output"].append("otf")
        if self.instance_ttfs.isChecked():
            args["output"].append("ttf")

        args["use_mutatormath"] = self.mutator_math.isChecked()
        args["round_instances"] = self.round_instances.isChecked()
        args["masters_as_instances"] = self.masters_as_instances.isChecked()
        args["interpolate"] = True
        self.addGeneralArgs(args)
        self.runTask(args)

    def runTask(self, args):
        task_id = str(uuid1())
        worker = FontmakeRunner(self.designspace_file, args, task_id=task_id)
        worker_thread = QThread()
        worker.moveToThread(worker_thread)
        worker_thread.started.connect(worker.start)
        worker.signalStatus.connect(self.show_results)
        if not self.spinner._isSpinning:
            self.spinner.start()
        self.buildlabel.show()
        worker_thread.start()
        print("Running task ", task_id)
        print(self.tasks)
        self.tasks[task_id] = {"worker": worker, "thread": worker_thread, "done": False}

    def show_results(self, task_id, status, error_message):
        print("Task ", task_id, "completed")
        task = self.tasks[task_id]
        task["thread"].quit()
        task["result"] = status
        task["message"] = error_message
        task["done"] = True

        if any([not x["done"] for x in self.tasks.values()]):  # More to come
            return

        # We are all done!
        self.buildlabel.hide()
        self.spinner.stop()
        if all([x["result"] == 0 for x in self.tasks.values()]):
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            plural = ""
            if len(self.tasks) > 1 or (
                self.buildInstances()
                and (
                    len(self.designspace.instances) > 1
                    or self.masters_as_instances.isChecked()
                )
            ):
                plural = "s"
            msg.setText("Font%s created successfully" % plural)
            msg.setWindowTitle("Success!")
            msg.setStandardButtons(QMessageBox.Ok)
            self.saved = True
            open_file(os.path.dirname(self.designspace_file))
        else:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Variable font creation failed")
            msg.setWindowTitle("Error!")
            msg.setDetailedText(
                "\n\n".join([x["message"] for x in self.tasks.values()])
            )
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

        self.buildlabel = QLabel("Building...")
        self.layout.addWidget(self.buildlabel)
        self.buildlabel.hide()
        self.spinner = QtWaitingSpinner(self)
        self.layout.addWidget(self.spinner)

        self.optionsScroll = QScrollArea()
        self.layout.addWidget(self.optionsScroll)
        self.optionsWidget = QWidget()
        self.optionsScroll.setWidget(self.optionsWidget)
        self.optionsLayout = QVBoxLayout()
        self.optionsWidget.setLayout(self.optionsLayout)

        self.fontmake_args_variable = {"output_dir": None}
        self.fontmake_args_instances = {"output_dir": None}

        # General options
        self.general_options = QGroupBox("General Options")
        self.general_options_layout = QVBoxLayout()
        self.general_options.setLayout(self.general_options_layout)

        self.autohint = QCheckBox("Run ttfautohint", checked=True)
        self.general_options_layout.addWidget(self.autohint)

        self.production_names = QCheckBox("Use production names", checked=True)
        self.general_options_layout.addWidget(self.production_names)

        self.remove_overlaps = QCheckBox("Remove overlaps", checked=True)
        self.general_options_layout.addWidget(self.remove_overlaps)

        self.optionsLayout.addWidget(self.general_options)

        # Varfont stuff
        self.varfont_options = QGroupBox("Variable Font Options")
        self.varfont_options_layout = QVBoxLayout()
        self.varfont_options.setLayout(self.varfont_options_layout)

        self.gen_vfont = QCheckBox(
            "Create a variable font (not just named instances)", checked=True
        )
        self.varfont_options_layout.addWidget(self.gen_vfont)

        self.optionsLayout.addWidget(self.varfont_options)

        # Instance generation options
        self.instance_options = QGroupBox("Instance Options")
        self.instance_options_layout = QVBoxLayout()
        self.instance_options.setLayout(self.instance_options_layout)

        self.output_instances = QCheckBox("Output named instances", checked=False)
        if self.designspace.instances:
            self.instance_options_layout.addWidget(self.output_instances)
            self.output_instances.setChecked(True)
            self.output_instances.stateChanged.connect(self.enableInstances)

        self.masters_as_instances = QCheckBox(
            "Output masters as instances", checked=True
        )
        self.instance_options_layout.addWidget(self.masters_as_instances)
        self.masters_as_instances.stateChanged.connect(self.enableInstances)

        self.mutator_math = QCheckBox(
            "Use MutatorMath (supports extrapolation)", checked=True
        )
        self.instance_options_layout.addWidget(self.mutator_math)

        self.round_instances = QCheckBox(
            "Round instances to integers when interpolating", checked=True
        )
        self.instance_options_layout.addWidget(self.round_instances)

        self.instance_otfs = QCheckBox("Create CFF instances", checked=False)
        self.instance_ttfs = QCheckBox("Create TrueType instances", checked=False)

        self.instance_widgets = [
            self.mutator_math,
            self.round_instances,
            self.instance_ttfs,
            self.instance_otfs,
        ]
        self.enableInstances()

        self.instance_otfs.setChecked(False)
        self.instance_ttfs.setChecked(True)
        self.instance_options_layout.addWidget(self.instance_ttfs)
        self.instance_options_layout.addWidget(self.instance_otfs)

        self.optionsLayout.addWidget(self.instance_options)
        self.optionsScroll.setWidgetResizable(True)

        self.parent.setButtonLayout(
            [
                QWizard.Stretch,
                QWizard.BackButton,
                QWizard.CustomButton1,
                QWizard.FinishButton,
            ]
        )
        self.parent.setButtonText(QWizard.CustomButton1, "Build")
        self.parent.setOption(QWizard.HaveCustomButton1, True)
        self.parent.button(QWizard.CustomButton1).clicked.connect(self.build)

    def buildInstances(self):
        return (
            self.masters_as_instances.isChecked() or self.output_instances.isChecked()
        )

    def enableInstances(self):
        if self.buildInstances():
            for w in self.instance_widgets:
                w.setEnabled(True)
        else:
            for w in self.instance_widgets:
                w.setEnabled(False)
