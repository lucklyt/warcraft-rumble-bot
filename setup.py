from distutils.core import setup

from Cython.Build import cythonize

targets = ["conf/conf.py", "process_control/main_process.py", "emulator/warcraft.py", "emulator/adb_helper.py",
           "emulator/script_helper.py", "emulator/battle.py", "emulator/energy.py",
           "emulator/units.py", "mail/mail.py", "detect/image_cv.py"]

setup(name='warcraft_rumble',
      ext_modules=cythonize(targets))
