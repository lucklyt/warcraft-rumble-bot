# cython: language_level=3
import os
import random
import re
import time
from datetime import datetime
from functools import lru_cache

import cv2
import dhash
import numpy
from PIL import Image
from cnocr import CnOcr

from conf import conf
from emulator import adb_helper
from conf.conf import log


def delay(t):
    log.debug("【主动延时】延时 {0} 秒".format(t))
    time.sleep(t)


pos_deviation = conf.get_pos_deviation()


def random_pos(pos):
    x, y = pos
    if random.randint(0, 1):
        x = x + random.randint(0, pos_deviation)
    else:
        x = x - random.randint(0, pos_deviation)
    return x, y


# 智能模拟点击某个点，将会随机点击以这个点为中心一定范围内的某个点，并随机按下时长
_touch_delay = conf.get_touch_delay()


def touch(pos):
    rand_time = random.randint(0, _touch_delay)
    _pos = random_pos(pos)
    log.debug("touch ({},{}), delay {}".format(_pos[0], _pos[1], rand_time))
    if rand_time < 10:
        adb_helper.touch(_pos)
    else:
        adb_helper.long_touch(_pos, rand_time)


slide_duration = conf.get_slide_duration()


# 智能模拟滑屏，给定起始点和终点的二元组，模拟一次随机智能滑屏
def slide(vector):
    start_pos, stop_pos = vector
    _startPos = random_pos(start_pos)
    _stopPos = random_pos(stop_pos)
    rand_time = random.randint(slide_duration[0], slide_duration[1])
    adb_helper.slide(_startPos, _stopPos, rand_time)


# 截屏，识图，返回坐标
def find_pic_max_pos(source: Image.Image, target: Image.Image, return_center=False, accuracy=conf.get_cv_threshold()):
    left_top_pos = locate(source, target, accuracy)
    if left_top_pos is None:
        return None
    if return_center:
        return image_center(target, left_top_pos)
    else:
        return left_top_pos


def find_pic_all_pos(source: Image.Image, target: Image.Image, return_center=False, accuracy=conf.get_cv_threshold()):
    left_top_pos = locate_all(source, target, accuracy)
    if len(left_top_pos) == 0:
        return left_top_pos
    if return_center:
        return [image_center(target, pos) for pos in left_top_pos]
    else:
        return left_top_pos


def find_pics(source: Image.Image, *targets: Image.Image, return_center=False, accuracy=conf.get_cv_threshold()):
    for target in targets:
        pos = find_pic_max_pos(source, target, return_center, accuracy)
        if pos:
            return pos
    return None


def find_pic_either_touch(source: Image.Image, *targets: Image, accuracy=conf.get_cv_threshold()):
    for target in targets:
        if find_pic_touch(source, target, accuracy):
            return True
    return False


# 寻找目标区块并在其范围内随机点击
def find_pic_touch(source: Image.Image, target: Image.Image, accuracy=conf.get_cv_threshold(),
                   max_t=True, random_t=False, ranged_t=-1):
    pos = None
    if random_t or ranged_t >= 0:
        all_pos = find_pic_all_pos(source, target, return_center=True, accuracy=accuracy)
        log.debug("find_pic_touch all_pos: {}".format(all_pos))
        if all_pos and len(all_pos) > 0:
            if random_t:
                pos = random.choice(all_pos)
            elif ranged_t >= 0:
                pos = all_pos[ranged_t % len(all_pos)]
    elif max_t:
        pos = find_pic_max_pos(source, target, return_center=True, accuracy=accuracy)
    if pos is None:
        return False
    touch(pos)
    return True


ocr = CnOcr(rec_model_name="doc-densenet_lite_136-gru",
            rec_model_fp=os.path.join(conf.ocr_path, "doc-densenet_lite_136-v2.3.onnx"))
number_ocr = CnOcr(rec_model_name="number-densenet_lite_136-gru",
                   rec_model_fp=os.path.join(conf.ocr_path, "number-densenet_lite_136-v2.3.onnx"))


def find_text_all(source: Image.Image, *targets):
    result = ocr_with_cache(source)
    for target in targets:
        found = False
        for r in result:
            if target in r.get("text", ""):
                found = True
                break
        if not found:
            return False
    return True


def find_text_either(source: Image.Image, *targets, y_min=None, y_max=None):
    result = ocr_with_cache(source)
    for target in targets:
        rs = [r for r in result if target in r.get("text", "") and (not y_min or y_min <= r.get("position")[0][1]) and
              (not y_max or r.get("position")[2][1] <= y_max)]
        if len(rs) > 0:
            return True
    return False


