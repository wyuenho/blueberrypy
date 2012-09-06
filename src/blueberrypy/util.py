import copy
import hashlib
import hmac
import textwrap
import warnings

from base64 import b64encode, urlsafe_b64encode

try:
    import simplejson as json
except ImportError:
    import json

from datetime import date, time, datetime, timedelta

from dateutil.parser import parse as parse_date

try:
    from sqlalchemy.orm import RelationshipProperty, Session, collections
except ImportError:
    sqlalchemy_support = False
else:
    sqlalchemy_support = True

try:
    from geoalchemy.base import SpatialElement, WKTSpatialElement
    from shapely.geometry import asShape, mapping as asGeoJSON
    from shapely.wkb import loads as wkb_decode
    from shapely.wkt import loads as wkt_decode
except ImportError:
    geos_support = False
else:
    geos_support = True


__all__ = ["to_collection", "to_mapping", "from_mapping", "CSRFToken",
           "pad_block_cipher_message", "unpad_block_cipher_message"]


def _get_model_properties(model, excludes, recursive=False):
    props = {}
    for prop in model.__mapper__.iterate_properties:
        if isinstance(prop, RelationshipProperty):
            if recursive:
                props[prop.key] = prop
                if prop.backref:
                    backref_prop_key = prop.backref[0]
                    for mapper in prop.mapper.polymorphic_iterator():
                        excludes.setdefault(mapper.class_, set()).add(backref_prop_key)
        else:
            if prop.key.startswith("_"):
                props[prop.columns[0].key] = prop
            else:
                props[prop.key] = prop
    return props

def _ensure_is_dict(key, inc_exc):

    if inc_exc:
        inc_exc = copy.deepcopy(inc_exc)

        if isinstance(inc_exc, basestring):
            inc_exc = {key: set([inc_exc])}
        elif isinstance(inc_exc, (list, tuple, set, frozenset)):
            inc_exc = {key: set(iter(inc_exc))}
        elif not isinstance(inc_exc, dict):
            raise TypeError(inc_exc, "Please provide a string, an iterable or a dict")

        return inc_exc

    return {}

def to_mapping(value, includes=None, excludes=None, format=None, recursive=False, **json_kwargs):
    warnings.warn("to_mapping() is deprecated and will be removed in 0.6, please use to_collection() instead.")
    return to_collection(value, includes=includes, excludes=excludes, format=format,
                         recursive=recursive, **json_kwargs)

