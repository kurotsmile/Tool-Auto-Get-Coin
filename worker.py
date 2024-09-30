import time


from PyQt5.QtCore import QObject, pyqtSignal
from helper import Shopee



class Worker(QObject):
    finished = pyqtSignal(str, list)
    error = pyqtSignal(str, list)
 
    def __init__(self, update_table_signal, phone_serial, total_coin, claim_count, stop_time,chitieu):
        super().__init__()
        self.phone_serial = phone_serial
        self.update_table_signal = update_table_signal
        self.shopee = Shopee(self.phone_serial, self.update_table_signal, total_coin, claim_count, stop_time,chitieu)
    def stop(self):
        self.shopee.update_stop_status(True)  
    def stop_time(self, stop, time):
        self.shopee.update_stop_time(stop, time)
    def run_task(self): 
        try:
            self.shopee.update_stop_status(False) 
            self.shopee.claim_coin()
            self.finished.emit(self.phone_serial, [self.shopee.total_coin_claimed, self.shopee.claim_counts, self.shopee.stop_time, 'Stopped'])
        except Exception as e:
            print(e)
            self.finished.emit(self.phone_serial, [self.shopee.total_coin_claimed, self.shopee.claim_counts, self.shopee.stop_time, 'Stopped'])
            if not self.shopee.is_stop:
                # self.update_table_signal.emit(phone_serial, [0, f'{e}'])
                self.update_table_signal.emit(self.phone_serial, [self.shopee.total_coin_claimed, self.shopee.claim_counts, self.shopee.stop_time, 'Error, waiting 10s to retry...'])
                time.sleep(10)
                self.error.emit(self.phone_serial, [self.shopee.total_coin_claimed, self.shopee.claim_counts, self.shopee.stop_time])
        

