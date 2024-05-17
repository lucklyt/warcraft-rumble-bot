# cython: language_level=3
import datetime as dt
import re

from conf.conf import log
import os.path
import time
from datetime import datetime

import pytz
from PIL import Image

import conf.conf as conf
import units
from adaptor import adaptor, emulator
from units import Unit
from mail import mail

source = Image.Image()
screen_time = time.time()


def capture():
    global source, screen_time
    source = None
    screen_time = time.time()
    source = adaptor.screen_picture()
    if source is None:
        log.error("ADB读取屏幕失败")
        return False
    adaptor.clear_ocr_cache()
    return True


def save_err_source():
    try:
        if source is not None and source.width != 0 and source.height != 0:
            file_name = "err_" + datetime.now().strftime(conf.get_capture_file_name())
            adaptor.save_image(source, file_name)
            return file_name
        return "no_source"
    except Exception as e:
        pass


line_up_units = []


def init_line_up_units():
    global line_up_units
    line_up_units = []
    if conf.get_anonymous_team():
        log.info("匿名战队")
        line_up_units = units.anonymous_units
        return
    us = conf.get_line_up()
    if len(us) == 0:
        raise Exception("line up config error")
    for u in us:
        name = u.get('name')
        talent = u.get('talent')
        if not name or not talent:
            log.fatal("line up config error")
            raise Exception("line up config error")
        unit = Unit.get_by_name(name)
        unit.equip_talent(talent)
        unit.priority = u.get('order', 0)
        if not Unit or not unit.valid():
            log.error("not support unit: %s-%s" % (name, talent))
            continue
        line_up_units.append(unit)
        log.info("line up unit: %s", name)
    Unit.get_by_name("狗头人矿工").equip_talent(conf.get_kobold_skin())


def is_fish_time(img: Image.Image):
    img = adaptor.crop_image(img, (320, 1848), (1037, 1892))
    count = 0
    for pixel in img.getdata():
        if pixel[0] < 100 and pixel[1] > 200 and pixel[2] < 50:
            count += 1
    return count > 100


def is_main_title():
    return adaptor.find_text_either(source, "竞技", y_min=1513, y_max=1658)


task_select_index = 0
last_battle_result = ""
task_name_areas = [(-540, 1258, -180, 1437), (-180, 1258, 180, 1437), (180, 1258, 540, 1437)]
unit_got_exp = dict()


def do_select_task():
    if not adaptor.find_text_all(source, "任务", "开始"):
        return False
    if adaptor.find_text_touch(source, "开始", index=get_task_index(), rand=False):
        log.info("开始任务")
        adaptor.delay(3)
        return True
    return False


def get_task_index():
    global task_select_index
    if conf.get_anonymous_team():
        task_select_index += 1
        return task_select_index
    tasks = []
    for area in task_name_areas:
        img = source.crop((area[0] + adaptor.base_width / 2, area[1], area[2] + adaptor.base_width / 2, area[3]))
        tasks.append(adaptor.get_texts(img, merge=True))
    log.info("任务列表候选单位为 {}".format(tasks))
    if last_battle_result == "victory" or last_battle_result == "":
        for i in range(len(tasks)):
            for j in line_up_units:
                log.debug("任务选择检测:{} {}".format(j.name, tasks[i]))
                if j.name.find(tasks[i]) >= 0 or j.name.replace("·", "").find(tasks[i]) >= 0:
                    task_select_index = i
                    log.info("上场战斗胜利，优先选择战队成员任务:{}(序号{})".format(j.name, task_select_index))
                    return task_select_index
        log.error("任务选择检测战队成员任务失败，确认出场配置正确")
    task_select_index += 1
    if len(tasks) == 0:
        tasks = ["任务列表识别错误"]
    log.info("上场战斗失败或者其他情况，选择下一任务:{}(序号{})".format(
        tasks[task_select_index % len(tasks)], task_select_index))
    return task_select_index