def to_collection(from_, includes=None, excludes=None, format=None, recursive=False, **json_kwargs):
    """Utility function to convert complex values and SQLAlchemy declarative model objects to a Python collection.
    
    This function generally works very similar to `json.dump()`, with the
    following enhancements:
    
    SQLAlchemy declarative model
    ----------------------------
    If `from_` is a SQLAlchemy declarative model object (identified by the
    existance of a `__mapper__` attribute), or a collection if it,
    `to_collection()` will iterate through all the value's mapped properties
    and put the mapped property's name and its value into the result object to
    be returned. In addition to basic Python data types, this function will
    convert `datetime` values according to the following table:

    ========== =========== =============
    value type result key  result value
    ========== =========== =============
    datetime   datetime    .isoformat()
    time       time        .isoformat()
    date       date        .isoformat()
    timedelta  interval    .seconds
    ========== =========== =============
    
    Furthermore, GeoAlchemy `SpatialElement values are also converted to
    `geojson <http://geojson.org/>`_ format using
    `Shapely <http://toblerity.github.com/shapely/>_`.
    
    If `includes` is provided, additional attribute(s) in the model value(s)
    will be included in the returned result. `includes` can be a string, an
    iterable of strings, or a mapping of classes to iterables of strings. This
    is usually used for getting the values of the un-mapped properties from the
    model instances.
    
    If `excludes` is provided, which can also be a string, an iterable of
    strings, or a mapping of classes to iterables of strings, the attribute(s)
    will be excluded from the returned result.
    
    Internally, `to_collection()` will convert the provided `includes` and
    `excludes` property sets to a mapping of the classes of the values to lists
    of property key strings.
    
    **Note:** Mapped property names starting with '_' will never be included in the
    returned result.

    If `recursive` is True, `to_collection` will recursively traverse the entire
    object graph of the values and return a result representing the entire
    object tree. The backrefs of the relationship properties will be
    automatically added to the `excludes` set to prevent running into an
    infinite loop. If you set `recursive` to True, and also supply either an
    `includes` or `excludes` property sets, it is encouraged that you provide
    mappings for explicitness.

    Complex values
    --------------
    If `from_` is not a a SQLAlchemy declarative model, it must be a Python
    collection and its elements are processed according to the same logic as
    SQLAlchemy mode. If `from_` is a collection, this function will recursively
    convert all elements if `recursive` is True. `includes` and `excludes` will
    have no effect under this mode unless some decendent objects are SQLAlchemy
    declarative model objects, in which case processing will be the same as
    described above.
    
    **Note:** If `from_` is an instance of a dict its keys will be converted to
    a string regardless. All iterables besides a dict is returned as a list.
    
    
    If `format` is the string `json`, the result returned will be a JSON string
    , otherwise a Python collection object will be returned.
    
    If any `json_kwargs` is provided, they will be passed through to the
    underlying simplejson JSONDecoder.
    
    Examples:
    ---------
    >>> to_collection(legco) #doctest: +SKIP
    {'name': 'Hong Kong Legislative Council Building', 'founded': {'date': '1912-01-15'}, 'location': {'type': 'Point', 'coordinates': (22.280909, 114.160349)}}
    
    >>> to_collection(legco, excludes=['founded', 'location']) #doctest: +SKIP
    {'name': 'Hong Kong Legislative Council Building'}
    
    >>> to_collection(legco, excludes='founded', format='json') #doctest: +SKIP
    '{"name": "Hong Kong Legislative Council Building", 'location': {'type': 'Point', 'coordinates': [22.280909, 114.160349]}}'
    
    >>> to_collection([legco, hkpark], recursive=True, included={Location: set(['founded'])}) #doctest: +SKIP
    [{'name': 'Hong Kong Legislative Council Building', 'founded': {'date': '1912-01-15'}, 'location': {'type': 'Point', 'coordinates': (22.280909, 114.160349)}},
    {'name': 'Hong Kong Park', 'founded': {'date': '1991-05-23'}, 'location': {'type': 'Point', 'coordinates': [22.2771398, 114.1613993]}}]
    """
    if hasattr(from_, "__mapper__"):

        if not sqlalchemy_support:
            raise ImportError(textwrap.dedent("""SQLAlchemy not installed.

            Please use install it first before proceding:

            $ pip install sqlalchemy
            """))

        includes = _ensure_is_dict(from_.__class__, includes)
        excludes = _ensure_is_dict(from_.__class__, excludes)

        props = _get_model_properties(from_, excludes, recursive=recursive)
        attrs = set(props.iterkeys())
        if includes and from_.__class__ in includes:
            attrs |= includes[from_.__class__]
        if excludes and from_.__class__ in excludes:
            attrs -= excludes[from_.__class__]

        result = {}
        for attr in attrs:
            if not attr.startswith("_"):
                val = getattr(from_, attr)
                val = to_collection(val, includes=includes, excludes=excludes, recursive=recursive)
                result[attr] = val
    else:
        if isinstance(from_, datetime):
            result = {"datetime": from_.isoformat()}
        elif isinstance(from_, time):
            result = {"time": from_.isoformat()}
        elif isinstance(from_, date):
            result = {"date": from_.isoformat()}
        elif isinstance(from_, timedelta):
            result = {"interval": from_.seconds}
        elif geos_support and isinstance(from_, SpatialElement):
            if isinstance(from_, WKTSpatialElement):
                result = asGeoJSON(wkt_decode(from_.geom_wkt))
            else:
                result = asGeoJSON(wkb_decode(str(from_.geom_wkb)))
        elif isinstance(from_, dict):
            result = {}
            for k, v in from_.items():
                result[unicode(k)] = to_collection(v, includes=includes, excludes=excludes, recursive=recursive)
        elif hasattr(from_, "__iter__"): # iterable collections, not strings
            result = [to_collection(v, includes=includes, excludes=excludes, recursive=recursive)
                      for v in from_] if recursive else list(from_)
        else:
            result = from_

    if format == "json":
        return json.dumps(result, **json_kwargs)

    return result

def from_mapping(mapping, instance, excludes=None, format=None):
    warnings.warn("from_mapping() is deprecated and will be removed in 0.6, please use from_collection() instead.")
    return from_collection(mapping, instance, excludes=excludes, format=format)

def _get_property_instance(session, mapping, prop):
    prop_cls = prop.mapper.class_
    prop_pk_vals = tuple((mapping[pk_col.key] for pk_col in prop.mapper.primary_key if pk_col.key in mapping))
    if prop_pk_vals:
        prop_inst = session.query(prop_cls).get(prop_pk_vals)
    elif prop.mapper.polymorphic_on is not None:
        prop_inst = prop.mapper.polymorphic_map[mapping[prop.mapper.get_property_by_column(prop.mapper.polymorphic_on).key]].class_()
    else:
        prop_inst = prop_cls()
    return prop_inst

