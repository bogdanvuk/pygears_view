from PySide2 import QtCore
from PySide2 import QtWidgets
from pygears.conf import Inject, reg_inject
from .main_window import register_prefix
from .actions import shortcut, Interactive

register_prefix(None, (QtCore.Qt.Key_Space, QtCore.Qt.Key_B), 'buffers')


class BufferCompleter(QtWidgets.QCompleter):
    @reg_inject
    def __init__(self, layout=Inject('gearbox/layout')):
        super().__init__()

        self.layout = layout
        self.setCompletionMode(self.PopupCompletion)
        self.setCaseSensitivity(QtCore.Qt.CaseInsensitive)

        model = QtCore.QStringListModel()
        completion_list = [b.name for b in layout.buffers]
        model.setStringList(completion_list)
        self.setModel(model)

    def get_result(self, text):
        return self.layout.get_buffer_by_name(text)


@shortcut(None, (QtCore.Qt.Key_Space, QtCore.Qt.Key_B, QtCore.Qt.Key_B),
          'select')
@reg_inject
def select_buffer(
        buff=Interactive('buffer: ', BufferCompleter),
        layout=Inject('gearbox/layout')):

    if buff is not None:
        layout.current_window.place_buffer(buff)
