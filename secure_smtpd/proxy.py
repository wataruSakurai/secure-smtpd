import secure_smtpd

from smtp_server import SMTPServer
from store_credentials import StoreCredentials

class ProxyServer(SMTPServer):
    """Implements an open relay.  Inherits from secure_smtpd, so can handle
    SSL incoming.  Modifies attributes slightly:

    * if "ssl" is true accepts SSL connections inbound and connects via SSL
        outbound
    * adds "sslOutOnly", which can be set to True when "ssl" is False so that
        inbound connections are in plain text but outbound are in SSL
    * adds "printDebug", which if True prints all inbound messages to stdout
    * ignores any credential validators, passing any credentials upstream
    """
    def __init__(self, *args, **kwargs):
        self.sslOutOnly = False
        if kwargs.has_key('sslOutOnly'):
            self.sslOutOnly = kwargs.pop('sslOutOnly')

        self.printDebug = False
        if kwargs.has_key('printDebug'):
            self.printDebug = kwargs.pop('printDebug')

        kwargs['credential_validator'] = StoreCredentials()
        SMTPServer.__init__(self, *args, **kwargs)

    def process_message(self, peer, mailfrom, rcpttos, data):
        if self.printDebug:
            # ------------------------
            # stolen directly from stmpd.DebuggingServer
            inheaders = 1
            lines = data.split('\n')
            print '---------- MESSAGE FOLLOWS ----------'
            for line in lines:
                # headers first
                if inheaders and not line:
                    print 'X-Peer:', peer[0]
                    inheaders = 0
                print line
            print '------------ END MESSAGE ------------'

        # ------------------------
        # following code is direct from smtpd.PureProxy
        lines = data.split('\n')
        # Look for the last header
        i = 0
        for line in lines:
            if not line:
                break
            i += 1
        lines.insert(i, 'X-Peer: %s' % peer[0])
        data = '\n'.join(lines)
        self._deliver(mailfrom, rcpttos, data)

    def _deliver(self, mailfrom, rcpttos, data):
        # ------------------------
        # following code is adapted from smtpd.PureProxy with modifications to
        # handle upstream SSL

        import smtplib
        refused = {}
        try:
            if self.ssl or self.sslOutOnly:
                s = smtplib.SMTP_SSL()
            else:
                s = smtplib.SMTP()

            s.connect(self._remoteaddr[0], self._remoteaddr[1])
            if self.credential_validator.stored:
                # we had credentials passed in, use them
                s.login(self.credential_validator.username,
                    self.credential_validator.password)
            try:
                refused = s.sendmail(mailfrom, rcpttos, data)
                print 'refused: ', refused
            finally:
                s.quit()
        except smtplib.SMTPRecipientsRefused, e:
            print '********* ERROR: got SMTPRecipientsRefused'
            refused = e.recipients
        except (socket.error, smtplib.SMTPException), e:
            print '********* ERROR: got', e.__class__
            # All recipients were refused.  If the exception had an associated
            # error code, use it.  Otherwise,fake it with a non-triggering
            # exception code.
            errcode = getattr(e, 'smtp_code', -1)
            errmsg = getattr(e, 'smtp_error', 'ignore')
            for r in rcpttos:
                refused[r] = (errcode, errmsg)
        return refused