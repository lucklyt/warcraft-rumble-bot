# cython: language_level=3
import copy
import os

from PIL import Image

from adaptor import adaptor
from conf.conf import log
import math
import random
import time
from operator import attrgetter

import detect.image_cv
from conf import conf
import warcraft, units
from process_control import energy
from units import Unit, PlacementState, Trait

kobold = Unit.get_by_name("狗头人矿工")

placement_pos_list = []
unit_target_pos = dict()

base_defense_y = 1200


def init_placement_pos(mode="pve"):
    global placement_pos_list, unit_target_pos
    # 默认部署位置为基地左右
    placement_pos_list = [(adaptor.base_width / 2 - 240, base_defense_y),
                          (adaptor.base_width / 2, base_defense_y - 250),
                          (adaptor.base_width / 2 + 240, base_defense_y)]
    unit_target_pos = dict()
    for target in conf.get_placement_pos(mode):
        if target.get('name'):
            unit_target_pos[Unit.get_by_name(target.get('name'))] = target.get('pos')
        elif target.get('trait'):
            for unit in warcraft.line_up_units:
                if unit.has_trait(target.get('trait')):
                    unit_target_pos[unit] = target.get('pos')
        else:
            placement_pos_list.append(target.get('pos'))
    if warcraft.continues_failed >= 3:
        for _ in range(int(warcraft.continues_failed / 3)):
            placement_pos_list = move_to_end(placement_pos_list, placement_pos_list[0])


placement_order = [[], [], []]
cur_placement_index = 0
fetters = dict()  # 羁绊
follows = dict()  # 追随
last_placement_pos = None
last_pos_count = 0
last_placement_unit = None


def reset_placement_order(mode="pve"):
    global placement_order, cur_placement_index, fetters, follows, last_placement_pos, last_pos_count, last_placement_unit
    placement_order = [[] for _ in range(10)]
    cur_placement_index = 0
    fetters = dict()
    follows = dict()
    last_placement_pos = None
    last_pos_count = 0
    last_placement_unit = None
    rounds = conf.get_placement_rounds()
    rounds.sort(key=lambda x: x['seq'], reverse=True)
    used = dict()
    default_seq = 2
    # 指定单位的优先级最高
    bonds = conf.get_bond()
    for r in bonds:
        former_unit = Unit.get_by_name(r.get('former'))
        latter_unit = Unit.get_by_name(r.get('latter'))
        relation = r.get('relation')
        if former_unit not in warcraft.line_up_units or latter_unit not in warcraft.line_up_units:
            continue
        if relation == "单向":
            if follows.get(former_unit) is None:
                follows[former_unit] = []
            follows[former_unit].append(latter_unit)
        else:
            fetters[former_unit] = latter_unit
            used[former_unit] = True
        used[latter_unit] = True

    for unit in warcraft.line_up_units:
        if used.get(unit):
            continue
        if unit.priority:
            if unit.priority > 0:
                placement_order[unit.priority].append(unit)
            used[unit] = True

    for r in rounds:  # 指定天赋的轮次
        seq = r.get('seq', 0)
        if r.get('default'):
            default_seq = seq
        traits = r.get('traits', [])
        for t in traits:
            for line_unit in warcraft.line_up_units:
                if used.get(line_unit):
                    continue
                if line_unit.has_trait(t):
                    placement_order[seq].append(line_unit)
                    used[line_unit] = True

    for unit in warcraft.line_up_units:  # 剩下未处理的单位都放到默认轮次
        if used.get(unit):
            continue
        placement_order[default_seq].append(unit)
        used[unit] = True
    placement_order = [x for x in placement_order if len(x) > 0]
    init_placement_pos(mode)
    log.info("初始化通用部署顺序: %s", placement_order_str(placement_order))
    log.info("初始化特殊部署顺序: %s, %s",
             ",".join(["[{}--羁绊-->{}]".format(x.name, y.name) for x, y in fetters.items()]),
             ",".join(["[{}--追随-->{}]".format([s.name for s in y], x.name) for x, y in follows.items()]))
    if len(unit_target_pos) > 0:
        log.info("初始化特定单位部署位置: %s",
                 ",".join(["[{}-->{}]".format(x.name, y) for x, y in unit_target_pos.items()]))
    log.info("初始化兜底部署位置: %s", placement_pos_list)


def placement_order_str(orders):
    return "  ->  ".join(",".join(u.name for u in us) for us in orders)


def move_to_end(lst, elem):
    lst = [x for x in lst if x != elem] + [elem]
    return lst


def move_to_head(lst, elem):
    lst = [elem] + [x for x in lst if x != elem]
    return lst


def move_unit_to_head(orders, unit):
    for us in orders:
        for u in us:
            if u == unit:
                orders = move_to_head(orders, us)
                orders[0] = move_to_head(orders[0], u)
                return orders


def valid_play_pos(pos):
    if adaptor.base_width / 2 - 520 < pos[0] < adaptor.base_width / 2 + 520 and pos[1] < 188:
        return False
    if pos[1] > 1555:
        return False
    return True


enemy_pos_map = dict()


