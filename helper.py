import re
import time
#import ctypes
import random
#import base64
#import logging
#import threading
import uiautomator2 as u2
import subprocess
from xpaths import XPATHS
from config import CONFIG
from datetime import datetime

#logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')


class Shopee:
    def __init__(self, device_serial: str, update_signal, total_coin, claim_count, stop_time,chitieu) -> None:
        self.device_serial = device_serial
        self.update_signal = update_signal
        self.d = u2.connect(device_serial)
        self.total_coin_claimed = int(total_coin)
        self.is_stop = False
        self.status = 0
        self.claim_counts = int(claim_count)
        self.stop_time = stop_time
        self.captcha_count=0
        self.chitieu=chitieu
        
    def update_stop_time(self, stop, time):
        if stop:
            self.stop_time = time
            self.update_signal.emit(self.device_serial, [self.total_coin_claimed, self.claim_counts, self.stop_time, "Set time off"])
        else:
            self.stop_time = None
            self.update_signal.emit(self.device_serial, [self.total_coin_claimed, self.claim_counts, self.stop_time, "Set time off"])
    def update_stop_status(self, is_stop):
        self.is_stop = is_stop
    def update_status(self, status: str):
        if self.update_signal != None:
            self.update_signal.emit(self.device_serial, [self.total_coin_claimed, self.claim_counts, self.stop_time, status])
        # write to log file
        #current_time_date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    def send_log(self, log_message: str):
        #logging.info(f'{self.device_serial} -> {log_message}')
        self.update_status(log_message)

    def click_exist(self, xpath: str, time_click: int = 10, adding_xpath: str = None):
        #self.send_log(f'Finding {xpath}')
        if adding_xpath:
            if self.d.xpath(adding_xpath).wait(0.5):
                self.d.xpath(adding_xpath).click_exists(1)

        self.d.xpath(xpath).click_exists(timeout=time_click)

    def clickText(self, identifier='', desc='', count=5, index=0, x=0, y=0, click=True):
        try:
            for t in range(count):
                try:
                    #print(f'Finding {identifier}')
                    if identifier.startswith("text="):
                        element = self.d(
                            text=identifier.replace("text=", ""))[index]
                    elif identifier.startswith("resourceId="):
                        element = self.d(resourceId=identifier.replace(
                            "resourceId=", ""))[index]
                    elif identifier.startswith("className="):
                        element = self.d(className=identifier.replace(
                            "className=", ""), description=desc)[index]
                    else:
                        raise ValueError("Loại identifier không được hỗ trợ")

                    if element.exists:
                        x1, y1 = element.info['bounds']['left'], element.info['bounds']['top']
                        if click:
                            self.d.click(x1+x, y1+y)
                            
                        return True
                except Exception as e:
                    self.send_log(f'Error: {e}')
                time.sleep(1)
            return False
        except Exception as e:
            return False

    # def sendText(self, text):
        # try:
            # """Nhập văn bản ADB"""
            # self.d.shell('ime set com.android.adbkeyboard/.AdbIME')
            # text = str(base64.b64encode(text.encode('utf-8')))[1:]
            # self.d.shell(f'am broadcast -a ADB_INPUT_B64 --es msg {text}')

        # except Exception as e:
            # return False

    # def find_and_set_text(self, xpath: str, text: str, time_click: int = 10):
        # self.send_log(f'Finding {xpath}')
        # time.sleep(0.5)
        # if self.d.xpath(xpath).wait(time_click):
            # self.d.xpath(xpath).set_text(text)


    def scroll_down(self, min: int = 1, max: int = 1):
        
        screen_size = self.d.window_size()
        width, height = screen_size[0], screen_size[1]
        
        for _ in range(random.randint(min, max)):
            self.d.swipe(width // 2, height * 3 // 4, width // 2, height // 20, 0.1)

    def start_app(self):
        self.send_log('Starting app')
        self.d.app_start(CONFIG.APP_PACKAGE, stop=True, use_monkey=True)
        if self.d.xpath(XPATHS.POPUP_BANNER + '|' + XPATHS.LIVE_STREAM_TAB).wait(10):
            if self.d.xpath(XPATHS.POPUP_BANNER).wait(1):
                self.click_exist(XPATHS.POPUP_CLOSE)

        if not self.d.xpath(XPATHS.LIVE_STREAM_TAB).wait(10):
            self.send_log('App not started')
            self.lietke()
            return False
        
        self.click_exist(XPATHS.LIVE_STREAM_TAB)
        self.send_log('Processing claim')
        return True
    
    # def _test(self):
        # while True:
            # self.send_log('Test')
            # self.total_coin_claimed += 1
            # time.sleep(5)

    def check_stop_time(self):
        if self.stop_time is not None and self.stop_time != "":
            stop_time = datetime.strptime(self.stop_time, "%Y-%m-%d %H:%M:%S")
            current_time = datetime.now()
            if stop_time > current_time:
                self.update_stop_status(True)
                print("Stop_time")

    def lietke(self):
        elements = self.d(textContains='Xác nhận')
        if elements.exists:
            webviews = self.d(className="android.webkit.WebView")
            if webviews.exists:
                self.send_log('Vựa qua Captcha lần '+ str(self.captcha_count))
                start_y = random.randint(300, 560)
                self.d.swipe(166, 666, start_y, 666, duration=0.2)
                self.captcha_count+=1
                if self.captcha_count>=40 :
                    self.send_log('Đã cập nhật thêm dữ liệu captcha cho lần tiếp theo')
                    self.captcha_count=0
                    self.start_app()
                else:
                    self.lietke()



    def generate_random_id(self):
        characters = list('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789')
        random_id = ''.join(random.choice(characters) for _ in range(20))
        return random_id

    def update_data_captcha(self):
        start_y = random.randint(300, 560)
        with open("captcha.data", "a") as file:
            id_cap=self.generate_random_id()
            file.write(str(id_cap)+":"+str(start_y)+"\n")

    def checkchitieu(self):
        print('Kiểm tra chỉ tiêu '+str(self.total_coin_claimed)+'/'+str(self.chitieu))
        if self.total_coin_claimed>=self.chitieu:
            self.send_log('Đủ chỉ tiêu rồi không săn xu nữa!')
            self.is_stop=True

    def claim_coin(self, times: int = 5):
        #print(self.total_coin_claimed)
        #self.start_app()
        time.sleep(5)
        while not self.is_stop:
            #print('Bắt đầu vòng lặp 1')
            #print(self.is_stop)

            if not self.status == 1:
                self.status = 1
                self.send_log('Scrolling down')
            if self.d.app_current()['package'] != CONFIG.APP_PACKAGE:
                self.start_app()
            self.lietke()
            if not self.d.xpath(XPATHS.MORE_BTN).wait(10):
                self.start_app()
            
            self.click_exist(XPATHS.POPUP_AD)
            self.check_stop_time()
            self.scroll_down()
            #print('Kéo Scroll')
            self.lietke()
            if not self.d.xpath(XPATHS.COIN_STATE).wait(10):
                time.sleep(CONFIG.WAIT_COIN_TIME)
                continue
            coin_status = self.d.xpath(XPATHS.COIN_STATE).get_text()
            #print('Coin Status')
            if coin_status == 'Kết thúc':
                time.sleep(CONFIG.WAIT_COIN_TIME)
                continue

            if coin_status == 'Giới hạn':
                time.sleep(CONFIG.WAIT_COIN_TIME)
                continue

            if coin_status == 'Đăng nhập':
                return False

            if not self.d.xpath(XPATHS.COIN_NUM).wait(1):
                time.sleep(CONFIG.WAIT_COIN_TIME)
                continue

            coin_value = self.d.xpath(XPATHS.COIN_NUM).get_text()
            #print('Coin Value')
            if int(coin_value) <= CONFIG.MIN_COIN_VALUE:
                time.sleep(CONFIG.WAIT_COIN_TIME)
                continue
            
            while not self.is_stop:
                self.click_exist(XPATHS.POPUP_AD)
                if self.d.app_current()['package'] != CONFIG.APP_PACKAGE:
                    self.start_app()
                    break

                if not self.d.xpath(XPATHS.MORE_BTN).wait(10):
                    self.start_app()
                    break

                self.lietke()
                current_status = self.d.xpath(XPATHS.COIN_STATE).get_text()
                #print('Status')
                if current_status == 'Kết thúc':
                    time.sleep(CONFIG.WAIT_COIN_TIME)
                    break

                if coin_status == 'Giới hạn':
                    time.sleep(CONFIG.WAIT_COIN_TIME)
                    break

                if current_status == 'Đăng nhập':
                    time.sleep(CONFIG.WAIT_COIN_TIME)
                    return False
                
                if int(coin_value) <= CONFIG.MIN_COIN_VALUE:
                    time.sleep(CONFIG.WAIT_COIN_TIME)
                    break

                if not self.status == 2:
                    self.status = 2
                    self.send_log(f'Claiming: {coin_value} coin')

                #print('Kiểm tra chữ Lưu')
                if self.d.xpath(XPATHS.COIN_STATE).get_text() == 'Lưu':
                    self.d.xpath(XPATHS.COIN_NUM).click_exists(1)
                    
                    if not self.d.xpath(XPATHS.CLAIM_REMAINING).wait(10):        
                        continue
                    
                    try:
                        claim_remaining = self.d.xpath(XPATHS.CLAIM_REMAINING).get_text()
                        claim_remaining = int(re.search(r'\d+', claim_remaining).group())
                    except:
                        claim_remaining = 0

                    
                    self.click_exist(XPATHS.CLAIM_POPUP_CLOSE)
                    self.clickText('resourceId=com.shopee.vn.dfpluginshopee7:id/tv_claim_count', x=200, y=150, click=True, count=2)
                    self.claim_counts += 1
                    
                    # update to title here with coin_value
                    self.total_coin_claimed += int(coin_value)
                    self.send_log(f'Claim: {coin_value} success')

                    sel.checkchitieu()

                    subprocess.run("cls", shell=True)
                    if self.claim_counts >= CONFIG.CLAIM_TIMES:
                        self.update_stop_status(True)
                        break

                    time.sleep(5)

                    if not self.d.xpath(XPATHS.COIN_STATE).wait(10):
                        time.sleep(CONFIG.WAIT_COIN_TIME)
                        break
                    
                    coin_status = self.d.xpath(XPATHS.COIN_STATE).get_text()
                    if coin_status == 'Kết thúc':
                        time.sleep(CONFIG.WAIT_COIN_TIME)
                        break

                    if coin_status == 'Giới hạn':
                        time.sleep(CONFIG.WAIT_COIN_TIME)
                        break

                    if coin_status == 'Đăng nhập':
                        return False

                    if not self.d.xpath(XPATHS.COIN_NUM).wait(1):
                        time.sleep(CONFIG.WAIT_COIN_TIME)
                        break
                    coin_value = self.d.xpath(XPATHS.COIN_NUM).get_text()
                    
                    if int(coin_value) <= CONFIG.MIN_COIN_VALUE:
                        time.sleep(CONFIG.WAIT_COIN_TIME)
                        break
                    
                    self.lietke()
                time.sleep(3)
            
            if self.claim_counts >= CONFIG.CLAIM_TIMES:
                self.update_stop_status(True)
                break
            time.sleep(3)

        subprocess.run(['adb', '-s', self.device_serial, 'shell', 'am', 'force-stop', CONFIG.APP_PACKAGE], check=True)
        return True
    
# if __name__ == '__main__':
    # shopee = Shopee('42004ff0d630a4d9', None, None)
    # shopee.claim_coin()
