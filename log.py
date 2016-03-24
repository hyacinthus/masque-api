import logging
import os
import sys

from config import LogConfig, FlaskConfig

# debug mode
if FlaskConfig.DEBUG:
    _screen_level = "DEBUG"
    _file_level = "DEBUG"
    _root_level = "DEBUG"
else:
    _screen_level = LogConfig.SCREEN_LEVEL
    _file_level = LogConfig.FILE_LEVEL
    _root_level = LogConfig.ROOT_LEVEL

# root log handler
root_log = logging.getLogger('masque')
root_log.setLevel(_root_level)
formatter = logging.Formatter('%(asctime)s - %(name)s - '
                              '%(levelname)s - %(message)s')
# screen handler
if _screen_level:
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(_screen_level)
    ch.setFormatter(formatter)
    root_log.addHandler(ch)
    root_log.debug("Logging %s level to screen", _screen_level)

# file handler
if LogConfig.PATH and _file_level:
    LOG_PATH = os.path.abspath(LogConfig.PATH)
    os.makedirs(os.path.realpath(LOG_PATH), exist_ok=True)
    LOG_FILE = os.path.join(LOG_PATH, 'server.log')
    fh = logging.FileHandler(LOG_FILE)
    fh.setLevel(_file_level)
    fh.setFormatter(formatter)
    root_log.addHandler(fh)
    root_log.debug("Logging %s level to %s", (_file_level,
                   LOG_FILE))

# db handler send to celery

# pubu handler send to celery

app_log = logging.getLogger('masque.app')