def get_enemy_pos():
    targets = detect.cv.detect_enemy_tag(warcraft.source)
    sorted_targets = sorted(targets, key=lambda pos: math.dist(pos, (adaptor.base_width / 2, base_defense_y)))
    for target in sorted_targets:
        enemy_pos_map[target] = enemy_pos_map.get(target, 0) + 1
        if valid_play_pos(target) and enemy_pos_map[target] < 8:
            log.info("发现em可能位置 {}".format(adaptor.base_position(target)))
            return target
    return None


def get_defensive_pos():
    targets = detect.cv.detect_defensive_structure(warcraft.source)
    targets = [target for target in targets if valid_play_pos(target)]
    targets.sort(key=lambda pos: pos[1])
    if len(targets) > 0:
        log.info("检测ds位置 {}".format([adaptor.base_position(target) for target in targets]))
    result = []
    for target in targets:
        if target[0] - 150 > 0:
            result.append((target[0] - 150, target[1]))
        if target[0] + 150 < adaptor.base_width:
            result.append((target[0] + 150, target[1]))
    return result


def get_placement_pos(unit: Unit):
    global placement_pos_list, cur_placement_index, placement_order, last_placement_pos, last_pos_count
    # 羁绊和追随者用上一次的部署位置,默认他们没有特殊位置
    for x, y in fetters.items():
        if y == unit and last_placement_pos:
            last_pos_count += 1
            return last_placement_pos
    for x, y in follows.items():
        if unit in y and last_placement_pos:
            last_pos_count += 1
            return last_placement_pos
    enemy_pos = get_enemy_pos()
    defensive_pos = get_defensive_pos() + placement_pos_list
    if enemy_pos:
        if unit.has_trait(Trait.Unbound) or len(defensive_pos) == 0:
            last_placement_pos = enemy_pos
            return last_placement_pos

        poses = [pos for pos in defensive_pos if pos[1] > enemy_pos[1]]
        if len(poses) == 0:
            poses = defensive_pos

        last_placement_pos = min(poses, key=lambda pos: math.dist(pos, enemy_pos))
        return last_placement_pos

    last_placement_pos = unit_target_pos.get(unit)
    if last_placement_pos:
        log.debug("unit_target_pos get pos: {}".format(last_placement_pos))
        return last_placement_pos
    defensive_pos = defensive_pos[:3]
    last_placement_pos = defensive_pos[cur_placement_index % len(defensive_pos)]
    last_pos_count += 1
    return last_placement_pos


img_gold_full = Image.open(os.path.join(conf.static_path, "img/gold_full.png"))


def get_kobold_placement_pos():
    gold_pos = adaptor.find_pic_max_pos(warcraft.source, img_gold_full)
    if not gold_pos:
        return placement_pos_list[cur_placement_index % len(placement_pos_list)]
    defensive_pos = get_defensive_pos() + placement_pos_list
    defensive_pos = [pos for pos in defensive_pos if pos[1] > gold_pos[1]]
    return min(defensive_pos, key=lambda pos: math.dist(pos, gold_pos))


little_fish_last_time = 0
special_scene = False


# 判断是否特殊关系得到满足
def special_relations(orders):
    global fetters, follows, last_placement_unit, special_scene
    if conf.get_anonymous_team():
        special_scene = True
        return orders
    follow_units = follows.get(last_placement_unit)
    fetter_unit = fetters.get(last_placement_unit)
    special_scene = True

    if fetter_unit:
        log.info(
            "{}的羁绊单位{}已经上场".format(fetter_unit.name, last_placement_unit.name))
        return [[fetter_unit]]
    if follow_units:
        log.info(
            "{}的追随单位{}已经上场".format([u.name for u in follow_units], last_placement_unit.name))
        return [follow_units] + orders
    for x, y in fetters.items():
        state, _ = x.placement_state(warcraft.source, 10)
        if state == PlacementState.NotWaiting:
            continue
        state, _ = y.placement_state(warcraft.source, 10)
        if state == PlacementState.NotWaiting:
            continue
        log.info("{}与其羁绊单位{}同时存在".format(x.name, y.name))
        x = copy.copy(x)
        x.placement_cost = min(x.placement_cost + y.placement_cost - 1, 9)
        return [[x]] + orders
    special_scene = False
    return orders


