#!/usr/bin/env python

import optparse
import eventlet
eventlet.monkey_patch()
import eventlet.tpool
from eventlet.green import socket
import os
import sys

import post
from post import send_command, get_reply, PostArticle

class PostFile:
    def __init__(self, path, filename, filesize, filenum, blocksize):
        self.path     = path
        self.filename = filename
        self.filesize = filesize
        self.filenum  = filenum
        self.parts    = int((filesize + blocksize - 1) / blocksize)

def gen_subject(comment, fileno, files, fname, partno, parts):
    return '%s - [%d/%d] - "%s" yEnc (%d/%d)' % (comment, fileno, files, fname, partno, parts)

def dbg(x):
    if x.strip():
        sys.stderr.write(x + '\r\n')

def establish_connection(server, port):
    n = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    n.connect((server, port))
    n.file = n.makefile('rb')
    dbg('connected')
    reply = get_reply(n, post.NNTP_SERVER_READY_POSTING_ALLOWED)
    reply = reply and send_command(n, 'AUTHINFO USER {user}\r\n'.format(user=options.user), post.NNTP_MORE_AUTHENTICATION_REQUIRED)
    reply = reply and send_command(n, 'AUTHINFO PASS {password}\r\n'.format(password=options.password), post.NNTP_AUTHENTICATION_SUCCESSFUL)

    if not reply:
        n = None

    return n

def worker(server, port, q):
    # Establish a connection
    n = None
    while n is None:
        n = establish_connection(server, port)
        if n is None:
            dbg("Failed to connect...")
            eventlet.sleep(10)

    # Post the parts
    while True:
        item = q.get()
        if not post.postpart_to_connection(n, item):
            dbg("Posting failed...")
            q.put(item)
        else:
            q.task_done()

def sort_by_extensions(filelist):
    for f in filelist:
        ext = f.basename.rsplit('.',1)[1]

def main(server, port, user, password, threads, name, email, newsgroups, comment, lines, linelength, files):
    pool = eventlet.GreenPool(threads)

    blocksize = linelength * lines

    if server.isalpha():
        server = socket.gethostbyname(server)

    # Create a list of files including useful properties about the files
    filelist = []
    for i in range(len(files)):
        f = files[i]
        filelist.append(PostFile(path=f, filename=os.path.basename(f), filesize=os.path.getsize(f), filenum=i+1, blocksize=blocksize))

    # Creating the producer/multi-consumers & queue
    q = eventlet.Queue()
    for i in range(threads):
        pool.spawn(worker, server, port, q)

    # Posting
    for pf in filelist:
        with open(pf.path, 'rb') as f:
            for i in xrange(1, pf.parts + 1):
                subject = gen_subject(comment, pf.filenum, len(filelist), pf.filename, i, pf.parts)
                data = eventlet.tpool.execute(f.read, blocksize)
                q.put(PostArticle(name, email, newsgroups, subject, lines, linelength, pf.filename, pf.filesize, i, pf.parts, data))

    dbg('waiting')
    q.join()

if __name__ == '__main__':
    p = optparse.OptionParser(description='Post files.')
    p.add_option('--server',    '-s', action='store', help='Hostname or IP of the news server')
    p.add_option('--port',            action='store', help='Port number on the news server [%(default)d]', type='int', default=119)
    p.add_option('--user',      '-u', action='store', help='username on the news server')
    p.add_option('--password',  '-p', action='store', help='Password on the news server')
    p.add_option('--threads',   '-t', action='store', help='amount of thread to use for posting [%(default)d]', type='int', default=1)
    p.add_option('--email',     '-e', action='store', help='Your email address [%(default)s]',dest='email', default='anonymous@anonymous.org')
    p.add_option('--name',            action='store', help='Your full name. [%(default)s]', default='Anonymous')
    p.add_option('--newsgroup', '-n', action='store', help='Comma seperated newsgroups to post to. [%(default)s]', dest='newsgroups', default='alt.binaries.test')
    p.add_option('--comment',   '-c', action='store', help='Subject of the post. Default is equal to filename.')
    p.add_option('--lines',     '-l', action='store', help='Amount of lines to post with. [%(default)d]', type='int', default=5000)
    p.add_option('--linelength',      action='store', help='Characters per line. [%(default)d]', type='int', default=128)

    (options, args) = p.parse_args()

    # Parameter checking
    if not options.comment and len(args) != 1:
        dbg("You have to specify the comment when posting more than one file.")
        exit(1)

    # Mandatory options
    if not options.server:
        print "--server is required"
        exit()
    if not options.user:
        print "--user is required"
        exit()
    if not options.password:
        print "--password is required"
        exit()

    options.newsgroups = options.newsgroups.split(",")
    sys.exit(main(files=args, **options.__dict__))