def from_collection(from_, to_, excludes=None, format=None, collection_handling="replace"):
    """Utility function to recursively apply data in a Python collection to SQLAlchemy declarative model objects.
    
    This function takes a `from_` and an `to_` and sets the attributes on the
    SQLAlchemy declarative model instance using the key-value pairs from the
    collection **inplace**.
    
    If `excludes` is provided, it works similarily as `to_collection`.
    
    If `format` is the string `json`, the mapping returned will be a JSON
    string, otherwise the mapped model(s) will be returned.
    
    If `collection_handling` is `replace`, which is the default, all the
    supplied relationship mappings will be converted to the correct subclass
    instances and replace the entire relationship collection on the parent
    objects. If the value is `append`, the mapped model instance will be
    appended to the relationship collection instead.
    
    If a key from the mapping is not found as a column on a model instance, it
    will simply be skipped and not set on the instance.
    
    The values supplied is converted according to the similiar rules as
    `to_collection()`:
    
    ============== ============================================
    column type    mapping value format
    ============== ============================================
    datetime       {"datetime": "ISO-8601"}
    time           {"time": "ISO-8601"}
    date           {"date": "ISO-8601"}
    timedelta      {"interval": seconds}
    SpatialElement GeoJSON
    ============== ============================================
    
    **Security Notice:** This function currently does not yet have integration 
    support for data validation. If you are using this function to directly 
    mass-assign user supplied data to your model instances, make sure you have 
    validated the data first. In a future version of blueberrypy, integration 
    with a form validation library will be provided to ease this process. 
    """
    if format == "json":
        from_ = json.loads(from_)

    if not isinstance(from_, dict):
        if hasattr(from_, "__iter__"):
            if not hasattr(to_, "__iter__"):
                raise TypeError("to_ must be an iterable if from_ is an iterable.")
            elif len(from_) != len(to_):
                raise ValueError("length of to_ must match length of from_.")

    if collection_handling != "replace" and collection_handling != "append":
        raise ValueError("collection_handling must be 'replace' or 'append'.")

    excludes = _ensure_is_dict(to_.__class__, excludes)

    if isinstance(from_, dict):
        if isinstance(to_, dict):
            for k in to_.iterkeys():
                if k in from_:
                    to_[k] = from_collection(from_[k], to_[k], excludes=excludes)
        elif hasattr(to_, "__mapper__"):

            if not sqlalchemy_support:
                raise ImportError(textwrap.dedent("""SQLAlchemy not installed.
    
                Please use install it first before proceding:
    
                $ pip install sqlalchemy
                """))

            props = _get_model_properties(to_, excludes, recursive=True)
            attrs = set(props.iterkeys())
            if excludes and to_.__class__ in excludes:
                attrs -= excludes[to_.__class__]

            for attr in attrs:
                if attr in from_:
                    prop = props[attr]
                    from_val = from_[attr]
                    if isinstance(prop, RelationshipProperty):
                        if not isinstance(from_val, list) and not isinstance(from_val, dict):
                            raise ValueError("%r must be either a list or a dict" % attr)

                        if prop.uselist is None or prop.uselist:

                            if collection_handling == "replace":
                                col = collections.prepare_instrumentation(prop.collection_class or list)()
                            elif collection_handling == "append":
                                col = getattr(to_, attr)

                            appender = col._sa_appender

                            from_iterator = iter(from_val) if isinstance(from_val, list) else from_val.itervalues()

                            for v in from_iterator:
                                prop_inst = _get_property_instance(Session.object_session(to_), v, prop)
                                appender(from_collection(v, prop_inst, excludes=excludes))

                            if collection_handling == "replace":
                                setattr(to_, attr, col)
                        else:
                            prop_inst = _get_property_instance(Session.object_session(to_), from_val, prop)
                            setattr(to_, attr, from_collection(from_val, prop_inst, excludes=excludes))
                    else:
                        setattr(to_, attr, from_collection(from_val, None, excludes=excludes))
        else:
            if "date" in from_:
                to_ = parse_date(from_["date"]).date()
            elif "time" in from_:
                to_ = parse_date(from_["time"]).time()
            elif "datetime" in from_:
                to_ = parse_date(from_["datetime"])
            elif "interval" in from_:
                to_ = timedelta(seconds=from_["interval"])
            elif geos_support and "type" in from_:
                to_ = WKTSpatialElement(asShape(from_).wkt)

    elif hasattr(from_, "__iter__") and hasattr(to_, "__iter__"):
        to_ = [from_collection(f, t, excludes=excludes) for f, t in zip(from_, to_)]

    else:
        to_ = from_

    return to_


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
