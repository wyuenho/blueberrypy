import functools
import hashlib
import hmac

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from base64 import b64encode
from datetime import date, time, datetime, timedelta

import testconfig

from geoalchemy import GeometryColumn, Point, WKTSpatialElement, GeometryDDL
from sqlalchemy import Column, Integer, Date, DateTime, Time, Interval, Enum, \
    ForeignKey, UnicodeText, engine_from_config
from sqlalchemy.orm import sessionmaker, scoped_session, relationship, backref
from sqlalchemy.ext.declarative import declarative_base

from blueberrypy.util import CSRFToken, pad_block_cipher_message, \
    unpad_block_cipher_message, from_collection, to_collection


engine = engine_from_config(testconfig.config["sqlalchemy_engine"], '')
Session = scoped_session(sessionmaker(engine))

Base = declarative_base()
metadata = Base.metadata
metadata.bind = engine


class RelatedEntity(Base):

    __tablename__ = "related"

    id = Column(Integer, autoincrement=True, primary_key=True)
    key = Column(UnicodeText)

    parent_id = Column(Integer, ForeignKey("testentity.id"))

    discriminator = Column("type", Enum("related", "relatedsubclass",
                                        name="searchoptiontype"))

    __mapper_args__ = {"polymorphic_on": discriminator,
                       "polymorphic_identity": "related"}


class RelatedEntitySubclass(RelatedEntity):

    __mapper_args__ = {"polymorphic_identity": "relatedsubclass"}

    subclass_prop = Column(UnicodeText)


# remember to setup postgis
class TestEntity(Base):

    __tablename__ = "testentity"

    discriminator = Column("type", Enum("base", "derived", name="entitytype"),
                           nullable=False)

    __mapper_args__ = {"polymorphic_on": discriminator,
                       "polymorphic_identity": "base"}

    id = Column(Integer, primary_key=True)
    date = Column(Date)
    time = Column(Time)
    datetime = Column(DateTime)
    interval = Column(Interval)
    geo = GeometryColumn(Point(2))

    @property
    def combined(self):
        return datetime.combine(self.date, self.time)

    related = relationship(RelatedEntity, backref=backref("parent"))


GeometryDDL(TestEntity.__table__)


class DerivedTestEntity(TestEntity):

    __tablename__ = "derivedtestentity"

    __mapper_args__ = {"polymorphic_identity": "derived"}

    id = Column(Integer, ForeignKey("testentity.id"), nullable=False,
                primary_key=True)

    derivedprop = Column(Integer)


def orm_session(func):
    def _orm_session(*args, **kwargs):
        session = Session()
        try:
            return func(*args, **kwargs)
        except:
            raise
        finally:
            session.close()
    return functools.update_wrapper(_orm_session, func)


class CSRFTokenTest(unittest.TestCase):

    def test_csrftoken(self):
        csrftoken = CSRFToken("/test", "secret", 1)

        mac = hmac.new("secret", digestmod=hashlib.sha256)
        mac.update("/test")
        mac.update('1')
        testtoken = b64encode(mac.digest())

        self.assertEqual(str(csrftoken), testtoken)
        self.assertTrue(csrftoken.verify(testtoken))

        mac = hmac.new("secret2", digestmod=hashlib.sha256)
        mac.update("/test")
        mac.update('1')
        testtoken = b64encode(mac.digest())

        self.assertNotEqual(str(csrftoken), testtoken)
        self.assertFalse(csrftoken.verify(testtoken))

        mac = hmac.new("secret", digestmod=hashlib.sha256)
        mac.update("/test2")
        mac.update('1')
        testtoken = b64encode(mac.digest())

        self.assertNotEqual(str(csrftoken), testtoken)
        self.assertFalse(csrftoken.verify(testtoken))

        mac = hmac.new("secret", digestmod=hashlib.sha256)
        mac.update("/test2")
        mac.update('2')
        testtoken = b64encode(mac.digest())

        self.assertNotEqual(str(csrftoken), testtoken)
        self.assertFalse(csrftoken.verify(testtoken))


