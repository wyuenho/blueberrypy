from __future__ import absolute_import

import logging
import smtplib
import socket
import time

from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr


logger = logging.getLogger(__name__)


class Mailer(object):

    def __init__(self, host='', port=0, local_hostname=None,
                 timeout=socket._GLOBAL_DEFAULT_TIMEOUT,
                 ssl=False, keyfile=None, certfile=None,
                 default_sender=None, debug=False, connection_retries=10):

        self.host = host
        self.port = port
        self.local_hostname = local_hostname
        self.timeout = timeout
        self.ssl = ssl
        self.keyfile = keyfile
        self.certfile = certfile
        self.default_sender = default_sender
        self.debug = debug
        self.connection_retries = connection_retries

    def get_connection(self):
        if self.ssl:
            connection = smtplib.SMTP_SSL(self.host, self.port,
                                          self.local_hostname,
                                          self.keyfile, self.certfile,
                                          self.timeout)
        else:
            connection = smtplib.SMTP(self.host, self.port, self.local_hostname,
                                      self.timeout)
        connection.set_debuglevel(self.debug)
        return connection

    def send_mail(self, to_, from_=None, subject=None, body=None,
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

        connection = self.get_connection()
        try:
            connection.sendmail(from_addr, to_addr, message.as_string(False))
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
                    connection.sendmail(from_addr, to_addr, message.as_string(False))
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

