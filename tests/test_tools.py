import unittest

if not hasattr(unittest.TestCase, "assertIn"):
    import unittest2 as unittest

try:
    import simplejson as json
except ImportError:
    import json

import cherrypy
from cherrypy import HTTPError, HTTPRedirect, InternalRedirect
from cherrypy.test import helper

from sqlalchemy import Column, Integer, Unicode, engine_from_config
from sqlalchemy.ext.declarative import declarative_base

from testconfig import config as testconfig

from blueberrypy.plugins import SQLAlchemyPlugin
from blueberrypy.tools import SQLAlchemySessionTool


def get_config(section_name):
    return dict([(str(k), v) for k, v in testconfig[section_name].iteritems()])

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(Unicode(128), nullable=False, unique=True)


class Address(Base):
    __tablename__ = 'address'
    id = Column(Integer, autoincrement=True, primary_key=True)
    address = Column(Unicode(128), nullable=False, unique=True)


class SQLAlchemySessionToolSingleEngineTest(helper.CPWebCase, unittest.TestCase):

    engine = engine_from_config(get_config('sqlalchemy_engine'), '')

    @classmethod
    def setup_class(cls):

        super(SQLAlchemySessionToolSingleEngineTest, cls).setup_class()

        User.metadata.create_all(cls.engine)
        Address.metadata.create_all(cls.engine)
    setUpClass = setup_class

    @classmethod
    def teardown_class(cls):

        super(SQLAlchemySessionToolSingleEngineTest, cls).teardown_class()

        User.metadata.drop_all(cls.engine)
        Address.metadata.drop_all(cls.engine)
    tearDownClass = teardown_class

    @staticmethod
    def setup_server():
        class SingleEngine(object):

            _cp_config = {'tools.orm_session.on': True,
                          'tools.orm_session.passable_exceptions': [HTTPRedirect, InternalRedirect]}

            def save_user_and_address(self):
                session = cherrypy.request.orm_session
                bob = User(name=u"joey")
                session.add(bob)
                hk = Address(address=u"United States")
                session.add(hk)
                session.commit()
            save_user_and_address.exposed = True

            def query_user(self):
                session = cherrypy.request.orm_session
                joey = session.query(User).filter_by(name=u'joey').one()
                assert isinstance(joey.name, unicode)
                return json.dumps({'id': joey.id, 'name': joey.name})
            query_user.exposed = True

            def query_addresss(self):
                session = cherrypy.request.orm_session
                us = session.query(Address).filter_by(address=u'United States').one()
                assert isinstance(us.address, unicode)
                return json.dumps({'id': us.id, 'address': us.address})
            query_addresss.exposed = True

            def raise_not_passable_exception_save(self):
                session = cherrypy.request.orm_session
                bob = User(name=u"bob")
                session.add(bob)
                raise ValueError
            raise_not_passable_exception_save.exposed = True

            def raise_not_passable_exception_query(self):
                session = cherrypy.request.orm_session
                bob = session.query(User).filter_by(name=u'bob').first()
                return json.dumps(None)
            raise_not_passable_exception_query.exposed = True

            def raise_passable_exception_save(self):
                session = cherrypy.request.orm_session
                bob = User(name=u"bob")
                session.add(bob)
                session.commit()
                raise HTTPRedirect('/')
            raise_passable_exception_save.exposed = True

            def raise_passable_exception_query(self):
                session = cherrypy.request.orm_session
                bob = session.query(User).filter_by(name=u'bob').first()
                return json.dumps({'id': bob.id, 'name': bob.name})
            raise_passable_exception_query.exposed = True

        saconf = {'sqlalchemy_engine': get_config('sqlalchemy_engine')}
        cherrypy.engine.sqlalchemy = SQLAlchemyPlugin(cherrypy.engine, saconf)
        cherrypy.tools.orm_session = SQLAlchemySessionTool()
        cherrypy.config.update({'engine.sqlalchemy.on': True})
        cherrypy.tree.mount(SingleEngine())

    def test_orm_session_tool_commit(self):
        self.getPage('/save_user_and_address')
        self.assertStatus(200)

    def test_orm_session_tool_query_user(self):
        self.getPage('/query_user')
        json_resp = json.loads(self.body)
        self.assertIn('id', json_resp)
        self.assertIn('name', json_resp)
        self.assertEqual(u'joey', json_resp['name'])
        self.assertStatus(200)

    def test_orm_session_tool_query_address(self):
        self.getPage('/query_addresss')
        json_body = json.loads(self.body)
        self.assertIn('id', json_body)
        self.assertIn('address', json_body)
        self.assertEqual(u'United States', json_body['address'])
        self.assertStatus(200)

    def test_raise_not_passable_exception(self):
        self.getPage('/raise_not_passable_exception_save')
        self.assertStatus(500)
        self.getPage('/raise_not_passable_exception_query')
        self.assertBody(json.dumps(None))
        self.assertStatus(200)

    def test_raise_passable_exception(self):
        self.getPage('/raise_passable_exception_save')
        self.assertStatus(303)
        self.getPage('/raise_passable_exception_query')
        json_resp = json.loads(self.body)
        self.assertIn('id', json_resp)
        self.assertIn('name', json_resp)
        self.assertEqual(u'bob', json_resp['name'])
        self.assertStatus(200)


