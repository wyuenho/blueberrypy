__version__ = "0.5"

import logging
import sys

logger = logging.getLogger(__name__)

logger.propagate = False
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
logger.addHandler(handler)
