# cython: language_level=3
from conf.conf import log
import os
import subprocess
import time
import platform

from PIL import Image
from dateutil import parser
from adb_shell import exceptions
from adb_shell.adb_device import AdbDeviceTcp
from adb_shell.auth.sign_pythonrsa import PythonRSASigner
from conf import conf

adb_path = os.path.join(conf.application_path, "platform-tools")
os.environ["PATH"] += os.pathsep + adb_path
device_id = "localhost:" + str(conf.adb_port())

target_size = (1080, 1920)
ratio = 1.0

base_height = 1920
base_width = 1080
device = AdbDeviceTcp('localhost', 5555, default_transport_timeout_s=10.)


def init():
    connect()


def screen_size():
    global base_width
    r = device.shell("wm size", timeout_s=10, decode=True)
    ss = r.split()
    if len(ss) == 0:
        log.error("获取模拟器分辨率失败！{}".format(r))
        return
    ss = ss[len(ss) - 1].split("x")
    if len(ss) != 2:
        log.error("获取模拟器分辨率失败！{}".format(ss))
        return
    global target_size, ratio
    target_size = (int(ss[0]), int(ss[1]))
    ratio = target_size[1] / base_height
    base_width = int(target_size[0] / ratio)
    log.info("模拟器分辨率为{}，转换比例为{:.2f},转换后为{}".format(target_size, ratio, (base_width, base_height)))


def connect():
    global device
    try:
        device = AdbDeviceTcp('localhost', conf.adb_port(), default_transport_timeout_s=10.)
        with open(conf.private_key) as f:
            private_key = f.read()
        with open(conf.public_key) as f:
            public_key = f.read()
        signer = PythonRSASigner(public_key, private_key)
        if device.connect(rsa_keys=[signer], auth_timeout_s=3):
            screen_size()
        else:
            log.error("connect failed")
    except ConnectionRefusedError as e:
        log.error("connect refused")
    finally:
        if not device.available:
            log.error("connect failed")


def is_app_running():
    r = device.shell("dumpsys window", decode=True, timeout_s=10)
    ss = r.split("\n")
    for s in ss:
        if "mCurrentFocus" not in s:
            continue
        if conf.get_app_package() in s:
            return True
        else:
            return False
    return False


def start_app():
    device.shell("am start -n " + conf.get_app_activity(), decode=True, timeout_s=10)


def start_play_game():
    device.shell("am start -n com.google.android.play.games/com.google.android.gms.games.ui.destination."
                 "main.MainActivity", decode=True, timeout_s=10)
    time.sleep(1)
    device.shell("am start -n com.android.vending/com.google.android.finsky.activities.MainActivity", decode=True, timeout_s=10)


def stop_app():
    device.shell("am force-stop " + conf.get_app_package(), decode=True, timeout_s=10)


def reconnect():
    log.info("reconnecting...")
    stop_emulator()
    start_emulator()
    connect()


def clean():
    if device.available:
        device.close()


def start_emulator():
    if platform.system().lower() == 'windows':
        if conf.get_emulator_path():
            os.startfile(conf.get_emulator_path())
            time.sleep(10)


def stop_emulator():
    if platform.system().lower() == 'windows':
        if conf.get_emulator_path():
            subprocess.run('taskkill /f /im %s' % os.path.basename(conf.get_emulator_path()),
                           shell=True, text=True, timeout=10)
            time.sleep(3)


# 设备屏幕截图，需给定did和本机截图保存路径
def screen_capture(cap_path):
    try:
        device.shell("screencap  sdcard/adb_screenCap.png", decode=True, timeout_s=10)
        device.pull("sdcard/adb_screenCap.png", cap_path)
        if os.path.exists(cap_path):
            img = Image.open(cap_path)
            if ratio != 1.0:
                img = img.resize((base_width, base_height))
            return img
        else:
            log.error(
                "图片保存失败，请确定路径 {} 存在，并尝试将文件夹放到硬盘根目录，去掉文件夹路经中的数字空格等符号".format(
                    cap_path))
            return None
    except (exceptions.AdbConnectionError, exceptions.AdbTimeoutError, exceptions.AdbCommandFailureException,
            exceptions.TcpTimeoutException, ConnectionAbortedError, ConnectionRefusedError, ConnectionResetError,
            BrokenPipeError):
        log.error("adb device not found or timeout,sleep 3s then try reconnect")
        reconnect()
        return None


# 模拟点击屏幕，参数pos为目标坐标(x, y)
def touch(pos):
    device.shell("input touchscreen tap {0} {1}".format(
        base_pos(pos[0]), base_pos(pos[1])), decode=True, timeout_s=10)


# 模拟滑动屏幕，posStart为起始坐标(x, y)，posStop为终点坐标(x, y)，time为滑动时间
def slide(start_pos, end_pos, duration):
    device.shell("input draganddrop {0} {1} {2} {3} {4}".
                 format(base_pos(start_pos[0]), base_pos(start_pos[1]),
                        base_pos(end_pos[0]), base_pos(end_pos[1]), duration), decode=True, timeout_s=10)


# 模拟长按屏幕，参数pos为目标坐标(x, y)，time为长按时间
def long_touch(pos, duration):
    device.shell("input swipe {0} {1} {2} {3} {4}".format(
        base_pos(pos[0]), base_pos(pos[1]),
        base_pos(pos[0]), base_pos(pos[1]), duration), decode=True,
        timeout_s=10)


def set_timezone(timezone):
    device.shell("service call alarm 3 s16 {0}".format(timezone), decode=True, timeout_s=10)


def get_datetime():
    r = device.shell("date +\"%Y-%m-%dT%H:%M:%S%z\"", decode=True, timeout_s=10)
    try:
        st = parser.parse(r)
        return st
    except Exception as e:
        log.error("get_datetime error: " + str(e))
        return None


def back():
    device.shell("input keyevent KEYCODE_BACK", timeout_s=10)


def base_pos(pos):
    return int(pos * ratio)


def base_target(target):
    return base_pos(target[0]), base_pos(target[1])
