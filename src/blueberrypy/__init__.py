__version__ = "0.6"

import sys
import logging

if sys.version_info < (3, 3):
    try:
        import cdecimal
        sys.modules["decimal"] = cdecimal
    except:
        pass

logger = logging.getLogger(__name__)

# TODO: include a default logging config format for when no project logging config (commands)
logger.propagate = False
logger.setLevel(logging.INFO)

error_handler = logging.StreamHandler()
error_handler.setLevel(logging.WARNING)

info_handler = logging.StreamHandler(stream=sys.stdout)
info_handler.setLevel(logging.INFO)

logger.addHandler(error_handler)
logger.addHandler(info_handler)

warning_logger = logging.getLogger("py.warnings")
warning_logger.propagate = False
warning_logger.setLevel(logging.WARNING)
warning_logger.addHandler(error_handler)