def placement_unit():
    global placement_pos_list, little_fish_last_time, fetters, cur_placement_index, last_placement_unit
    start_time = time.time()
    warcraft.capture()
    state = PlacementState.NotWaiting
    waiting_unit = []
    ec = energy.recognize(warcraft.source)
    if ec <= 0:
        return -1
    log.info("当前能量值 {}, 延迟 {:.1f}s".format(ec, time.time() - warcraft.screen_time))
    if warcraft.should_failed():
        log.info("连胜次数已满，不再放置单位")
        return 1
    cur_placement_order = (placement_order[cur_placement_index % len(placement_order):] +
                           placement_order[:cur_placement_index % len(placement_order)])
    for k in range(len(cur_placement_order)):
        cur_placement_order[k] = (cur_placement_order[k][cur_placement_index % len(cur_placement_order[k]):] +
                                  cur_placement_order[k][:cur_placement_index % len(cur_placement_order[k])])
    cur_placement_order = special_relations(cur_placement_order)
    log.info(
        "当前放置顺序 {}，延迟 {:.1f}s".format(placement_order_str(cur_placement_order),
                                              time.time() - warcraft.screen_time))

    for us in cur_placement_order:
        for u in us:
            state, pos = u.placement_state(warcraft.source, ec)
            if state == PlacementState.Ready:
                target_pos = get_placement_pos(u)
                log.info("单位 %s 能量已满，部署位置：%s->%s", u.name, adaptor.base_position(pos),
                         adaptor.base_position(target_pos))
                cur_placement_index = cur_placement_index + 1
                last_placement_unit = u
                adaptor.slide((pos, target_pos))
                break
            elif state == PlacementState.NotReady:
                waiting_unit.append(u.name)
                break
        if state == PlacementState.Ready:
            break
        if len(waiting_unit) > 0:
            log.debug("当前能量值[{}],单位[{}]能量未满，继续等待".format(ec, waiting_unit))
            break

    if not special_scene and state == PlacementState.Ready and kobold.valid():
        kobold_state, pos = kobold.placement_state(warcraft.source, ec)
        if kobold_state == PlacementState.Ready:
            target_pos = get_kobold_placement_pos()
            log.info("部署狗头人矿工，%s->%s", pos, target_pos)
            adaptor.slide((pos, target_pos))
    if state == PlacementState.NotWaiting and len(waiting_unit) == 0:
        if ec > 3:
            log.error("当前能量值[{}],错误没有找到任何单位！！".format(ec))
            warcraft.save_err_source()
            if ec >= 7:
                random_placement()
    log.debug("当前能量值[{}],部署单位处理完成，耗时 {:.2f}s".format(ec, time.time() - start_time))
    if conf.get_anonymous_team():
        adaptor.delay(0.5)
    return int(state == PlacementState.Ready) + len(waiting_unit)


def fish_time():
    log.info("鱼人时间开始！！！")
    adaptor.delay(1.5)
    st = time.time()
    order = []
    for unit in warcraft.line_up_units:
        if unit.name != "老瞎眼":
            order.append(unit)
    order.sort(key=attrgetter('placement_cost'))
    k = 0
    next_unit = None
    next_pos = None
    while True:
        warcraft.capture()
        if time.time() - st > 10:
            break
        if not warcraft.is_fish_time(warcraft.source):
            break
        ec = energy.recognize(warcraft.source)
        if not next_unit:
            for u in order:
                if u.placement_cost > ec:
                    continue
                state, pos = u.placement_state(warcraft.source, ec)
                if state == PlacementState.Ready:
                    next_unit = u
                    next_pos = pos
                    k = 0
                    order = move_to_end(order, u)
                    break
                if state == PlacementState.NotReady:
                    break

        if next_unit and ec >= next_unit.placement_cost:
            target_pos = get_placement_pos(next_unit)
            log.info("单位 %s 能量已满，去上场,位置：%s->%s", next_unit.name, next_pos, target_pos)
            adaptor.slide((next_pos, target_pos))
            # ec = ec - (next_unit.placement_cost + k)
            k = k + 1
            if next_unit.name != "迅猛龙" or k >= 3:
                next_unit = None
    log.info("鱼人时间开结束，持续时间%.2fs！！！", time.time() - st)


def random_placement():
    cards_pos = [(adaptor.base_width / 2 + units.waiting_x[0], 1678),
                 (adaptor.base_width / 2 + units.waiting_x[1], 1678),
                 (adaptor.base_width / 2 + units.waiting_x[2], 1678),
                 (adaptor.base_width / 2 + units.waiting_x[3], 1678)]
    random.shuffle(cards_pos)
    for card in cards_pos:
        adaptor.slide((card, placement_pos_list[random.randrange(0, len(placement_pos_list))]))


def map_init(mode):
    if mode == "":
        mode = "pve"
    if mode == "arclight":
        warcraft.line_up_units = units.anonymous_units
    elif not conf.get_anonymous_team() and warcraft.line_up_units == units.anonymous_units:
        warcraft.init_line_up_units()
    # cmds = conf.get_map_init_op(mode)
    # for cmd in cmds:
    #     if cmd.startswith("slide"):
    #         r = parse.parse("slide ({},{}) ({},{})", cmd)
    #         if not r or len(r.fixed) != 4:
    #             log.error("slide cmd error {}".format(cmd))
    #             continue
    #         log.info("地图初始化 slide (%d,%d) -> (%d,%d)", int(r[0]), int(r[1]), int(r[2]), int(r[3]))
    #         adaptor.slide(((int(r[0]), int(r[1])), (int(r[2]), int(r[3]))))
    #     elif cmd.startswith("touch"):
    #         r = parse.parse("touch ({},{})", cmd)
    #         if not r or len(r.fixed) != 2:
    #             log.error("touch cmd error {}".format(cmd))
    #             continue
    #         log.info("地图初始化 touch (%d,%d)", int(r[0]), int(r[1]))
    #         adaptor.touch((int(r[0]), int(r[1])))
    #     else:
    #         log.error("not support cmd {}".format(cmd))
