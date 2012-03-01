import hashlib
import hmac

from base64 import b64encode, urlsafe_b64encode

try:
    import simplejson as json
except ImportError:
    import json

from datetime import date, time, datetime

from dateutil.parser import parse as parse_date
from cherrypy import HTTPError

try:
    from geoalchemy.base import SpatialElement
    from shapely.geometry import asShape, mapping as asGeoJSON
except ImportError:
    geos_support = False

    class SpatialElement:
        pass

    def asShape(d):
        pass

    def asGeoJSON(d):
        pass
else:
    geos_support = True

def to_json(instance, includes=None, excludes=None, serialize=False):

    includes = set([includes] if isinstance(includes, basestring) else includes and list(includes) or [])
    excludes = set([excludes] if isinstance(excludes, basestring) else excludes and list(excludes) or [])
    attrs = set(instance.__table__.c.keys())
    attrs = includes | attrs - excludes

    doc = {}
    for k in attrs:
        v = getattr(instance, k)
        if not k.startswith("_") and not isinstance(v, (tuple, list, set, frozenset, dict)):
            if isinstance(v, datetime):
                v = {"datetime": v.isoformat()}
            elif isinstance(v, time):
                v = {"time": v.isoformat()}
            elif isinstance(v, date):
                v = {"date": v.isoformat()}
            elif geos_support and isinstance(v, SpatialElement):
                v = asGeoJSON(v)
            doc[k] = v

    if serialize:
        return json.dumps(doc)
    return doc

def from_json(doc, instance, includes=None, excludes=None):

    if isinstance(doc, basestring):
        doc = json.loads(doc)

    if not isinstance(doc, dict):
        raise TypeError(doc, "doc must be a dict")

    includes = set([includes] if isinstance(includes, basestring) else includes and list(includes) or [])
    excludes = set([excludes] if isinstance(excludes, basestring) else excludes and list(excludes) or [])
    attrs = set(instance.__table__.c.keys())
    attrs = includes | attrs - excludes

    for k, v in doc.iteritems():

        if k in attrs:
            if isinstance(v, dict):
                if "date" in v:
                    v = parse_date(v["date"])
                elif "time" in v:
                    v = parse_date(v["time"])
                elif "datetime" in v:
                    v = parse_date(v["datetime"])
                elif geos_support and "type" in v:
                    v = asShape(v)

            setattr(instance, k, v)
        else:
            raise HTTPError(400)

    return instance


class CSRFToken(object):

    def __init__(self, path, secret, session_id, urlsafe=False):
        self.path = str(path)
        self.secret = str(secret)
        self.session_id = str(session_id)
        self.urlsafe = urlsafe
        self.token = self.generate(urlsafe)

    def generate(self, urlsafe=False):
        mac = hmac.new(self.secret, digestmod=hashlib.sha256)
        mac.update(self.path)
        mac.update(self.session_id)

        if urlsafe or self.urlsafe:
            self.token = urlsafe_b64encode(mac.digest())
        else:
            self.token = b64encode(mac.digest())

        return self.token

    def verify(self, other):
        return str(self) == str(other)

    def __str__(self):
        return self.token

    def __repr__(self):
        return "CSRFToken(%r, %r, %r, %r)" % (self.path, self.secret, self.session_id, self.urlsafe)


def pad_block_cipher_message(msg, block_size=16, padding='{'):
    return msg + (block_size - len(msg) % block_size) * padding

def unpad_block_cipher_message(msg, padding="{"):
    return msg.rstrip(padding)
