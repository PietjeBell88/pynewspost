import zlib

ENC_TABLE = ''.join([chr((i + 42) % 256) for i in xrange(256)])

def yencode(data):
    return data.translate(ENC_TABLE).replace('=', '=\x7d').replace('\x00', '=\x40').replace('\r', '=\x4d').replace('\n', '=\x4a')

def yencwrap(data, name, fsize, part, parts, linelength, lines): # part starts counting at 1
    psize = len(data)
    crcstr = '%08X' % (zlib.crc32(data) & 0xFFFFFFFF)
    encdata = yencpart(data, linelength)
    t = []
    begin = (part - 1) * linelength * lines + 1
    end = begin + psize - 1
    header = '=ybegin part=%d line=%d size=%d name=%s\r\n=ypart begin=%d end=%d\r\n' % (part, linelength, fsize, name, begin, end)
    t.append(header)
    t.append(encdata) # assume encdata is from nntpyencpart and therefore ends with CRLF
    footer = '\r\n=yend size=%d part=%d pcrc32=%s' % (psize, part, crcstr)
    t.append(footer)
    return ''.join(t)

def yencpart(data, linelength):
    bytes = len(data)
    encdata = yencode(data)
    lines = []
    pointer = 0
    while 1:
        try:
            if encdata[pointer] == '.':
                lines.append('=\x6e')
                lines.append(encdata[pointer + 1:pointer + linelength - 1])
                pointer += linelength - 1
            else:
                lines.append(encdata[pointer:pointer + linelength])
                pointer += linelength
            if lines[len(lines) - 1][-1] == '=':
                lines.append(encdata[pointer])
                pointer += 1
        except IndexError:
            lines.append(encdata[pointer:])
            pointer = 0
            lines.append('\r\n')
            break
        lines.append('\r\n')
    encdata = None
    partstr = ''.join(lines)
    lines = None
    return partstr