image_take_exp_button = Image.open(os.path.join(conf.static_path, "task/take_exp_award.png"))


def get_zh(s):
    return "".join(re.findall(r"[\u4e00-\u9fa5]+", s))


def do_take_exp_award():
    global got_exp, unit_got_exp, exp_0_cnt
    log.debug("领取奖励判断")
    if not adaptor.find_text_touch(source, "领取", y_min=1435, y_max=1545):
        return False

    img = source.crop((adaptor.base_width / 2 + 28, 563, adaptor.base_width / 2 + 250, 624))
    exp = adaptor.recognize_number(img)
    if exp < 0 or exp > 1000:
        exp = 0
    if exp == 0:
        exp_0_cnt += 1
    else:
        exp_0_cnt = 0
    got_exp = got_exp + exp
    img = source.crop((adaptor.base_width / 2 - 150, 1269, adaptor.base_width / 2 + 150, 1439))
    name = get_zh(adaptor.get_texts(img, merge=True))
    unit_got_exp[name] = unit_got_exp.get(name, 0) + exp
    log.info(
        "领取奖励,已获取经验值 {}({}+{})exp, 经验获取速率 {:.2f}exp/s".format(got_exp, name, exp, got_exp / (
                time.time() - start)))
    log.info("各单位领取经验分布为 {}".format(unit_got_exp))
    adaptor.delay(3)
    return True


def do_error_conform():
    if adaptor.find_text_all(source, "错", "确定"):
        log.error("监测到错误弹框")
        adaptor.find_text_touch(source, "确定")
        adaptor.delay(30)


img_level_up = Image.open(os.path.join(conf.static_path, "level/level_up.png"))


def unit_level_up():
    if adaptor.find_text_touch(source, "等级提升"):
        log.info("单位等级提升")
        adaptor.delay(6)
        return True
    if adaptor.find_pic_touch(source, img_level_up):
        log.info("单位等级提升")
        adaptor.delay(6)
        return True
    return False


def open_game():
    log.info("打开游戏")
    adaptor.start_app()
    adaptor.delay(20)
    return True


def is_game_open():
    return adaptor.is_app_running()


def close_game():
    log.info("关闭游戏")
    adaptor.close_app()
    adaptor.delay(1)


def do_user_level_up():
    if adaptor.find_text_either(source, "收藏等级提升", "经验值奖励提高"):
        log.info("收藏等级提升，领取奖励")
        if adaptor.find_text_touch(source, "领取奖励"):
            log.info("领取奖励成功")
            adaptor.delay(5)
            return True
    return False


def open_task_interface():
    if adaptor.find_text_touch(source, "任务"):
        log.info("打开任务面板")
        adaptor.delay(1)
        return True
    return False


def open_pvp_interface():
    if adaptor.find_text_touch(source, "竞技", y_min=1513, y_max=1658):
        log.debug("打开竞技")
        adaptor.delay(1)
        return True
    return False


def start_pvp_match():
    if adaptor.find_text_touch(source, "乱斗"):
        log.debug("开始匹配对手")
        adaptor.delay(15)
        return True
    return False


image_loading = Image.open(os.path.join(conf.static_path, "img/loading.png"))


def is_loading():
    log.debug("is_loading")
    if adaptor.find_pic_max_pos(source, image_loading):
        return True
    if adaptor.find_text_touch(source, "点击跳"):
        log.info("点击跳过")
        return True
    return adaptor.find_text_either(source, "加载中")


image_pvp_vs = Image.open(os.path.join(conf.static_path, "img/pvp_vs.png"))


def is_cut_scenes():
    log.debug("is_cut_scenes")
    if adaptor.find_text_touch(source, "点击跳过"):
        log.info("点击跳过")
        return True
    return adaptor.find_pic_max_pos(source, image_pvp_vs)


