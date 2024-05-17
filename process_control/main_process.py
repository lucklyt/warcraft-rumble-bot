# cython: language_level=3
import sys
import time
import traceback
from enum import Enum

from conf import conf
from conf.conf import log
from . import battle
from adaptor import adaptor
from . import warcraft

last_battle_time = time.time()
enter_battle = False
mode = ""
start_time = time.time()
slept = False
expired_time = 180


class RunningStatus(str, Enum):
    Running = "running"
    Stopped = "stopped"


status = RunningStatus.Stopped


def prepare():
    try:
        global enter_battle
        global last_battle_time
        global mode
        enter_battle = False
        while True:
            log.debug("准备阶段判断开始")
            if status == RunningStatus.Stopped:
                return
            if time.time() - last_battle_time > 60:
                if warcraft.something_wrong():
                    return
            if time.time() - last_battle_time > expired_time:
                log.error("异常！长时间没进入战斗界面")
                restart_game()
            if not warcraft.capture():
                break
            if warcraft.is_main_title():
                log.debug("在主界面")
                if warcraft.check_network():
                    continue
                if warcraft.remove_support_icon():
                    continue
                if conf.game_mode() != "pvp":
                    if warcraft.click_arclight_map():
                        continue
                    if warcraft.goto_arclight_map():
                        continue
                    if warcraft.click_task_award():
                        continue
                    if warcraft.open_task_interface():
                        continue
                if conf.game_mode() != "pve":
                    if warcraft.open_pvp_interface():
                        continue
            elif warcraft.arclight_take_award():
                continue
            elif warcraft.start_arclight_task():
                enter_battle = True
                mode = "arclight"
                break
            elif warcraft.select_arclight_task():
                continue
            elif warcraft.arclight_back():
                continue
            elif warcraft.do_select_task():
                enter_battle = True
                mode = "pve"
                break
            elif warcraft.do_take_exp_award():
                continue
            elif conf.game_mode() != "pve" and warcraft.start_pvp_match():
                enter_battle = True
                mode = "pvp"
                break
            else:
                break
        log.debug("准备阶段结束")

    except KeyboardInterrupt:
        sys.exit()
    except Exception as e:
        warcraft.save_err_source()
        log.error(traceback.format_exc())


def battle_flow():
    global last_battle_time
    global enter_battle
    global mode
    started = False
    start_count = 0
    try:
        log.debug("战斗阶段判断")
        st = time.time()
        battle.map_init(mode)
        battle.reset_placement_order(mode)
        while True:
            if status == RunningStatus.Stopped:
                return
            if time.time() - st > 360:
                log.error("异常!战斗中停留时间过长,重启游戏")
                restart_game()
                return
            if start_count > 10:
                log.error("点击开始10次仍无反应，估计卡死了重启游戏")
                restart_game()
                return
            if not warcraft.capture():
                log.error("获取图片失败")
                break
            if not started or time.time() - last_battle_time > 3:
                if warcraft.session_error():
                    break
                if warcraft.continue_battle():
                    adaptor.delay(0.2)
                    continue
                if warcraft.is_battle_over():
                    if enter_battle and time.time() - st < 30:
                        log.debug("战斗中不识别画面，等待时间不够，继续等待")
                    else:
                        log.debug("战斗结束退出")
                        break
            if not started:
                if warcraft.is_loading():
                    log.debug("加载中")
                    adaptor.delay(0.1)
                    continue
                if warcraft.is_cut_scenes():
                    log.debug("战斗动画播放中")
                    adaptor.delay(0.1)
                    continue
            if not started or time.time() - last_battle_time > 5:
                log.debug("not started and > 5s  since last battle")
                if warcraft.start_battle():
                    warcraft.capture()
                    start_count = start_count + 1
            if battle.placement_unit() >= 0:
                log.debug("placement return >= 0")
                started = True
                last_battle_time = time.time()

        log.debug("战斗阶段结束")
    except KeyboardInterrupt:
        sys.exit()
    except Exception as e:
        log.error(traceback.format_exc())
        warcraft.save_err_source()


def settlement():
    try:
        got = False
        log.debug("结算阶段判断")
        while True:
            if status == RunningStatus.Stopped:
                return
            if not warcraft.capture():
                break
            if time.time() - last_battle_time > expired_time:
                log.error("异常！长时间没进入战斗界面")
                restart_game()
                return
            if warcraft.is_settlement_interface():
                log.debug("在结算页面")
                if not got:
                    warcraft.battle_statistical()
                    got = True
                if warcraft.refresh_task():
                    restart_game()
                    return
                if warcraft.return_main_interface():
                    if not warcraft.capture():
                        break
                    if warcraft.do_take_exp_award():
                        break
            else:
                break
    except KeyboardInterrupt:
        sys.exit()
    except Exception as e:
        log.error(traceback.format_exc())


def check_other():
    try:
        global last_battle_time, slept
        log.info("检查其他")
        if status == RunningStatus.Stopped:
            return
        if warcraft.do_take_exp_award():
            return
        if conf.get_auto_delete_cache():
            adaptor.delete_expired_files()
        if warcraft.total % 40 != 0:
            slept = False
        if not slept and warcraft.total != 0 and warcraft.total % 40 == 0:
            log.info("休息半小时")
            warcraft.close_game()
            st = time.time()
            slept = True
            while True:
                if status == RunningStatus.Stopped:
                    return
                if time.time() - st > 1800:
                    restart_game()
                    return
                time.sleep(1)
        if time.time() - last_battle_time < 30:
            return
        if time.time() - last_battle_time > expired_time:
            log.error("异常！长时间没进入战斗界面")
            restart_game()
        if not warcraft.capture():
            return
        if warcraft.check_network():
            return
        if warcraft.do_take_exp_award():
            return
        if warcraft.take_unit_award():
            return
        elif warcraft.do_error_conform():
            return
        elif warcraft.do_user_level_up():
            return
        elif warcraft.unit_level_up():
            return
        elif not warcraft.is_game_open():
            warcraft.open_game()
        elif warcraft.take_lost_thing():
            log.info("未领取的物品!")
        elif warcraft.choose_exp():
            return
        elif warcraft.wait_server():
            return
        elif warcraft.rank_up():
            log.info("排名提升")
        elif warcraft.leave_h5():
            return
        elif warcraft.cancel_exit_game():
            return

    except KeyboardInterrupt:
        sys.exit()
    except Exception as e:
        warcraft.save_err_source()
        log.error(traceback.format_exc())


def restart_game():
    global last_battle_time
    warcraft.close_game()
    warcraft.open_game()
    last_battle_time = time.time()


def init():
    global last_battle_time, start_time, mode, slept
    last_battle_time = time.time()
    start_time = time.time()
    mode = ""
    slept = False
    try:
        warcraft.init()
        if not warcraft.is_game_open():
            warcraft.open_game()
    except Exception as e:
        log.error(traceback.format_exc())


def run():
    init()
    global status
    status = RunningStatus.Running
    while True:
        if status == RunningStatus.Stopped:
            log.debug("已停止退出")
            break
        if not conf.schedule_check():
            log.info("不在定时区间，结束")
            break
        prepare()
        battle_flow()
        settlement()
        check_other()
    warcraft.clean()


def stop():
    global status
    status = RunningStatus.Stopped


if __name__ == "__main__":
    run()
