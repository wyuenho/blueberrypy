import logging
import unittest
import warnings

from email.header import decode_header

from lazr.smtptest.controller import QueueController

from blueberrypy import email
from blueberrypy.email import Mailer


logger = logging.getLogger(__name__)


class MailerTest(unittest.TestCase):

    def setUp(self):
        self.controller = QueueController("localhost", 9025)
        self.controller.start()

    def tearDown(self):
        self.controller.stop()

    def test_send_email(self):
        mailer = Mailer("localhost", 9025)
        body = "This is the bloody test body"
        mailer.send_email("rcpt@example.com", "from@example.com", "test subject", body)

        messages = list(self.controller)
        message = messages[0]
        (from_str, from_cs) = decode_header(message["From"])[0]
        (to_str, to_cs) = decode_header(message["To"])[0]
        (subject_str, subject_cs) = decode_header(message["Subject"])[0]

        self.assertEqual("from@example.com", from_str)
        self.assertEqual("rcpt@example.com", to_str)
        self.assertEqual("test subject", subject_str)
        self.assertEqual(body, message.get_payload(decode=True))

    def test_send_html_email(self):
        mailer = Mailer("localhost", 9025)
        text = u"This is the bloody test body"
        html = u"<p>This is the bloody test body</p>"
        mailer.send_html_email("rcpt@example.com", "from@example.com", "test subject", text, html)

        messages = list(self.controller)
        message = messages[0]
        (from_str, from_cs) = decode_header(message["From"])[0]
        (to_str, to_cs) = decode_header(message["To"])[0]
        (subject_str, subject_cs) = decode_header(message["Subject"])[0]

        self.assertEqual("from@example.com", from_str)
        self.assertEqual("rcpt@example.com", to_str)
        self.assertEqual("test subject", subject_str)
        self.assertEqual(text, message.get_payload(0).get_payload(decode=True))
        self.assertEqual("text/plain", message.get_payload(0).get_content_type())
        self.assertEqual(html, message.get_payload(1).get_payload(decode=True))
        self.assertEqual("text/html", message.get_payload(1).get_content_type())

class EmailModuleFuncTest(unittest.TestCase):

    def setUp(self):
        self.controller = QueueController("localhost", 9025)
        self.controller.start()

    def tearDown(self):
        self.controller.stop()

    def test_warnings(self):

        email._mailer = None

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("error")
            self.assertRaises(UserWarning, email.send_email, "rcpt@example.com", "from@example.com", "test subject", "test body")
            self.assertRaises(UserWarning, email.send_html_email, "rcpt@example.com", "from@example.com", "test subject", "plain body", "<p>html body</p>")

    def test_send_email(self):
        email.configure({"host": "localhost",
                         "port": 9025})

        body = "This is the bloody test body"
        email.send_email("rcpt@example.com", "from@example.com", "test subject", body)

        messages = list(self.controller)
        message = messages[0]
        (from_str, from_cs) = decode_header(message["From"])[0]
        (to_str, to_cs) = decode_header(message["To"])[0]
        (subject_str, subject_cs) = decode_header(message["Subject"])[0]

        self.assertEqual("from@example.com", from_str)
        self.assertEqual("rcpt@example.com", to_str)
        self.assertEqual("test subject", subject_str)
        self.assertEqual(body, message.get_payload(decode=True))

    def test_send_html_email(self):
        email.configure({"host": "localhost",
                         "port": 9025})

        text = u"This is the bloody test body"
        html = u"<p>This is the bloody test body</p>"
        email.send_html_email("rcpt@example.com", "from@example.com", "test subject", text, html)

        messages = list(self.controller)
        message = messages[0]
        (from_str, from_cs) = decode_header(message["From"])[0]
        (to_str, to_cs) = decode_header(message["To"])[0]
        (subject_str, subject_cs) = decode_header(message["Subject"])[0]

        self.assertEqual("from@example.com", from_str)
        self.assertEqual("rcpt@example.com", to_str)
        self.assertEqual("test subject", subject_str)
        self.assertEqual(text, message.get_payload(0).get_payload(decode=True))
        self.assertEqual("text/plain", message.get_payload(0).get_content_type())
        self.assertEqual(html, message.get_payload(1).get_payload(decode=True))
        self.assertEqual("text/html", message.get_payload(1).get_content_type())
