import eventlet
eventlet.monkey_patch()
import eventlet.tpool
from eventlet.green import socket

NNTP_SERVER_READY_POSTING_ALLOWED = "200"
NNTP_AUTHENTICATION_SUCCESSFUL    = "281"
NNTP_MORE_AUTHENTICATION_REQUIRED = "381"
NNTP_UNKNOWN_COMMAND              = "500"
NTTP_AUTHENTICATION_UNSUCCESSFUL  = "502"
NNTP_PROCEED_WITH_POST            = "340"
NNTP_POSTING_NOT_ALLOWED          = "440"
NNTP_ARTICLE_POSTED_OK            = "240"
NNTP_POSTING_FAILED               = "441"
NNTP_DATE                         = "111"

def dbg(x):
    import sys
    if x.strip():
        sys.stderr.write(x.strip() + '\r\n')

class NntpSocket:
    def __init__(self, server, port, user, password):
        self.server   = server
        self.port     = port
        self.user     = user
        self.password = password

        self.n = None
        self.reconnect()

    def __try_connection(self):
        self.n = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.n.connect((self.server, self.port))
        self.n.file = self.n.makefile('rb')
        dbg('connected')
        success = self.get_reply(NNTP_SERVER_READY_POSTING_ALLOWED)
        success = success and self.send_command('AUTHINFO USER {user}\r\n'.format(user=self.user), NNTP_MORE_AUTHENTICATION_REQUIRED)
        success = success and self.send_command('AUTHINFO PASS {password}\r\n'.format(password=self.password), NNTP_AUTHENTICATION_SUCCESSFUL)

        if not success:
            self.n = None

    def reconnect(self):
        self.n = None
        while self.n is None:
            self.__try_connection()
            if self.n is None:
                dbg("Failed to connect...")
                eventlet.sleep(10)

    def get_reply(self, code):
        reply = self.n.file.readline()
        dbg(reply)
        while reply.split(' ')[0] != code:
            reply = self.n.file.readline()
            dbg(reply)
        return True

    def send_command(self, command, code, timeout=120):
        dbg("Sending command: %s" % command)
        self.n.sendall(command)
        return self.get_reply(code)

    def sendall(self, data):
        return self.n.sendall(data)
