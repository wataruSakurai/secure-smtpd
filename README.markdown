Secure SMTPD
============

Secure-SMTPD extends on Petri Lehtinen's SMTPD library adding support for AUTH and SSL.

Usage
-----

```python
import asyncore
from secure_smtpd import SMTPServer
import logging


class OkCredentialValidator(object):
    def validate(self, username, password):
        # TODO: check username, password for validation test
        return True


class OkSMTPServer(SMTPServer):
    def __init__(self):
        SMTPServer.__init__(self,
                            ('0.0.0.0', 2500),
                            None,
                            require_authentication=True,
                            ssl=False,
                            credential_validator=OkCredentialValidator())
        self.logger.setLevel(logging.DEBUG)

    def process_message(self, peer, mailfrom, rcpttos, data):
        # TODO: need check envelope
        print("%s %s %s %s" % (peer, mailfrom, rcpttos, data))


OkSMTPServer()
asyncore.loop()
```