def is_battle_pause():
    return adaptor.find_text_either(source, "重来", "设置", "投降")


battle_continue_img = Image.open(os.path.join(conf.static_path, "img/battle_continue.png"))


def continue_battle():
    log.debug("continue_battle judge")
    if adaptor.find_pic_touch(source, battle_continue_img):
        log.info("游戏暂停了，继续")
        return True
    return False


image_pvp_emoji = Image.open(os.path.join(conf.static_path, "img/pvp_emotion.png"))
image_pve_pause = Image.open(os.path.join(conf.static_path, "img/battle_pause.png"))


def is_battle_over():
    log.debug("battle_over")
    return not adaptor.find_pics(source, image_pvp_emoji, image_pve_pause)


def start_battle():
    if adaptor.find_text_touch(source, "开始"):
        log.debug("进入战斗画面：点击开始")
        adaptor.delay(0.5)
        return True
    return False


def is_settlement_interface():
    return adaptor.find_text_either(source, "继续", "世界地图")


def return_main_interface():
    if adaptor.find_text_touch(source, "继续"):
        log.debug("点击继续")
        adaptor.delay(4)
        return True
    if adaptor.find_text_touch(source, "世界地图"):
        log.debug("点击世界地图")
        adaptor.delay(4)
        return True
    return False


image_take_lost_button = Image.open(os.path.join(conf.static_path, "img/take_lost_button.png"))


def take_lost_thing():
    if adaptor.find_text_either(source, "未领取的物品"):
        log.info("发现未领取的物品")
        if adaptor.find_pic_touch(source, image_take_lost_button):
            log.info("点击领取")
            adaptor.delay(1)
        return True
    log.debug("没有未领取的物品")
    return False


def take_unit_award():
    if adaptor.find_text_either(source, "士兵选择", "主将选择"):
        log.info("选择单位奖励")
        adaptor.touch((adaptor.base_width / 2, 1555))
        return True
    return False


def rank_up():
    if adaptor.find_text_touch(source, "名提升"):
        return True
    return False


victory = 0
failed = 0
draw = 0
total = 0
got_exp = 0
start = time.time()
continues_failed = 0
continues_victory = 0
exp_0_cnt = 0


def should_failed():
    return continues_victory >= 4


def battle_statistical():
    global victory, failed, draw, total, got_exp, last_battle_result, continues_failed, continues_victory, exp_0_cnt
    if should_failed():
        continues_victory = 0
        return
    total = total + 1
    if adaptor.find_text_either(source, "胜", "利"):
        victory += 1
        last_battle_result = "victory"
        continues_failed = 0
        continues_victory += 1
    elif adaptor.find_text_either(source, "失", "败"):
        failed = failed + 1
        last_battle_result = "failed"
        continues_failed += 1
        continues_victory = 0
    elif adaptor.find_text_either(source, "平", "局"):
        draw = draw + 1
        last_battle_result = "draw"
        continues_failed += 1
        continues_victory = 0
    else:
        save_err_source()
        victory += 1
        last_battle_result = "unknown"
        continues_victory = 0
        log.error("结算页面无法识别结果 %s", save_err_source())
    img = source.crop((adaptor.base_width / 2 - 240, 1525, adaptor.base_width / 2 + 240, 1628))
    exp = adaptor.recognize_number(img)
    if exp < 0 or exp > 1000:
        exp = 0
    if exp == 0:
        exp_0_cnt += 1
    else:
        exp_0_cnt = 0
    got_exp = got_exp + exp
    detail_info = "结算，已运行时间 %s, 总场次 %d,总获取经验值 %d(+%d), 胜利 %d(连胜%d), 失败 %d, 平局 %d, 胜率 %.2f, 单局平均时长 %d秒" % (
        dt.timedelta(seconds=time.time() - start - int((total - 1) / 40) * 1800), total, got_exp, exp, victory,
        continues_victory,
        failed, draw, victory / total, (time.time() - start - int((total - 1) / 40) * 1800) / total)
    log.info(detail_info)
    receiver = conf.get_mail_receiver()
    code = conf.get_mail_code()
    if receiver and code:
        mail.send_email("战后结算", detail_info, receiver, code)