class SQLAlchemySessionToolTwoPhaseTest(helper.CPWebCase, unittest.TestCase):

    engine = engine_from_config(get_config('sqlalchemy_engine'), '')
    engine_bindings = {User: engine, Address: engine}

    @classmethod
    def setup_class(cls):

        super(SQLAlchemySessionToolTwoPhaseTest, cls).setup_class()

        User.metadata.create_all(cls.engine)
        Address.metadata.create_all(cls.engine)
    setUpClass = setup_class

    @classmethod
    def teardown_class(cls):

        super(SQLAlchemySessionToolTwoPhaseTest, cls).teardown_class()

        User.metadata.drop_all(cls.engine_bindings[User])
        Address.metadata.drop_all(cls.engine_bindings[Address])
    tearDownClass = teardown_class

    @staticmethod
    def setup_server():

        class TwoPhase(object):

            _cp_config = {'tools.orm_session.on': True,
                          'tools.orm_session.passable_exceptions': [HTTPRedirect, InternalRedirect]}

            def save_user_and_address(self):
                session = cherrypy.request.orm_session
                alice = User(name=u"alice")
                session.add(alice)
                hk = Address(address=u"Hong Kong")
                session.add(hk)
                session.commit()
            save_user_and_address.exposed = True
            save_user_and_address._cp_config = {'tools.orm_session.bindings': [User, Address]}

            def query_user(self):
                session = cherrypy.request.orm_session
                alice = session.query(User).filter_by(name=u'alice').one()
                assert isinstance(alice.name, unicode)
                return json.dumps({'id': alice.id, 'name': alice.name})
            query_user.exposed = True
            query_user._cp_config = {'tools.orm_session.bindings': [User]}

            def query_addresss(self):
                session = cherrypy.request.orm_session
                hk = session.query(Address).filter_by(address=u'Hong Kong').one()
                assert isinstance(hk.address, unicode)
                return json.dumps({'id': hk.id, 'address': hk.address})
            query_addresss.exposed = True
            query_addresss._cp_config = {'tools.orm_session.bindings': [Address]}

            def raise_not_passable_exception_save(self):
                session = cherrypy.request.orm_session
                katy = User(name=u"katy")
                session.add(katy)
                raise HTTPError(400)
            raise_not_passable_exception_save.exposed = True
            raise_not_passable_exception_save._cp_config = {'tools.orm_session.bindings': [User]}

            def raise_not_passable_exception_query(self):
                session = cherrypy.request.orm_session
                katy = session.query(User).filter_by(name=u'katy').first()
                if katy is not None:
                    return json.dumps({'id': katy.id, 'name': katy.name})
                else:
                    return json.dumps(None)
            raise_not_passable_exception_query.exposed = True
            raise_not_passable_exception_query._cp_config = {'tools.orm_session.bindings': [User]}

            def raise_passable_exception_save(self):
                session = cherrypy.request.orm_session
                david = User(name=u"david")
                session.add(david)
                session.commit()
                raise HTTPRedirect('/')
            raise_passable_exception_save.exposed = True
            raise_passable_exception_save._cp_config = {'tools.orm_session.bindings': [User]}

            def raise_passable_exception_query(self):
                session = cherrypy.request.orm_session
                david = session.query(User).filter_by(name=u'david').first()
                return json.dumps({'id': david.id, 'name': david.name})
            raise_passable_exception_query.exposed = True
            raise_passable_exception_query._cp_config = {'tools.orm_session.bindings': [User]}

        saconf = {'sqlalchemy_engine_tests.test_tools.User': get_config('sqlalchemy_engine'),
                  'sqlalchemy_engine_tests.test_tools.Address': get_config('sqlalchemy_engine')}
        cherrypy.engine.sqlalchemy = SQLAlchemyPlugin(cherrypy.engine, saconf)
        cherrypy.tools.orm_session = SQLAlchemySessionTool()
        cherrypy.config.update({'engine.sqlalchemy.on': True})
        cherrypy.tree.mount(TwoPhase())

    def test_orm_session_tool_commit(self):
        self.getPage('/save_user_and_address')
        self.assertStatus(200)

    def test_orm_session_tool_query_user(self):
        self.getPage('/query_user')
        json_resp = json.loads(self.body)
        self.assertIn('id', json_resp)
        self.assertIn('name', json_resp)
        self.assertEqual(u'alice', json_resp['name'])
        self.assertStatus(200)

    def test_orm_session_tool_query_address(self):
        self.getPage('/query_addresss')
        json_body = json.loads(self.body)
        self.assertIn('id', json_body)
        self.assertIn('address', json_body)
        self.assertEqual(u'Hong Kong', json_body['address'])
        self.assertStatus(200)

    def test_raise_not_passable_exception(self):
        self.getPage('/raise_not_passable_exception_save')
        self.assertStatus(400)
        self.getPage('/raise_not_passable_exception_query')
        self.assertBody(json.dumps(None))
        self.assertStatus(200)

    def test_raise_passable_exception(self):
        self.getPage('/raise_passable_exception_save')
        self.assertStatus(303)
        self.getPage('/raise_passable_exception_query')
        json_resp = json.loads(self.body)
        self.assertIn('id', json_resp)
        self.assertIn('name', json_resp)
        self.assertEqual(u'david', json_resp['name'])
        self.assertStatus(200)
