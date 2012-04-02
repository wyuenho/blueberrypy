from __future__ import absolute_import

import logging
import smtplib
import socket
import time
import warnings

from email.header import Header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import parseaddr, formataddr


logger = logging.getLogger(__name__)


class Mailer(object):

    def __init__(self, host='', port=0, local_hostname=None,
                 timeout=socket._GLOBAL_DEFAULT_TIMEOUT,
                 ssl=False, keyfile=None, certfile=None,
                 default_sender=None, debuglevel=False, connection_retries=10):

        self.host = host
        self.port = port
        self.local_hostname = local_hostname
        self.timeout = timeout
        self.ssl = ssl
        self.keyfile = keyfile
        self.certfile = certfile
        self.default_sender = default_sender
        self.debuglevel = debuglevel
        self.connection_retries = connection_retries

    def _get_connection(self):
        if self.ssl:
            connection = smtplib.SMTP_SSL(self.host, self.port,
                                          self.local_hostname,
                                          self.keyfile, self.certfile,
                                          self.timeout)
        else:
            connection = smtplib.SMTP(self.host, self.port, self.local_hostname,
                                      self.timeout)
        connection.set_debuglevel(self.debuglevel)
        return connection

    def send_email(self, to_, from_=None, subject=None, body=None,
                  subtype="plain", charset="utf-8"):

        message = MIMEText(body, subtype, charset)

        if subject:
            subject_header = Header()
            subject = unicode(subject, charset) if isinstance(subject, str) else subject
            subject_header.append(subject.strip())
            message["Subject"] = subject_header

        from_ = from_ or self.default_sender
        from_ = unicode(from_, charset) if isinstance(from_, str) else from_
        from_realname, from_addr = parseaddr(from_)
        from_header = Header()
        from_header.append(formataddr((from_realname, from_addr)))
        message['From'] = from_header

        to_ = unicode(to_, charset) if isinstance(to_, str) else to_
        to_realname, to_addr = parseaddr(to_)
        to_header = Header()
        to_header.append(formataddr((to_realname, to_addr)))
        message['To'] = to_header

        self._send(message, from_addr, to_addr)

    def _send(self, mime_message, from_, to_):
        connection = self._get_connection()
        try:
            connection.sendmail(from_, to_, mime_message.as_string(False))
        except smtplib.SMTPHeloError, e:
            logger.error(e, exc_info=True)
            raise
        except smtplib.SMTPSenderRefused, e:
            logger.error(e, exc_info=True)
            raise
        except smtplib.SMTPDataError, e:
            logger.error(e, exc_info=True)
            raise
        except smtplib.SMTPServerDisconnected, e:
            tries = 0
            exp_timeout = 2 ** tries
            exception = None
            while tries < self.connection_retries:
                try:
                    logger.warn("Server disconnected, retrying in %s seconds...", exp_timeout)
                    time.sleep(exp_timeout)
                    connection.sendmail(from_, to_, mime_message.as_string(False))
                    break
                except smtplib.SMTPException, e:
                    tries = tries + 1
                    exp_timeout = 2 ** tries
                    exception = e
            else:
                logger.error(exception, exc_info=True)
                raise exception
        finally:
            connection.quit()

    def send_html_email(self, to_, from_=None, subject=None, text=None,
                        html=None, charset="utf-8"):

        message = MIMEMultipart("alternative")

        if subject:
            subject_header = Header()
            subject = unicode(subject, charset) if isinstance(subject, str) else subject
            subject_header.append(subject.strip())
            message["Subject"] = subject_header

        from_ = from_ or self.default_sender
        from_ = unicode(from_, charset) if isinstance(from_, str) else from_
        from_realname, from_addr = parseaddr(from_)
        from_header = Header()
        from_header.append(formataddr((from_realname, from_addr)))
        message['From'] = from_header

        to_ = unicode(to_, charset) if isinstance(to_, str) else to_
        to_realname, to_addr = parseaddr(to_)
        to_header = Header()
        to_header.append(formataddr((to_realname, to_addr)))
        message['To'] = to_header

        message.attach(MIMEText(text, "plain", charset))
        message.attach(MIMEText(html, "html", charset))

        self._send(message, from_addr, to_addr)


_mailer = None

def configure(email_config):
    global _mailer
    _mailer = Mailer(**email_config)

def send_email(to_, from_=None, subject=None, body=None, subtype="plain",
               charset="utf-8"):

    if _mailer is None:
        warnings.warn("Module %s not configured." % __name__)
    else:
        return _mailer.send_email(to_, from_, subject, body, subtype, charset)

def send_html_email(to_, from_=None, subject=None, text=None, html=None,
                    charset="utf-8"):

    if _mailer is None:
        warnings.warn("Module %s not configured." % __name__)
    else:
        return _mailer.send_html_email(to_, from_, subject, text, html, charset)
