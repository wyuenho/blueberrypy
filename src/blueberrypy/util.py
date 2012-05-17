import copy
import hashlib
import hmac

from base64 import b64encode, urlsafe_b64encode

try:
    import simplejson as json
except ImportError:
    import json

from datetime import date, time, datetime, timedelta

from dateutil.parser import parse as parse_date

from sqlalchemy.orm import RelationshipProperty

try:
    from geoalchemy.base import SpatialElement, WKTSpatialElement
    from shapely.geometry import asShape, mapping as asGeoJSON
    from shapely.wkb import loads as wkb_decode
    from shapely.wkt import loads as wkt_decode
except ImportError:
    geos_support = False
else:
    geos_support = True


__all__ = ["to_mapping", "from_mapping", "CSRFToken",
           "pad_block_cipher_message", "unpad_block_cipher_message"]


def to_mapping(value, includes=None, excludes=None, format=None, **json_kwargs):
    """Utility function to convert a value to a mapping.
    
    This function has 2 modes:
        - SQLAlchemy declarative model -> mapping
        - complex value type (e.g. datetime types and GeoAlchemy SpatialElement) -> mapping
    
    SQLAlchemy declarative model
    ----------------------------
    If `value` is a SQLAlchemy declarative model value (identified by the
    existance of an `__table__` attribute), `to_mapping()` will iterate through
    all the value's column and put the column's name and its value into the
    mapping object to be returned. In addition to basic Python data types, this
    function will convert `datetime` values according to the following table:

    ========== =========== =============
    value type mapping key mapping value
    ========== =========== =============
    datetime   datetime    .isoformat()
    time       time        .isoformat()
    date       date        .isoformat()
    timedelta  interval    .seconds
    ========== =========== =============
    
    In additional to `datetime` values, GeoAlchemy `SpatialElement values are
    also converted to `geojson <http://geojson.org/>`_ format using
    `Shapely <http://toblerity.github.com/shapely/>_`.
    
    Under SQLalchemy mode, if `includes` is provided, additional attribute(s) in
    the model value will be included in the returned mapping. `includes` can be
    a string or a list of strings. If `excludes` is provided, which can also be
    a string or a list of strings, the attribute(s) will be exclude from the
    returned mapping.
    
    **Note:** columns with names starting with '_' and attributes that are
    containers (e.g. relationship attributes) will not be included in the
    returned mapping by default unless specified by `includes`.
    
    Complex values
    --------------
    If `value` is not a a SQLAlchemy declarative model, a shallow copy of it
    will be made and processed according to the same logic as SQLAlchemy mode's
    column values. Namely `datatime` values and GeoAlchemy SpatialElement values
    will be converted to their mapping representations.
    
    If `format` is the string `json`, the mapping returned will be a JSON string
    , otherwise a mapping object will be returned.
    
    If any `json_kwargs` is provided, they will be passed through to the
    underlying simplejson JSONDecoder.
    
    Examples:
    ---------
    >>> to_mapping(legco) #doctest: +SKIP
    {'name': 'Hong Kong Legislative Council Building', 'founded': {'date': '1912-01-15'}, 'location': {'type': 'Point', 'coordinates': (22.280909, 114.160349)}}
    
    >>> to_mapping(legco, excludes=['founded', 'location']) #doctest: +SKIP
    {'name': 'Hong Kong Legislative Council Building'}
    
    >>> to_mapping(legco, excludes=['founded'], format='json') #doctest: +SKIP
    '{"name": "Hong Kong Legislative Council Building", 'location': {'type': 'Point', 'coordinates': [22.280909, 114.160349]}}'
    """

    if hasattr(value, "__table__"):
        includes = set([includes] if isinstance(includes, basestring) else includes and list(includes) or [])
        excludes = set([excludes] if isinstance(excludes, basestring) else excludes and list(excludes) or [])
        attrs = set([prop.key for prop in value.__mapper__.iterate_properties if not isinstance(prop, RelationshipProperty)])
        attrs = includes | attrs - excludes

        mapping = {}
        for k in attrs:
            v = getattr(value, k)
            if not k.startswith("_") and not isinstance(v, (tuple, list, set, frozenset, dict)):
                if isinstance(v, datetime):
                    v = {"datetime": v.isoformat()}
                elif isinstance(v, time):
                    v = {"time": v.isoformat()}
                elif isinstance(v, date):
                    v = {"date": v.isoformat()}
                elif isinstance(v, timedelta):
                    v = {"interval": v.seconds}
                elif geos_support and isinstance(v, SpatialElement):
                    if isinstance(v, WKTSpatialElement):
                        v = asGeoJSON(wkt_decode(v.geom_wkt))
                    else:
                        v = asGeoJSON(wkb_decode(str(v.geom_wkb)))
                mapping[k] = v

        if format == "json":
            return json.dumps(mapping, **json_kwargs)
        return mapping
    else:
        v = copy.copy(value)
        if isinstance(v, datetime):
            v = {"datetime": v.isoformat()}
        elif isinstance(v, time):
            v = {"time": v.isoformat()}
        elif isinstance(v, date):
            v = {"date": v.isoformat()}
        elif isinstance(v, timedelta):
            v = {"interval": v.seconds}
        elif geos_support and isinstance(v, SpatialElement):
            if isinstance(v, WKTSpatialElement):
                v = asGeoJSON(wkt_decode(v.geom_wkt))
            else:
                v = asGeoJSON(wkb_decode(str(v.geom_wkb)))

        if format == "json":
            return json.dumps(v, **json_kwargs)
        return v

