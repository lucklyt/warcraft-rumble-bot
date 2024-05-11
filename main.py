# @formatter:off
from process_control import main_process
import os
import sys
import yaml
from logging import handlers
import os
import subprocess
import time
from datetime import datetime
from adb_shell.auth.keygen import keygen
from dateutil import parser
from adb_shell import exceptions
from adb_shell.adb_device import AdbDeviceTcp
from adb_shell.auth.sign_pythonrsa import PythonRSASigner
from conf import conf
import logging
import os
import random
import re
import time
from datetime import datetime

import cv2
import numpy
from PIL import Image
from cnocr import CnOcr

from conf import conf
from emulator import adb_helper
import json
import logging
import os.path
from enum import Enum

from PIL import Image

from conf import conf
from emulator import script_helper
import datetime as dt
import logging
import os.path
import random
import time
from datetime import datetime
from operator import attrgetter

import parse
import pytz
from PIL import Image

import conf.conf as conf
from emulator import adb_helper
from emulator import script_helper as gamer
from emulator.units import Unit, PlacementState
from mail import mail
import argparse
from hashlib import md5

import machineid

import logging
from email.mime.text import MIMEText
from smtplib import SMTP_SSL
import logging
import os
import random
import sys
import time
import traceback
from conf import conf
from emulator import script_helper as gamer
from emulator import warcraft, energy, battle
from functools import lru_cache
import dhash
import webview
import detect.image_cv
from multiprocessing import freeze_support
from conf.conf import log
if __name__ == "__main__":
    log.info("start app from script!")
    main_process.run()