def refresh_task():
    global exp_0_cnt
    if not conf.is_refresh_task():
        return
    now = adb_helper.get_datetime()
    if exp_0_cnt < 2 and (not now or now.minute < 50 or now.hour == 23):
        return
    log.info("模拟器当前时间 {}, 获取经验为0次数 {}".format(now, exp_0_cnt))
    timezones = pytz.all_timezones
    for zone in timezones:
        if zone == "America/Godthab" or zone == "Antarctica/Casey" or zone.startswith("Africa"):
            continue
        tz = pytz.timezone(zone)
        c = now.astimezone(tz)
        if (exp_0_cnt >= 2 and c.hour == 0) or (exp_0_cnt < 2 and c.hour == 23):
            log.info("设置模拟器时区为 {}".format(zone))
            adaptor.set_timezone(zone)
            new_dt = adaptor.get_datetime()
            if new_dt:
                log.info("设置后模拟器当前时间 {}".format(new_dt))
            if exp_0_cnt >= 2:
                exp_0_cnt = 0
            return True
    return False


img_arclight_start = [Image.open(os.path.join(conf.static_path, "arclight/task_start_tag.png")),
                      Image.open(os.path.join(conf.static_path, "arclight/task_start_tag2.png"))]


def start_arclight_task():
    if total > 20:
        return False
    if adaptor.find_pic_either_touch(source, *img_arclight_start):
        log.info("开始孤光任务")
        adaptor.delay(3)
        return True
    return False


img_arclight_task_list = [Image.open(os.path.join(conf.static_path, "arclight/task_list_tag.png")),
                          Image.open(os.path.join(conf.static_path, "arclight/task_list_tag2.png"))]


def select_arclight_task():
    if total > 20:
        return False
    if adaptor.find_pic_either_touch(source, *img_arclight_task_list, accuracy=0.85):
        log.info("选择孤光任务")
        adaptor.delay(1)
        return True
    return False


img_arclight_map = [Image.open(os.path.join(conf.static_path, "arclight/map_tag.png")),
                    Image.open(os.path.join(conf.static_path, "arclight/map_tag2.png"))]


def click_arclight_map():
    if total > 20:
        return False
    if adaptor.find_pic_either_touch(source, *img_arclight_map):
        log.info("点击孤光地图")
        adaptor.delay(1)
        return True
    return False


img_arclight_intros = [Image.open(os.path.join(conf.static_path, "arclight/intro.png")),
                       Image.open(os.path.join(conf.static_path, "arclight/intro2.png")),
                       Image.open(os.path.join(conf.static_path, "arclight/intro3.png")),
                       Image.open(os.path.join(conf.static_path, "arclight/intro5.png")),
                       Image.open(os.path.join(conf.static_path, "arclight/intro6.png")),
                       Image.open(os.path.join(conf.static_path, "arclight/intro7.png")),
                       Image.open(os.path.join(conf.static_path, "arclight/intro8.png")),
                       Image.open(os.path.join(conf.static_path, "arclight/intro9.png")),
                       Image.open(os.path.join(conf.static_path, "arclight/intro10.png")),
                       Image.open(os.path.join(conf.static_path, "arclight/intro11.png")),
                       Image.open(os.path.join(conf.static_path, "arclight/intro12.png")),
                       Image.open(os.path.join(conf.static_path, "arclight/intro13.png")),
                       Image.open(os.path.join(conf.static_path, "arclight/intro14.png")),
                       Image.open(os.path.join(conf.static_path, "arclight/intro15.png")),
                       Image.open(os.path.join(conf.static_path, "arclight/intro16.png")),
                       Image.open(os.path.join(conf.static_path, "arclight/intro4.png"))]