def find_text_touch(source: Image.Image, target, index=0, rand=True, y_min=None, y_max=None):
    result = ocr_with_cache(source)
    if rand:
        random.shuffle(result)
    else:
        result.sort(key=lambda r: r.get("position")[0][0])
    rs = [r for r in result if target in r.get("text", "") and (not y_min or y_min <= r.get("position")[0][1]) and
          (not y_max or r.get("position")[2][1] <= y_max)]
    if len(rs) == 0:
        return False
    r = rs[index % len(rs)]
    pos = r.get('position')
    center = (pos[0][0] + pos[2][0]) / 2, (pos[0][1] + pos[2][1]) / 2
    # print(center)
    touch(center)
    return True


def get_texts(source: Image.Image, sort_pos=False, merge=False):
    result = ocr_with_cache(source)
    if sort_pos:
        result = sorted(result, key=lambda x: x.get('position')[0][0])
    if merge:
        return "".join([r.get('text') for r in result])
    return [r.get('text') for r in result]


def recognize_number(source: Image.Image):
    result = number_ocr.ocr(source)
    log.debug("number_ocr result: {}".format(result))
    for r in result:
        return int(r.get('text'))
    return 0


def screen_picture():
    capture_file_name = "screen.png"
    if conf.get_capture_log_switch():
        capture_file_name = datetime.now().strftime("%H_%M_%S") + "_" + capture_file_name
    image = os.path.join(conf.cache_dir, capture_file_name)
    if os.path.isfile(image):
        os.remove(image)
    return adb_helper.screen_capture(image)


# 从source图片中查找wanted图片所在的位置，当置信度大于accuracy时返回找到的最大置信度位置的左上角坐标
def locate(source: Image.Image, wanted: Image.Image, accuracy=0.90):
    screen_cv2 = cv2.cvtColor(numpy.array(source), cv2.COLOR_RGB2BGR)
    wanted_cv2 = cv2.cvtColor(numpy.array(wanted), cv2.COLOR_RGB2BGR)

    result = cv2.matchTemplate(screen_cv2, wanted_cv2, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    log.debug("locate: {},{},{},{}".format(min_val, max_val, min_loc, max_loc))

    if max_val >= accuracy:
        return max_loc
    else:
        return None


def locate_all(source: Image.Image, wanted: Image.Image, accuracy=0.90):
    loc_pos = []
    screen_cv2 = cv2.cvtColor(numpy.array(source), cv2.COLOR_RGB2BGR)
    wanted_cv2 = cv2.cvtColor(numpy.array(wanted), cv2.COLOR_RGB2BGR)

    result = cv2.matchTemplate(screen_cv2, wanted_cv2, cv2.TM_CCOEFF_NORMED)
    location = numpy.where(result >= accuracy)

    ex, ey = 0, 0
    for pt in zip(*location[::-1]):
        x = pt[0]
        y = pt[1]

        if (x - ex) + (y - ey) < 15:  # 去掉邻近重复的点
            continue
        ex, ey = x, y

        loc_pos.append([int(x), int(y)])

    return loc_pos


# 给定目标尺寸大小和目标左上角顶点坐标，即可给出目标中心的坐标
def image_center(img: Image.Image, top_left_pos):
    tlx, tly = top_left_pos
    if tlx < 0 or tly < 0 or img.width <= 0 or img.height <= 0:
        return None
    return tlx + img.width / 2, tly + img.height / 2


def save_image(img: Image.Image, filename):
    path = os.path.join(conf.cache_dir, filename + ".png")
    img.save(path)


def delete_expired_files():
    for f in os.listdir(conf.cache_dir):
        file_path = os.path.join(conf.cache_dir, f)
        if os.stat(file_path).st_mtime < time.time() - 3600:
            if os.path.isfile(file_path):
                os.remove(file_path)


def crop_image(img: Image.Image, left_top_pos, right_bottom_pos):
    tlx, tly = left_top_pos
    rbx, rby = right_bottom_pos
    return img.crop((tlx, tly, rbx, rby))


class ImageHash:
    def __init__(self, image: Image):
        self.image = image

    def __hash__(self):
        return dhash.dhash_int(self.image)

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()


def ocr_with_cache(image):
    return ocr_with_hash(ImageHash(image))


@lru_cache(maxsize=1)
def ocr_with_hash(image: ImageHash):
    result = ocr.ocr(image.image)
    log.debug("get_texts result: {}".format(result))
    return result


def clear_ocr_cache():
    ocr_with_hash.cache_clear()
