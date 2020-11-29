from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt

class MyWizardPage(QWizardPage):
  disableEnter = False

  def keyPressEvent(self, event):
    if self.disableEnter and (event.key() == Qt.Key_Enter or Qt.Key_Return):
      event.accept()
      return
    super().keyPressEvent(event)

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
