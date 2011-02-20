import eventlet
from nntpyenc import nntpyencpart, nntpyencwrap
import nntp
from random import SystemRandom
from time import time
rand = SystemRandom()

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

class PostArticle:
    def __init__(self, name, email, newsgroups, subject, lines, linelength, filename, filesize, part, parts, data):
        self.name       = name
        self.email      = email
        self.newsgroups = newsgroups

        self.subject    =  subject

        self.lines      = lines
        self.linelength = linelength

        self.filename   = filename
        self.filesize   = filesize
        self.part       = part
        self.parts      = parts

        self.data       = data

def dbg(x):
    import sys
    if x.strip():
        sys.stderr.write(x.strip() + '\r\n')

def gen_mid(part, parts):
    return 'Part%dof%d.%08X%08X%08X%.0f@4894782.local' % (part, parts, rand.randint(0, 0xffffffff), rand.randint(0, 0xffffffff), rand.randint(0, 0xffffffff), time())

def get_reply(n, code):
    reply = n.file.readline()
    dbg(reply)
    while reply.split(' ')[0] != code:
        reply = n.file.readline()
        dbg(reply)
    return True

def send_command(n, command, code, timeout=120):
    dbg("Sending command: %s" % command)
    n.sendall(command)
    return get_reply(n, code)

def postpart_to_connection(n, article):
    t = []
    headers = 'From: %s (%s)\r\nNewsgroups: %s\r\nSubject: %s\r\nMessage-ID: <%s>\r\n\r\n' %\
        (article.email, article.name, ','.join(article.newsgroups), article.subject, gen_mid(article.part, article.parts))
    t.append(headers)
    encdata, crcstr = nntpyencpart(article.data, article.linelength)
    t.append(nntpyencwrap(encdata=encdata, name=article.filename, pcrc32=crcstr, fsize=article.filesize, psize=len(article.data), part=article.part, chars_per_line=article.linelength, lines_per_part=article.lines))
    t.append('\r\n.\r\n')
    data_to_post = ''.join(t)

    if send_command(n, 'POST\r\n', NNTP_PROCEED_WITH_POST):
        n.sendall(data_to_post)
        return get_reply(n, NNTP_ARTICLE_POSTED_OK)
