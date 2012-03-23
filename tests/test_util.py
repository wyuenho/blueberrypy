import hashlib
import hmac
import unittest

if not hasattr(unittest.TestCase, "assertIn"):
    import unittest2 as unittest

from base64 import b64encode
from datetime import date, time, datetime, timedelta

import decorator
import testconfig

from sqlalchemy import Column, Integer, Date, DateTime, Time, Interval, \
    engine_from_config
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base

from blueberrypy.util import CSRFToken, pad_block_cipher_message, \
    unpad_block_cipher_message, from_json, to_json


engine = engine_from_config(testconfig.config["sqlalchemy_engine"], '')
Session = scoped_session(sessionmaker(engine))

Base = declarative_base()
Base.metadata.bind = engine

class TestEntity(Base):

    __tablename__ = 'testentity'

    id = Column(Integer, primary_key=True)
    date = Column(Date)
    time = Column(Time)
    datetime = Column(DateTime)
    interval = Column(Interval)

    @property
    def combined(self):
        return datetime.combine(self.date, self.time)


@decorator.decorator
def orm_session(func, *args, **kwargs):
    session = Session()
    try:
        return func(*args, **kwargs)
    except:
        raise
    finally:
        session.close()


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



class JSONUtilTest(unittest.TestCase):

    @classmethod
    @orm_session
    def setup_class(cls):
        TestEntity.metadata.create_all(engine)

        te = TestEntity(date=date(2012, 1, 1),
                        time=time(0, 0, 0),
                        datetime=datetime(2012, 1, 1, 0, 0, 0),
                        interval=timedelta(seconds=3600))

        session = Session()
        session.add(te)
        session.commit()
    setUpClass = setup_class

    @classmethod
    @orm_session
    def teardown_class(cls):
        TestEntity.metadata.drop_all(engine)
    testDownClass = teardown_class

    @orm_session
    def test_to_json(self):
        doc = {'date': {'date': '2012-01-01'},
               'time': {'time': '00:00:00'},
               'interval': {'interval': 3600},
               'id': 1,
               'datetime': {'datetime': '2012-01-01T00:00:00'}}

        session = Session()
        te = session.query(TestEntity).one()
        result = to_json(te)

        self.assertEqual(doc, result)

        serialized_doc = '{"date": {"date": "2012-01-01"}, "time": {"time": "00:00:00"}, "interval": {"interval": 3600}, "id": 1, "datetime": {"datetime": "2012-01-01T00:00:00"}}'
        self.assertEqual(serialized_doc, to_json(te, serialize=True))

        doc = {'date': {'date': '2012-01-01'},
               'time': {'time': '00:00:00'},
               'datetime': {'datetime': '2012-01-01T00:00:00'},
               'combined': {'datetime': '2012-01-01T00:00:00'}}

        self.assertEqual(doc, to_json(te, includes=["combined"], excludes=["id", "interval"]))

    @orm_session
    def test_from_json(self):

        doc = {'date': {'date': '2012-01-01'},
               'time': {'time': '00:00:00'},
               'interval': {'interval': 3600},
               'id': 1,
               'datetime': {'datetime': '2012-01-01T00:00:00'}}

        te = TestEntity()
        te = from_json(doc, te)
        self.assertEqual(te.date, date(2012, 1, 1))
        self.assertEqual(te.time, time(0, 0, 0))
        self.assertEqual(te.interval, timedelta(seconds=3600))
        self.assertEqual(te.datetime, datetime(2012, 1, 1, 0, 0, 0))
        self.assertEqual(te.id, 1)

        te = TestEntity()
        te = from_json(doc, te, excludes=["interval"])
        self.assertEqual(te.date, date(2012, 1, 1))
        self.assertEqual(te.time, time(0, 0, 0))
        self.assertIsNone(te.interval)
        self.assertEqual(te.datetime, datetime(2012, 1, 1, 0, 0, 0))
        self.assertEqual(te.id, 1)

        te = TestEntity()
        serialized_doc = '{"date": {"date": "2012-01-01"}, "time": {"time": "00:00:00"}, "interval": {"interval": 3600}, "id": 1, "datetime": {"datetime": "2012-01-01T00:00:00"}}'
        te = from_json(serialized_doc, te)


class BlockCipherPaddingTest(unittest.TestCase):

    def test_pad_block_cipher_message(self):
        padded_message = pad_block_cipher_message("message")
        self.assertEqual(padded_message, "message{{{{{{{{{")

    def test_unpad_block_cipher_message(self):
        self.assertEqual(unpad_block_cipher_message("message{{{{{{{{{"), "message")
