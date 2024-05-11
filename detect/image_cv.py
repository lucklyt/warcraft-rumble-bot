from PIL import Image
import numpy as np
import cv2


def detect_grey_blocks(img: Image.Image, min_area=10000):
    # Reading the video from the
    # webcam in image frames
    cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    hsv_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2HSV)

    grey_lower = np.array([16, 29, 0], np.uint8)
    grey_upper = np.array([28, 63, 255], np.uint8)
    grey_mask = cv2.inRange(hsv_img, grey_lower, grey_upper)

    # Morphological Transform, Dilation
    # for each color and bitwise_and operator
    # between imageFrame and mask determines
    # to detect only that particular color
    kernel = np.ones((5, 5), "uint8")

    grey_mask = cv2.dilate(grey_mask, kernel)

    # Creating contour to track grey color
    contours, hierarchy = cv2.findContours(grey_mask,
                                           cv2.RETR_TREE,
                                           cv2.CHAIN_APPROX_SIMPLE)

    results = []
    for pic, contour in enumerate(contours):
        area = cv2.contourArea(contour)
        if area > min_area:
            x, y, w, h = cv2.boundingRect(contour)
            results.append((int(x + w / 2), int(y + h / 2)))
    return results


def detect_enemy_tag(img: Image.Image):
    # Reading the video from the
    # webcam in image frames
    cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    hsv_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2HSV)

    grey_lower = np.array([0, 187, 0], np.uint8)
    grey_upper = np.array([2, 195, 255], np.uint8)
    grey_mask = cv2.inRange(hsv_img, grey_lower, grey_upper)

    # Morphological Transform, Dilation
    # for each color and bitwise_and operator
    # between imageFrame and mask determines
    # to detect only that particular color
    kernel = np.ones((5, 5), "uint8")

    grey_mask = cv2.dilate(grey_mask, kernel)

    # Creating contour to track grey color
    contours, hierarchy = cv2.findContours(grey_mask,
                                           cv2.RETR_TREE,
                                           cv2.CHAIN_APPROX_SIMPLE)

    results = []
    for pic, contour in enumerate(contours):
        area = cv2.contourArea(contour)
        if 20 < area < 1500:
            x, y, w, h = cv2.boundingRect(contour)
            if 20 <= h <= 30:
                results.append((int(x + w / 2), int(y + h / 2)))
    return results


def detect_defensive_structure(img: Image.Image):
    cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    hsv_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2HSV)

    grey_lower = np.array([96, 58, 133], np.uint8)
    grey_upper = np.array([117, 228, 255], np.uint8)
    grey_mask = cv2.inRange(hsv_img, grey_lower, grey_upper)

    # Morphological Transform, Dilation
    # for each color and bitwise_and operator
    # between imageFrame and mask determines
    # to detect only that particular color
    kernel = np.ones((5, 5), "uint8")

    grey_mask = cv2.dilate(grey_mask, kernel)

    # Creating contour to track grey color
    contours, hierarchy = cv2.findContours(grey_mask,
                                           cv2.RETR_TREE,
                                           cv2.CHAIN_APPROX_SIMPLE)
    for pic, contour in enumerate(contours):
        area = cv2.contourArea(contour)
        if area < 400:
            cv2.fillPoly(grey_mask, pts=[contour], color=0)

    grey_mask = cv2.morphologyEx(grey_mask, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (100, 100)))
    contours, hierarchy = cv2.findContours(grey_mask,
                                           cv2.RETR_TREE,
                                           cv2.CHAIN_APPROX_SIMPLE)

    results = []
    for pic, contour in enumerate(contours):
        area = cv2.contourArea(contour)
        if 4000 < area < 30000:
            x, y, w, h = cv2.boundingRect(contour)
            results.append((int(x + w / 2), int(y + h / 2)))
    return results
