# @formatter:off
from process_control import main_process

from conf.conf import log
if __name__ == "__main__":
    log.info("start app from script!")
    main_process.run()
