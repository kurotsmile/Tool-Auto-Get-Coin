from PyQt5.QtCore import QThread, pyqtSignal


class LogUpdater(QThread):
    log_updated = pyqtSignal(str)

    def __init__(self, messages, parent=None):
        super().__init__(parent)
        self.messages = messages

    def run(self):
        self.log_updated.emit(self.messages)


class DeviceTableUpdater(QThread):
    device_table_updated = pyqtSignal(str, list)

    def __init__(self, phone_serial, data, parent=None):
        super().__init__(parent)
        self.phone_serial = phone_serial
        self.data = data

    def run(self):
        self.device_table_updated.emit(self.phone_serial, self.data)
