import cPickle as pickle
import logging
import threading
import time

from pprint import pformat

from cherrypy.lib import sessions
from redis import StrictRedis as _RedisClient


__all__ = ["RedisSession"]


logger = logging.getLogger(__name__)


def normalize_sep(prefix, sep=':'):

    prefix = str(prefix)

    if not prefix.endswith(sep):
        return prefix + sep
    else:
        return prefix.rstrip(':') + ':'


class RedisSession(sessions.Session):

    locks = {}

    prefix = "cp-session:"

    debug = False

    @classmethod
    def setup(cls, **kwargs):

        cls.prefix = normalize_sep(kwargs.pop("prefix", cls.prefix))

        for k, v in kwargs.items():
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
            retval = pickle.loads(data)
            return retval

    def _save(self, expiration_time):
        key = self.prefix + self.id
        td = int(time.mktime(expiration_time.timetuple()))

        data = pickle.dumps((self._data, expiration_time),
                            pickle.HIGHEST_PROTOCOL)

        def critical_section(pipe):
            pipe.multi()
            pipe.set(key, data)
            pipe.expireat(key, td)

        self.cache.transaction(critical_section, key)

    def _delete(self):
        self.cache.delete(self.prefix + self.id)

    def acquire_lock(self):
        self.locked = True
        self.locks.setdefault(self.id, threading.RLock()).acquire()

    def release_lock(self):
        self.locks[self.id].release()
        self.locked = False

    def __len__(self):
        """Return the number of active sessions."""
        keys = self.cache.keys(self.prefix + '*')
        return len(keys)
