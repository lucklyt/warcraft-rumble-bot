# cython: language_level=3
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from logging import handlers
from adb_shell.auth.keygen import keygen
import yaml

application_path = ""
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
elif __file__:
    application_path = os.getcwd()
conf_dir = os.path.join(application_path, "conf")
conf_path = os.path.join(application_path, "conf/app.yaml")
static_path = os.path.join(application_path, "static")
minis_path = os.path.join(static_path, "minis")
log_dir = os.path.join(application_path, "log")
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
cache_dir = os.path.join(application_path, "cache")
if not os.path.exists(cache_dir):
    os.mkdir(cache_dir)

ocr_path = os.path.join(static_path, "ocr")
public_key = os.path.join(conf_dir, "rsa.pub")
private_key = os.path.join(conf_dir, "rsa")
log = logging.getLogger("warcraft-rumble")
handler = handlers.TimedRotatingFileHandler(
    os.path.join(log_dir, str(int(time.time())) + "_" + str(os.getpid()) + ".log"),
    encoding="utf-8",
    when="H")
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
log.addHandler(handler)
open(public_key, 'w').close()
open(private_key, 'w').close()
keygen(private_key)
try:
    data = yaml.load(open(conf_path, encoding="utf-8"), Loader=yaml.FullLoader)
except Exception as e:
    log.error("解析配置文件失败，请检查配置格式是否正确，错误信息：%s", e)
    input("按回车退出")
    sys.exit(0)
pvp_data = data.get("pvp", {})
pve_data = data.get("pve", {})
notify = data.get("notify", {})


def get_platform():
    return data.get("platform", "pc")


def set_platform(platform):
    data["platform"] = platform
    save_file()
    log.debug("set platform %s", platform)


def adb_port():
    return data.get("adb", {}).get("port", 0)


def game_mode():
    return data.get("game_mode", "")


def set_game_mode(mode):
    data["game_mode"] = mode
    save_file()
    log.debug("set game mode %s", mode)


def get_line_up():
    return data.get("line_up", [])


def get_anonymous_team():
    return data.get("anonymous_team", False)


def set_anonymous_team(value):
    data["anonymous_team"] = value
    save_file()
    log.debug("set anonymous team %s", value)


def get_kobold_skin():
    return data.get("kobold", {}).get("skin", "无")


def get_slide_duration():
    return data.get("emulator", {}).get("slide_duration", [500, 1000])


def get_placement_pos(mode="pvp", battle_map="default"):
    if mode != "pve" and battle_map == "default":
        battle_map = pvp_data.get("map", "default")
    if mode != "pve":
        info = pvp_data
    else:
        info = pve_data
    r = info.get(battle_map, {}).get("placement_targets", [])
    if not r:
        r = []
    return r


def get_pos_deviation():
    return data.get("emulator", {}).get("pos_deviation", 10)


def get_auto_delete_cache():
    return data.get("log", {}).get("auto_delete_cache", False)


def get_log_level():
    return data.get("log", {}).get("level", "INFO")


def set_log_level(level):
    data["log"]["level"] = level
    save_file()
    log.debug("set log level %s", level)
    log.setLevel(logging.getLevelName(level))


def is_refresh_task():
    return data.get("pve", {}).get("refresh_task", False)


def set_refresh_task(value):
    data["pve"]["refresh_task"] = value
    save_file()
    log.debug("set refresh task %s", value)


def get_map_init_op(mode="pvp", map="default"):
    if mode != "pve" and map == "default":
        map = pvp_data.get("map", "default")
    if mode != "pve":
        info = pvp_data
    else:
        info = pve_data
    return info.get(map, {}).get("init_op", [])


def get_user():
    user = data.get("auth", {})
    return user.get("username", ""), user.get("password", "")


def get_placement_rounds():
    return data.get("placement_rounds", [])


def get_cv_threshold():
    return data.get("model", {}).get("cv_threshold", 0.8)


def get_touch_delay():
    return data.get("emulator", {}).get("touch_delay", 40)


def get_mail_receiver():
    return notify.get("mail", {}).get("receiver", "")


def get_mail_code():
    return notify.get("mail", {}).get("code", "")


def set_mail_code(code):
    notify["mail"]["code"] = code
    save_file()
    log.debug("set mail code %s", code)


def get_emulator_path():
    return data.get("emulator", {}).get("path", "")


def set_emulator_path(emulator_path):
    data["emulator"]["path"] = emulator_path
    save_file()
    log.debug("set emulator_path %s", emulator_path)


def get_capture_file_name():
    return data.get("log").get("capture_file_name", "screen")


def get_capture_log_switch():
    return data.get("log").get("save_capture", False)


def save_capture_log_switch(value):
    data["log"]["save_capture"] = value
    save_file()


def get_app_package():
    return data.get("adb", {}).get("app_package", "")


def get_app_activity():
    return data.get("adb", {}).get("app_activity", "")


# 写入配置
def set_user_name(username):
    data["auth"]["username"] = username
    save_file()
    log.debug("set username %s", username)


def set_mail_receiver(mail_receiver):
    notify["mail"]["receiver"] = mail_receiver
    save_file()
    log.debug("set mail receiver %s", mail_receiver)


def set_user_password(password):
    data["auth"]["password"] = password
    save_file()
    log.debug("set password %s", password)


def set_adb_port(port):
    data["adb"]["port"] = port
    save_file()
    log.debug("set port %s", port)


def set_line_up(line_up):
    for unit in line_up:
        if not unit.get('order', None):
            unit.pop('order', None)
    data["line_up"] = line_up
    save_file()
    log.debug("set line up %s", line_up)


def get_supported_units():
    m = dict()
    for name in os.listdir(minis_path):
        dir_path = os.path.join(minis_path, name)
        if os.path.isdir(dir_path):
            for talent in os.listdir(dir_path):
                if not talent.endswith(".png"):
                    continue
                m[name] = m.get(name, []) + [talent[:-4]]
    return m


def get_bond():
    return data.get("bond", [])


def set_bond(bond):
    data["bond"] = bond
    save_file()


def set_schedule_switch(value: bool):
    if not data.get("scheduled"):
        data["scheduled"] = dict()
    data["scheduled"]["enabled"] = value
    save_file()


def get_schedule_switch():
    return data.get("scheduled", {}).get("enabled", False)


def set_schedule_start_time(value):
    if not data.get("scheduled"):
        data["scheduled"] = dict()
    data["scheduled"]["start_time"] = value
    save_file()


def get_schedule_start_time():
    return data.get("scheduled", {}).get("start_time", None)


def set_schedule_end_time(value):
    if not data.get("scheduled"):
        data["scheduled"] = dict()
    data["scheduled"]["end_time"] = value
    save_file()


def get_schedule_end_time():
    return data.get("scheduled", {}).get("end_time", None)


def save_file():
    with open(conf_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, encoding="utf-8", allow_unicode=True, sort_keys=False)


def judge_time_range(st, et):
    now = datetime.now().strftime("%H:%M")
    if st > et:
        return st <= now <= "24:00" or "00:00" <= now <= et
    return st <= now <= et


def schedule_check():
    if not get_schedule_switch():
        return True
    if judge_time_range(get_schedule_start_time(), get_schedule_end_time()):
        return True
    return False


def schedule_countdown():
    now = datetime.now()
    start_time = datetime.strptime(str(now.date()) + get_schedule_start_time(), "%Y-%m-%d%H:%M")
    if now < start_time:
        delta = start_time - now
    else:
        delta = start_time + timedelta(days=1) - now
    return timedelta(seconds=int(delta.total_seconds()))


log.setLevel(logging.getLevelName(get_log_level()))
