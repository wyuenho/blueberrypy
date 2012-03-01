import hashlib
import hmac
import unittest

from base64 import b64encode

from cherrypie.util import CSRFToken, pad_block_cipher_message, \
    unpad_block_cipher_message


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

    def test_to_json(self):
        self.fail()

    def test_from_json(self):
        self.fail()


class BlockCipherPaddingTest(unittest.TestCase):

    def test_pad_block_cipher_message(self):
        padded_message = pad_block_cipher_message("message")
        self.assertEqual(padded_message, "message{{{{{{{{{")

    def test_unpad_block_cipher_message(self):
        self.assertEqual(unpad_block_cipher_message("message{{{{{{{{{"), "message")
