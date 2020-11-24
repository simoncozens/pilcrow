from PyQt5.QtWidgets import *

class MyWizardPage(QWizardPage):
  def clearLayout(self):
    self._clearLayout(self.layout)

  def _clearLayout(self,layout):
    if layout is not None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                self._clearLayout(item.layout())
