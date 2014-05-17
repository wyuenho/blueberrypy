try:
    import cPickle as pickle
except ImportError:
    import pickle

import logging
import math
import threading

from datetime import datetime
from pprint import pformat

from cherrypy.lib.sessions import Session
from redis import StrictRedis as _RedisClient


__all__ = ["RedisSession"]


logger = logging.getLogger(__name__)


def normalize_sep(prefix, sep=':'):

    prefix = str(prefix)

    if not prefix.endswith(sep):
        return prefix + sep
    else:
        return prefix.rstrip(':') + ':'


class RedisSession(Session):

    locks = {}

    prefix = "cp-session:"

    debug = False

    @classmethod
    def setup(cls, **kwargs):

        cls.prefix = normalize_sep(kwargs.pop("prefix", cls.prefix))

        for k, v in kwargs.viewitems():
            setattr(cls, k, v)
        cls.cache = cache = _RedisClient(**kwargs)
        redis_info = cache.info()
        if cls.debug:
            logger.info("Redis server ready.\n%s" % pformat(redis_info))
        else:
            logger.info("Redis server ready.")

    def _exists(self):
        return self.cache.exists(self.prefix + self.id)

    def _load(self):
        data = self.cache.get(self.prefix + self.id)
        if data:
            return pickle.loads(data)

    def _save(self, expiration_time):
        key = self.prefix + self.id
        seconds = int(math.ceil((expiration_time - datetime.now()).total_seconds()))
        data = pickle.dumps((self._data, expiration_time), pickle.HIGHEST_PROTOCOL)

        reply = self.cache.setex(key, seconds, data)
        if not reply:
            logger.error("Redis didn't reply for SETEX '{0}' '{1}' data".format(
                key, seconds))

    def _delete(self):
        self.cache.delete(self.prefix + self.id)

    def acquire_lock(self):
        """Acquire an exclusive lock on the currently-loaded session data."""
        self.locked = True
        self.locks.setdefault(self.id, threading.RLock()).acquire()
        if self.debug:
            logger.debug('Lock acquired.', 'TOOLS.SESSIONS')

    def release_lock(self):
        """Release the lock on the currently-loaded session data."""
        self.locks[self.id].release()
        self.locked = False

    def __len__(self):
        """Return the number of active sessions."""
        keys = self.cache.keys(self.prefix + '*')
        return len(keys)