class CollectionUtilTest(unittest.TestCase):

    @classmethod
    @orm_session
    def setup_class(cls):
        metadata.create_all(engine)

        te = DerivedTestEntity(id=1,
                               date=date(2012, 1, 1),
                               time=time(0, 0, 0),
                               derivedprop=2,
                               datetime=datetime(2012, 1, 1, 0, 0, 0),
                               interval=timedelta(seconds=3600),
                               geo=WKTSpatialElement("POINT(45.0 45.0)"))
        session = Session()
        session.add(te)

        te.related = [RelatedEntity(key=u"related1"),
                      RelatedEntitySubclass(key=u"related2", subclass_prop=u"sub1")]

        session.commit()

        te2 = TestEntity(id=2,
                         date=date(2013, 2, 2),
                         time=time(1, 1, 1),
                         datetime=datetime(2013, 2, 2, 1, 1, 1),
                         interval=timedelta(seconds=3601),
                         geo=WKTSpatialElement("POINT(46.0 44.0)"))

        session = Session()
        session.add(te2)

        te2.related = [RelatedEntity(key=u"related3"),
                      RelatedEntity(key=u"related4")]

        session.commit()
    setUpClass = setup_class

    @classmethod
    @orm_session
    def teardown_class(cls):
        metadata.drop_all(engine)
    testDownClass = teardown_class

    @orm_session
    def test_to_collection(self):

        self.assertEqual(1, to_collection(1))
        self.assertEqual(1.1, to_collection(1.1))
        self.assertEqual("str", to_collection("str"))
        self.assertEqual([1, 2, 3], to_collection([1, 2, 3]))
        self.assertEqual([1, 2, 3], to_collection((1, 2, 3)))
        self.assertEqual([1, 2, 3], to_collection(set([1, 2, 3])))
        self.assertEqual([1, 2, 3], to_collection(frozenset([1, 2, 3])))
        self.assertEqual({"1": [2]}, to_collection({1: [2]}))
        self.assertEqual({"a": [1, 2], "b": 2}, to_collection({"a": set([1, 2]), "b": 2}))

        doc = {'date': {'date': '2012-01-01'},
               'time': {'time': '00:00:00'},
               'interval': {'interval': 3600},
               'id': 1,
               'discriminator': 'derived',
               'derivedprop': 2,
               'datetime': {'datetime': '2012-01-01T00:00:00'},
               'geo': {'type': 'Point',
                       'coordinates': (45.0, 45.0)}}

        session = Session()
        te = session.query(TestEntity).get(1)
        result = to_collection(te)
        self.assertEqual(doc, result)

        doc = {'date': {'date': '2012-01-01'},
               'time': {'time': '00:00:00'},
               'interval': {'interval': 3600},
               'id': 1,
               'discriminator': 'derived',
               'derivedprop': 2,
               'datetime': {'datetime': '2012-01-01T00:00:00'},
               'geo': {'type': 'Point',
                       'coordinates': (45.0, 45.0)},
               'related': [{'id': 1,
                            'discriminator': 'related',
                            'key': u'related1',
                            'parent_id': 1},
                           {'id': 2,
                            'discriminator': 'relatedsubclass',
                            'key': u'related2',
                            'parent_id': 1,
                            'subclass_prop': u'sub1'}]}

        te = session.query(TestEntity).get(1)
        result = to_collection(te, recursive=True)
        self.assertEqual(doc, result)

        serialized_doc = '{"date": {"date": "2012-01-01"}, "datetime": {"datetime": "2012-01-01T00:00:00"}, "derivedprop": 2, "discriminator": "derived", "geo": {"coordinates": [45.0, 45.0], "type": "Point"}, "id": 1, "interval": {"interval": 3600}, "related": [{"discriminator": "related", "id": 1, "key": "related1", "parent_id": 1}, {"discriminator": "relatedsubclass", "id": 2, "key": "related2", "parent_id": 1, "subclass_prop": "sub1"}], "time": {"time": "00:00:00"}}'
        result = to_collection(te, format="json", recursive=True, sort_keys=True)
        self.assertEqual(serialized_doc, result)

        doc = {'date': {'date': '2012-01-01'},
               'time': {'time': '00:00:00'},
               'discriminator': 'derived',
               'datetime': {'datetime': '2012-01-01T00:00:00'},
               'combined': {'datetime': '2012-01-01T00:00:00'},
               'geo': {'type': 'Point', 'coordinates': (45.0, 45.0)}}

        self.assertEqual(doc, to_collection(te, includes=["combined"],
                                            excludes=["id", "interval", "derivedprop", "related"]))
        self.assertEqual("a", to_collection("a"))
        self.assertEqual(1, to_collection(1))
        self.assertEqual(1.1, to_collection(1.1))
        self.assertEqual({'date': '2012-01-01'}, to_collection(date(2012, 1, 1)))
        self.assertEqual({'time': '00:00:00'}, to_collection(time(0, 0, 0)))
        self.assertEqual({'interval': 3600}, to_collection(timedelta(seconds=3600)))
        self.assertEqual({'datetime': '2012-01-01T00:00:00'}, to_collection(datetime(2012, 1, 1, 0, 0, 0)))
        self.assertEqual({'type': 'Point', 'coordinates': (45.0, 45.0)}, to_collection(te.geo))

        tes = session.query(TestEntity).all()
        result = to_collection(tes, recursive=True,
                               includes={DerivedTestEntity: set(['combined'])},
                               excludes={DerivedTestEntity: set(['id', 'interval', 'derivedprop'])},
                               format="json", sort_keys=True)

        serialized_doc = '[{"combined": {"datetime": "2012-01-01T00:00:00"}, "date": {"date": "2012-01-01"}, "datetime": {"datetime": "2012-01-01T00:00:00"}, "discriminator": "derived", "geo": {"coordinates": [45.0, 45.0], "type": "Point"}, "related": [{"discriminator": "related", "id": 1, "key": "related1", "parent_id": 1}, {"discriminator": "relatedsubclass", "id": 2, "key": "related2", "parent_id": 1, "subclass_prop": "sub1"}], "time": {"time": "00:00:00"}}, {"date": {"date": "2013-02-02"}, "datetime": {"datetime": "2013-02-02T01:01:01"}, "discriminator": "base", "geo": {"coordinates": [46.0, 44.0], "type": "Point"}, "id": 2, "interval": {"interval": 3601}, "related": [{"discriminator": "related", "id": 3, "key": "related3", "parent_id": 2}, {"discriminator": "related", "id": 4, "key": "related4", "parent_id": 2}], "time": {"time": "01:01:01"}}]'
        self.assertEqual(serialized_doc, result)

    @orm_session
    def test_from_collection(self):

        self.assertEqual(1, from_collection(1, None))
        self.assertEqual(1.1, from_collection(1.1, None))
        self.assertEqual("str", from_collection("str", None))
        self.assertEqual([1, 2, 3], from_collection([1, 2, 3], [4, 5, 6]))
        self.assertEqual([1, 2, 3], from_collection((1, 2, 3), (4, 5, 6)))
        self.assertEqual([1, 2, 3], from_collection(set([1, 2, 3]), set([4, 5, 6])))
        self.assertEqual([1, 2, 3], from_collection(frozenset([1, 2, 3]), frozenset([4, 5, 6])))

        doc = {'date': {'date': '2012-01-01'},
               'time': {'time': '00:00:00'},
               'interval': {'interval': 3600},
               'id': 1,
               'derivedprop': 2,
               'datetime': {'datetime': '2012-01-01T00:00:00'},
               'geo': {'type': 'Point', 'coordinates': (45.0, 45.0)},
               'related': [{'key': u'key1', 'parent_id': 1, 'discriminator': 'related'},
                           {'key': u'key2', 'parent_id': 1, 'discriminator': 'relatedsubclass', 'subclass_prop': 'sub'}]}

        te = DerivedTestEntity()
        te = from_collection(doc, te)
        self.assertEqual(te.date, date(2012, 1, 1))
        self.assertEqual(te.time, time(0, 0, 0))
        self.assertEqual(te.interval, timedelta(seconds=3600))
        self.assertEqual(te.datetime, datetime(2012, 1, 1, 0, 0, 0))
        self.assertEqual(te.id, 1)
        self.assertEqual(te.derivedprop, 2)
        self.assertEqual(te.geo.geom_wkt, "POINT (45.0000000000000000 45.0000000000000000)")
        self.assertIsNone(te.related[0].id)
        self.assertEqual(te.related[0].parent_id, 1)
        self.assertEqual(te.related[0].key, "key1")
        self.assertEqual(te.related[0].discriminator, "related")
        self.assertIsNone(te.related[1].id)
        self.assertEqual(te.related[1].parent_id, 1)
        self.assertEqual(te.related[1].key, "key2")
        self.assertEqual(te.related[1].discriminator, "relatedsubclass")
        self.assertEqual(te.related[1].subclass_prop, "sub")

        #TODO: testing loading of persisted entity, json format, excludes
        doc = {'date': {'date': '2012-01-01'},
               'time': {'time': '00:00:00'},
               'interval': {'interval': 3600},
               'id': 1,
               'datetime': {'datetime': '2012-01-01T00:00:00'},
               'geo': {'type': 'Point', 'coordinates': (45.0, 45.0)},
               'related': [{'key': u'key1', 'parent_id': 1, 'discriminator': u'related', "id": 3}]}

        session = Session()
        te = session.query(TestEntity).get(2)
        te = from_collection(doc, te, excludes=["interval"])
        self.assertEqual(te.date, date(2012, 1, 1))
        self.assertEqual(te.time, time(0, 0, 0))
        self.assertEqual(te.interval, timedelta(seconds=3601))
        self.assertEqual(te.datetime, datetime(2012, 1, 1, 0, 0, 0))
        self.assertEqual(te.id, 1)
        self.assertEqual(te.geo.geom_wkt, "POINT (45.0000000000000000 45.0000000000000000)")
        self.assertEqual(te.related[0].parent_id, 1)
        self.assertEqual(te.related[0].key, u"key1")
        self.assertEqual(te.related[0].id, 3)
        self.assertEqual(te.related[0].discriminator, u"related")
        self.assertEqual(len(te.related), 1)
        self.assertIsNotNone(Session.object_session(te.related[0]))

        doc = {'related': [{'key': u'hello', 'parent_id': 1, 'discriminator': u'related'}]}
        te = from_collection(doc, te, collection_handling="append")
        self.assertEqual(len(te.related), 2)
        self.assertEqual(te.related[-1].key, u"hello")
        self.assertEqual(te.related[-1].parent_id, 1)
        self.assertEqual(te.related[-1].discriminator, "related")

        te = DerivedTestEntity()
        json_doc = '{"time": {"time": "00:00:00"}, "date": {"date": "2012-01-01"}, "geo": {"type": "Point", "coordinates": [45.0, 45.0]}, "interval": {"interval": 3600}, "datetime": {"datetime": "2012-01-01T00:00:00"}, "id": 1, "related": [{"parent_id": 1, "key": "key1", "discriminator": "related"}, {"parent_id": 1, "subclass_prop": "sub", "key": "key2", "discriminator": "relatedsubclass"}], "derivedprop": 2}'
        te = from_collection(json_doc, te, format="json")
        self.assertEqual(te.date, date(2012, 1, 1))
        self.assertEqual(te.time, time(0, 0, 0))
        self.assertEqual(te.interval, timedelta(seconds=3600))
        self.assertEqual(te.datetime, datetime(2012, 1, 1, 0, 0, 0))
        self.assertEqual(te.id, 1)
        self.assertEqual(te.derivedprop, 2)
        self.assertEqual(te.geo.geom_wkt, "POINT (45.0000000000000000 45.0000000000000000)")
        self.assertIsNone(te.related[0].id)
        self.assertEqual(te.related[0].parent_id, 1)
        self.assertEqual(te.related[0].key, "key1")
        self.assertEqual(te.related[0].discriminator, "related")
        self.assertIsNone(te.related[1].id)
        self.assertEqual(te.related[1].parent_id, 1)
        self.assertEqual(te.related[1].key, "key2")
        self.assertEqual(te.related[1].discriminator, "relatedsubclass")
        self.assertEqual(te.related[1].subclass_prop, "sub")


class BlockCipherPaddingTest(unittest.TestCase):

    def test_pad_block_cipher_message(self):
        padded_message = pad_block_cipher_message("message")
        self.assertEqual(padded_message, "message{{{{{{{{{")

    def test_unpad_block_cipher_message(self):
        self.assertEqual(unpad_block_cipher_message("message{{{{{{{{{"), "message")