# TODO: add validators support
def from_mapping(mapping, instance, excludes=None, format=None):
    """Utility function to set the column values of a SQLAlchemy declarative
    model instance via a mapping.
    
    This function takes a `mapping` and an `instance` and sets the attributes
    on the SQLAlchemy declarative model instance using the key-value pairs from
    the mapping **inplace**.
    
    If `excludes` is provided, which can be a string or a list of strings, the
    attribute(s) in the mapping will *NOT* be set on the instance.
    
    If `format` is the string `json`, the mapping returned will be a JSON string
    , otherwise a mapping object will be returned.
    
    If a key from the mapping is not found as a column on the instance, it will
    simply be skipped and not set on the instance.
    
    The values supplied is converted according to the similiar rules as
    `to_mapping()`:
    
    ============== ============================================
    column type    mapping value format
    ============== ============================================
    datetime       {"datetime": "ISO-8601"}
    time           {"time": "ISO-8601"}
    date           {"date": "ISO-8601"}
    timedelta      {"interval": seconds}
    SpatialElement {"type": "Point", "coordinates": [lat, lng]}
    ============== ============================================
    
    **Security Notice:** This function currently does not yet have integration 
    support for data validation. If you are using this function to directly 
    mass-assign user supplied data to your model instances, make sure you have 
    validated the data first. In a future version of blueberrypy, integration 
    with a form validation library will be provided to ease this process.
    
    **Note:** If you supply collections values, the entire collection on the
    entity is replaced instead of merging.
    """

    if format == "json":
        mapping = json.loads(mapping)

    if not isinstance(mapping, dict):
        raise TypeError(mapping, "mapping must be a dict")

    excludes = set([excludes] if isinstance(excludes, basestring) else excludes and list(excludes) or [])
    attrs = set([prop.key for prop in instance.__mapper__.iterate_properties])
    attrs = attrs - excludes

    for k, v in mapping.iteritems():

        if k in attrs:
            if isinstance(v, dict):
                if "date" in v:
                    v = parse_date(v["date"]).date()
                    setattr(instance, k, v)
                elif "time" in v:
                    v = parse_date(v["time"]).time()
                    setattr(instance, k, v)
                elif "datetime" in v:
                    v = parse_date(v["datetime"])
                    setattr(instance, k, v)
                elif "interval" in v:
                    v = timedelta(seconds=v["interval"])
                    setattr(instance, k, v)
                elif geos_support and "type" in v:
                    v = asShape(v)
                    setattr(instance, k, WKTSpatialElement(v.wkt))
            else:
                setattr(instance, k, v)

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
