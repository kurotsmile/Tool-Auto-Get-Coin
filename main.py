
import sys
from datetime import datetime, timedelta
import subprocess
from PyQt5.QtCore import QThread
from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton,QLineEdit, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QCheckBox, QStyledItemDelegate, QHBoxLayout, QComboBox

from config import CONFIG
from log_updater import LogUpdater, DeviceTableUpdater
from worker import Worker


class CenterCheckBoxDelegate(QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        if index.column() == 0:
            option.displayAlignment = Qt.AlignCenter

class CenterCheckBox(QCheckBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("QCheckBox::indicator {"
                           "    subcontrol-origin: padding;"
                           "    subcontrol-position: center;"
                           "}")

class MyMainWindow(QMainWindow):
    update_table_signal = pyqtSignal(str, list)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Shopee Coin Auto Claimer - nospk")
        self.workers = {}
        self.stop_button = False
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()
        main_widget.setLayout(layout)

        title_label = QLabel("Shopee Coin Auto Claimer")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title_label)

        self.table_widget = QTableWidget()
        self.table_widget.setItemDelegateForColumn(0, CenterCheckBoxDelegate())
        self.table_widget.setColumnCount(7)
        self.table_widget.setHorizontalHeaderLabels(
            ['Select', 'Device', 'Total Coin', 'Claim Counts', 'Status', 'Goal achieved', 'Time Stop'])
        self.table_widget.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_widget.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_widget.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table_widget)
        
        # Create a QHBoxLayout for the row
        row_layout = QHBoxLayout()

        # Create a checkbox
        self.checkbox_time = QCheckBox("Set Time")
        row_layout.addWidget(self.checkbox_time)

        # Create a combobox
        self.comboBox = QComboBox()
        for i in range(1, 13):
            self.comboBox.addItem(str(i))
        row_layout.addWidget(self.comboBox)

        # Create a label
        self.label = QLabel("Hours")
        row_layout.addWidget(self.label)

        # Create a button
        self.button = QPushButton("Update")
        self.button.clicked.connect(self.update_time_off)
        row_layout.addWidget(self.button)

        # Add the row layout to the main layout
        layout.addLayout(row_layout)

        
        util_layout = QHBoxLayout()
        
        self.select_all_button = QPushButton("Select All")
        self.select_all_button.clicked.connect(self.select_all)

        self.unselect_all_button = QPushButton("Unselect All")
        self.unselect_all_button.clicked.connect(self.select_all)

        util_layout.addWidget(self.select_all_button)
        util_layout.addWidget(self.unselect_all_button)
        layout.addLayout(util_layout)

        gold_layout=QHBoxLayout()
        self.label_chitieu = QLabel('Chỉ tiêu:')
        self.gold_edit=QLineEdit()
        self.gold_edit.setPlaceholderText('Nhập chỉ tiêu số xu đủ để dừng ở đây...')
        self.gold_edit.setText("100")
        gold_layout.addWidget(self.label_chitieu);
        gold_layout.addWidget(self.gold_edit)
        layout.addLayout(gold_layout)

        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_action)
        layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_action)
        layout.addWidget(self.stop_button)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_table)
        layout.addWidget(self.refresh_button)

        self.refresh_table()

    def refresh_table(self):
        self.table_widget.setRowCount(0)
        devices = self.get_devices_list()
        for device in devices:
            self.add_row(True, device, 0, 0, 'Ready',12)

    def add_row(self, is_select, device, total_coin, claim_count, status,chitieu):
        row_position = self.table_widget.rowCount()
        self.table_widget.insertRow(row_position)

        checkbox = CenterCheckBox()
        checkbox.setChecked(is_select)
        self.table_widget.setCellWidget(row_position, 0, checkbox)

        device_item = QTableWidgetItem(device)
        self.table_widget.setItem(row_position, 1, device_item)

        total_coin_item = QTableWidgetItem(str(total_coin))
        self.table_widget.setItem(row_position, 2, total_coin_item)
        
        claim_count_item = QTableWidgetItem(str(claim_count))
        self.table_widget.setItem(row_position, 3, claim_count_item)

        status_item = QTableWidgetItem(status)
        self.table_widget.setItem(row_position, 4, status_item)
        
        Goal = QTableWidgetItem(chitieu)
        self.table_widget.setItem(row_position, 5, Goal)

        time_off = QTableWidgetItem(None)
        self.table_widget.setItem(row_position, 6, time_off)


    def get_devices_list(self):
        output = subprocess.run(
            f'{CONFIG.ADB_PATH} devices', shell=True, capture_output=True, text=True).stdout.strip()

        lines = output.split('\n')
        devices = [line.split('\t')[0]
                   for line in lines[1:] if 'device' in line]
        return devices

    def update_status_by_device(self, device, data):
        for row in range(self.table_widget.rowCount()):
            device_item = self.table_widget.item(row, 1)
            total_coin, claim_count, stop_time, status = data
            if device_item.text() == device:
                if total_coin is not None:
                    self.table_widget.item(row, 2).setText(str(total_coin))
                    self.table_widget.item(row, 3).setText(str(claim_count))
                if stop_time is not None:
                    self.table_widget.item(row,6).setText(str(stop_time))
                else:
                    self.table_widget.setItem(row, 6, QTableWidgetItem(None))
                self.table_widget.item(row, 4).setText(status)
                self.table_widget.item(row,5).setText(self.gold_edit.text())
                break

    def send_data_to_table(self, device, data):
        device_table_updater = DeviceTableUpdater(device, data, self)
        device_table_updater.device_table_updated.connect(
            self.update_status_by_device)
        device_table_updater.start()

    def select_all(self):
        sender = self.sender()
        for row in range(self.table_widget.rowCount()):
            checkbox = self.table_widget.cellWidget(row, 0)
            if sender == self.select_all_button:
                checkbox.setChecked(True)
            else:
                checkbox.setChecked(False)
    
    def final_action(self, device, data):
        self.update_table_signal.emit(device, data)
    def start_action(self):
        for row in range(self.table_widget.rowCount()):
            checkbox = self.table_widget.cellWidget(row, 0)
            if checkbox.isChecked():
                device_item = self.table_widget.item(row, 1)
                total_coin = self.table_widget.item(row, 2).text()
                claim_count = self.table_widget.item(row, 3).text()
                stop_time = self.table_widget.item(row, 6).text()
                chitieu = self.table_widget.item(row, 5).text()
                device = device_item.text()
                if device not in self.workers:
                    worker = Worker(self.update_table_signal, device, total_coin, claim_count, stop_time,chitieu)
                    thread = QThread()
                    worker.moveToThread(thread)

                    worker.update_table_signal.connect(self.send_data_to_table)
                    worker.finished.connect(lambda device, data: self.final_action(device, data))
                    worker.error.connect(lambda device, data: self.restart_task(device, data))
                    thread.started.connect(worker.run_task)
                    self.workers[device] = {"worker": worker, "thread": thread}

                    # Bắt đầu thread mới
                    thread.start()
    def stop_action(self):
        self.devices_to_stop = []

        for row in range(self.table_widget.rowCount()):
            checkbox = self.table_widget.cellWidget(row, 0)
            if checkbox.isChecked():
                device_item = self.table_widget.item(row, 1)
                self.devices_to_stop.append(device_item.text())

        for device in self.devices_to_stop:
            if device in self.workers:
               
                worker_info = self.workers[device]
                worker_info["worker"].stop()
                worker_info["thread"].quit()
                worker_info["thread"].wait()
                del worker_info["worker"]
                del worker_info["thread"]
                del self.workers[device]
                
    def update_time_off(self):
        if self.checkbox_time.isChecked():
            current_time = datetime.now()
            # Thêm 2 tiếng vào thời gian hiện tại
            selected_value = int(self.comboBox.currentText())
            new_time = current_time + timedelta(hours=selected_value)   
            formatted_time = new_time.strftime('%Y-%m-%d %H:%M:%S')     
            for row in range(self.table_widget.rowCount()):
                checkbox = self.table_widget.cellWidget(row, 0)
                if checkbox.isChecked():
                    device = self.table_widget.item(row, 1).text()
                    if device in self.workers:
                        worker_info = self.workers[device]
                        worker_info["worker"].stop_time(True,str(formatted_time))      
        else:
            for row in range(self.table_widget.rowCount()):
                checkbox = self.table_widget.cellWidget(row, 0)
                if checkbox.isChecked():
                    device = self.table_widget.item(row, 1).text()
                    if device in self.workers:
                        worker_info = self.workers[device]
                        worker_info["worker"].stop_time(False,None)  
                    
    def restart_task(self, device, data):
        print(device)
        if device in self.workers:
            print('Restarting thread for device:', device)
            worker_info = self.workers[device]
            # Dừng thread hiện tại
            worker_info["worker"].stop()
            worker_info["thread"].quit()
            worker_info["thread"].wait()

            # Xóa worker và thread hiện tại
            del worker_info["worker"]
            del worker_info["thread"]
            total_coin, claim_count, stop_time = data
            # Tạo worker mới
            worker = Worker(self.update_table_signal, device, total_coin, claim_count, stop_time)
            thread = QThread()
            worker.moveToThread(thread)

            worker.update_table_signal.connect(self.send_data_to_table)
            worker.finished.connect(lambda device, data: self.final_action(device, data))
            worker.error.connect(lambda device, data: self.restart_task(device, data))
            thread.started.connect(worker.run_task)

            # Lưu trữ thông tin về worker và thread mới
            self.workers[device] = {"worker": worker, "thread": thread}

            # Bắt đầu thread mới
            thread.start()
                
    
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MyMainWindow()
    window.setGeometry(100, 100, 850, 600)
    window.show()
    sys.exit(app.exec_())