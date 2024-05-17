import pyautogui


def touch(pos):
    pyautogui.click(pos[0], pos[1])


def drag(start, end, duration=0):
    pyautogui.dragTo(start[0], start[1], end[0], end[1], duration)


def screen_capture(image):
    return pyautogui.screenshot(image)
