from random import SystemRandom
from time import time
rand = SystemRandom()

class PostPart:
    def __init__(self, name, email, newsgroups, subject, lines, linelength, filename, filesize, part, parts, data, encfunc):
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

        self.encfunc    = encfunc

    def __str__(self):
        t = []
        headers = 'From: %s (%s)\r\nNewsgroups: %s\r\nSubject: %s\r\nMessage-ID: <%s>\r\n\r\n' %\
            (self.email, self.name, ','.join(self.newsgroups), self.subject, self.gen_mid())
        t.append(headers)
        t.append(self.encfunc(data=self.data, name=self.filename, fsize=self.filesize, part=self.part, parts=self.parts, linelength=self.linelength, lines=self.lines))
        t.append('\r\n.\r\n')
        return ''.join(t)

    def gen_mid(self):
        return 'Part%dof%d.%08X%08X%08X%d@4894782.local' % (self.part, self.parts, rand.randint(0, 0xffffffff), rand.randint(0, 0xffffffff), rand.randint(0, 0xffffffff), int(time()))

