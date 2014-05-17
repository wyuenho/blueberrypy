import os

from cherrypy.test import helper


class SQLAlchemyPluginTest(helper.CPWebCase):

    def test_engine_bindings(self):
        if os.name not in ['posix']:
            return self.skip("skipped (not on posix) ")

        p = helper.CPProcess(ssl=(self.scheme.lower() == 'https'))
        p.write_conf(extra='test_case_name: "test_engine_bindings"')
        p.start(imports='blueberrypy.tests._test_plugins_engine_bindings')

        try:
            self.getPage("/engine_bindings")
            self.assertStatus(200)
            self.assertEqual(u"[(<class 'blueberrypy.tests._test_plugins_engine_bindings.Group'>, "
                             "Engine(sqlite://)), "
                             "(<class 'blueberrypy.tests._test_plugins_engine_bindings.User'>, "
                             "Engine(sqlite://))]", self.body.decode())
        finally:
            self.getPage("/exit")
        p.join()

    def test_engine(self):
        if os.name not in ['posix']:
            return self.skip("skipped (not on posix) ")

        p = helper.CPProcess(ssl=(self.scheme.lower() == 'https'))
        p.write_conf(extra='test_case_name: "test_engine"')
        p.start(imports='blueberrypy.tests._test_plugins_engine')

        try:
            self.getPage("/engine")
            self.assertStatus(200)
            self.assertEqual(u"Engine(sqlite://)", self.body.decode())
        finally:
            self.getPage("/exit")
        p.join()
