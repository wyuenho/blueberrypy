# -*- coding: utf-8 -*-

import unittest
import socket
import threading
import time

import cherrypy
from cherrypy.lib import sessions
from cherrypy.test import helper

from blueberrypy.session import RedisSession


def http_methods_allowed(methods=['GET', 'HEAD']):
    method = cherrypy.request.method.upper()
    if method not in methods:
        cherrypy.response.headers['Allow'] = ", ".join(methods)
        raise cherrypy.HTTPError(405)

cherrypy.tools.allow = cherrypy.Tool('on_start_resource', http_methods_allowed)


def setup_server():

    class Root:

        _cp_config = {'tools.sessions.on': True,
                      'tools.sessions.storage_type': 'redis',
                      'tools.sessions.host': 'localhost',
                      'tools.sessions.port': 6379,
                      'tools.sessions.prefix': 'whatever:',
                      'tools.sessions.timeout': (1.0 / 60)
                      }

        def clear(self):
            cherrypy.session.cache.flushdb()
        clear.exposed = True

        def data(self):
            cherrypy.session['aha'] = u'褔'
            return repr(cherrypy.session._data)
        data.exposed = True

        def testGen(self):
            counter = cherrypy.session.get('counter', 0) + 1
            cherrypy.session['counter'] = counter
            yield str(counter)
        testGen.exposed = True

        def testStr(self):
            counter = cherrypy.session.get('counter', 0) + 1
            cherrypy.session['counter'] = counter
            return str(counter)
        testStr.exposed = True

        def index(self):
            sess = cherrypy.session
            c = sess.get('counter', 0) + 1
            time.sleep(0.01)
            sess['counter'] = c
            return str(c)
        index.exposed = True

        def keyin(self, key):
            return str(key in cherrypy.session)
        keyin.exposed = True

        def delete(self):
            cherrypy.session.delete()
            sessions.expire()
            return "done"
        delete.exposed = True

        def delkey(self, key):
            del cherrypy.session[key]
            return "OK"
        delkey.exposed = True

        def blah(self):
            return self._cp_config['tools.sessions.storage_type']
        blah.exposed = True

        def iredir(self):
            raise cherrypy.InternalRedirect('/blah')
        iredir.exposed = True

        def restricted(self):
            return cherrypy.request.method
        restricted.exposed = True
        restricted._cp_config = {'tools.allow.on': True,
                                 'tools.allow.methods': ['GET']}

        def regen(self):
            cherrypy.tools.sessions.regenerate()
            return "logged in"
        regen.exposed = True

        def length(self):
            return str(len(cherrypy.session))
        length.exposed = True

        def session_cookie(self):
            # Must load() to start the clean thread.
            cherrypy.session.load()
            return cherrypy.session.id
        session_cookie.exposed = True
        session_cookie._cp_config = {
            'tools.sessions.path': '/session_cookie',
            'tools.sessions.name': 'temp',
            'tools.sessions.persistent': False}

    sessions.RedisSession = RedisSession
    cherrypy.tree.mount(Root())

# testing that redis-py is available and that we have a redis server running
try:
    import redis

    host, port = '127.0.0.1', 6379
    for res in socket.getaddrinfo(host, port, socket.AF_UNSPEC,
                                  socket.SOCK_STREAM):
        af, socktype, proto, canonname, sa = res
        s = None
        try:
            s = socket.socket(af, socktype, proto)
            s.settimeout(1.0)
            s.connect((host, port))
            s.close()
        except socket.error:
            if s:
                s.close()
            raise
        break

except ImportError:

    class RedisSessionTest(unittest.TestCase):
        def test_nothing(self):
            self.fail("redis-py not available")

except socket.error:

    class RedisSessionTest(unittest.TestCase):
        def test_nothing(self):
            self.fail("redis not reachable")

else:
    class RedisSessionTest(helper.CPWebCase):

        setup_server = staticmethod(setup_server)

        def test_0_Session(self):
            self.getPage('/testStr')
            self.assertBody('1')
            self.getPage('/testGen', self.cookies)
            self.assertBody('2')
            self.getPage('/testStr', self.cookies)
            self.assertBody('3')
            self.getPage('/length', self.cookies)
            self.assertBody('1')
            self.getPage('/delkey?key=counter', self.cookies)
            self.assertStatus(200)

            # Wait for the session.timeout (1 second)
            time.sleep(1.25)
            self.getPage('/')
            self.assertBody('1')

            # Test session __contains__
            self.getPage('/keyin?key=counter', self.cookies)
            self.assertBody("True")

            # Test session delete
            self.getPage('/delete', self.cookies)
            self.assertBody("done")

        def test_1_Concurrency(self):
            client_thread_count = 5
            request_count = 30

            # Get initial cookie
            self.getPage("/")
            self.assertBody("1")
            cookies = self.cookies

            data_dict = {}

            def request(index):
                for i in range(request_count):
                    self.getPage("/", cookies)
                    # Uncomment the following line to prove threads overlap.
##                    sys.stdout.write("%d " % index)
                if not self.body.isdigit():
                    self.fail(self.body)
                data_dict[index] = v = int(self.body)

            # Start <request_count> concurrent requests from
            # each of <client_thread_count> clients
            ts = []
            for c in range(client_thread_count):
                data_dict[c] = 0
                t = threading.Thread(target=request, args=(c,))
                ts.append(t)
                t.start()

            for t in ts:
                t.join()

            hitcount = max(data_dict.values())
            expected = 1 + (client_thread_count * request_count)
            self.assertEqual(hitcount, expected)

        def test_3_Redirect(self):
            # Start a new session
            self.getPage('/testStr')
            self.getPage('/iredir', self.cookies)
            self.assertBody("redis")

        def test_5_Error_paths(self):
            self.getPage('/unknown/page')
            self.assertErrorPage(404, "The path '/unknown/page' was not found.")

            # Note: this path is *not* the same as above. The above
            # takes a normal route through the session code; this one
            # skips the session code's before_handler and only calls
            # before_finalize (save) and on_end (close). So the session
            # code has to survive calling save/close without init.
            self.getPage('/restricted', self.cookies, method='POST')
            self.assertErrorPage(405)

