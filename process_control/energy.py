# cython: language_level=3
from conf.conf import log
import time

from PIL import Image
import os

from conf import conf
import numpy as np

from adaptor import emulator

nds = []


def get_nd(img):
    nd = np.eye(img.height, img.width)
    for i in range(0, img.height):  # process all pixels
        for j in range(0, img.width):
            data = img.getpixel((j, i))
            if data[0] < 230 and data[1] < 230 and data[2] < 230:
                nd[i][j] = 0
            else:
                nd[i][j] = 1
    return nd


size = (74, 74)
available_ec_pos = (-307, 1835)


def crop_ec(source, width):
    return source.crop((available_ec_pos[0] + width / 2, available_ec_pos[1],
                        available_ec_pos[0] + width / 2 + size[0], available_ec_pos[1] + size[1]))


for i in range(11):
    img = Image.open(os.path.join(conf.static_path, "energy/energy_{}.png".format(i)))
    img = crop_ec(img, 1080)
    nds.append(get_nd(img))


def similar(a, b):
    dot_product = np.dot(a, b)
    normal_a = np.linalg.norm(a)
    normal_b = np.linalg.norm(b)
    if normal_a * normal_b == 0:
        return 0
    return dot_product / (normal_a * normal_b)


def recognize(source):
    st = time.time()
    nd = get_nd(crop_ec(source, adb_helper.base_width))
    max_simi = 0
    max_x = 0
    for x in range(len(nds)):
        simi = similar(nd.ravel(), nds[x].ravel())
        if simi > max_simi:
            max_simi = simi
            max_x = x
        threshold = 0.99
        if adb_helper.ratio != 1.0:
            threshold = 0.8
        if simi >= threshold:
            log.debug("energy recognize {} latency {}".format(x, time.time() - st))
            return x
    log.debug("energy recognize unknown {}:{}".format(max_x,max_simi))
    return -1