def goto_arclight_map():
    if total % 20 != 0 or total > 20:
        return False
    if adaptor.find_pic_either_touch(source, *img_arclight_intros):
        log.info("点击孤光标记")
        adaptor.delay(1)
        return True
    return False


img_main_take_task_award = Image.open(os.path.join(conf.static_path, "task/main_take_task_award.png"))


def click_task_award():
    if adaptor.find_pic_touch(source, img_main_take_task_award):
        log.info("主界面点击任务奖励")
        adaptor.delay(1)
        return True
    return False


img_arclight_take_award = [Image.open(os.path.join(conf.static_path, "arclight/take_award.png")),
                           Image.open(os.path.join(conf.static_path, "arclight/take_award2.png"))]


def arclight_take_award():
    if total > 20:
        return False
    if adaptor.find_pic_either_touch(source, *img_arclight_take_award, accuracy=0.85):
        log.info("领取孤光任务奖励")
        adaptor.delay(1)
        return True
    return False


img_arclight_back = Image.open(os.path.join(conf.static_path, "arclight/back.png"))


def arclight_back():
    if adaptor.find_text_either(source, "竞技", "乱斗"):
        return False
    if adaptor.find_pic_touch(source, img_arclight_back):
        log.info("孤光任务地图已做完返回")
        adaptor.delay(1)
        return True
    return False


img_support = Image.open(os.path.join(conf.static_path, "img/support.png"))


def remove_support_icon():
    if adaptor.find_pic_touch(source, img_support):
        log.info("点击支持图标")
        adaptor.delay(3)
        capture()
        leave_h5()
        adaptor.delay(3)
        return True
    return False


def cancel_exit_game():
    if adaptor.find_text_all(source, "退出游戏", "取消"):
        log.info("返回游戏")
        adaptor.find_text_touch(source, "取消")
        return True
    return False


def check_network():
    if adaptor.find_text_all(source, "连接错误", "重试"):
        log.error("网络异常提示")
        if adaptor.find_text_touch(source, "重试"):
            log.info("点击重试")
            adaptor.delay(2)
        return True
    return False


def something_wrong():
    if adaptor.find_text_all(source, "Something went wrong"):
        log.error("Google Play 服务异常")
        close_game()
        emulator.start_play_game()
        adaptor.delay(3)
        open_game()
        if adaptor.find_text_touch(source, "重试"):
            log.info("点击重试")
            adaptor.delay(2)
        return True
    return False


def leave_h5():
    img = adaptor.crop_image(source, (0, 0), (adaptor.base_width, 156))
    if adaptor.find_text_touch(img, "Done"):
        log.info("关闭H5页面")
        return True
    return False


def session_error():
    if adaptor.find_text_all(source, "会话错误"):
        log.error("会话错误")
        if adaptor.find_text_touch(source, "确定"):
            log.info("点击确定")
            adaptor.delay(10)
            return True
    return False


img_exp_choose = Image.open(os.path.join(conf.static_path, "level/choose_exp.png"))


def choose_exp():
    if adaptor.find_pic_max_pos(source, img_exp_choose):
        log.info("领取左边单位的经验值")
        adaptor.touch((adaptor.base_width / 2 - 250, 770))
        adaptor.delay(2)


def wait_server():
    if adaptor.find_text_touch(source, "等待服务器"):
        log.error("等待服务器报错，点击重载游戏")
        adaptor.delay(2)


def init():
    init_line_up_units()
    global victory, failed, draw, total, got_exp, last_battle_result, continues_failed, \
        continues_victory, start, unit_got_exp
    victory = 0
    failed = 0
    draw = 0
    total = 0
    got_exp = 0
    start = time.time()
    continues_failed = 0
    continues_victory = 0
    last_battle_result = ""
    unit_got_exp = dict()


def clean():
    adaptor.clean()
