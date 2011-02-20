import zlib

ENC_TABLE = ''.join([chr((i + 42) % 256) for i in xrange(256)])

def yencode(data):
    return data.translate(ENC_TABLE).replace('=', '=\x7d').replace('\x00', '=\x40').replace('\r', '=\x4d').replace('\n', '=\x4a')

def nntpyencwrap(encdata, name, fsize, psize, pcrc32, part, chars_per_line, lines_per_part): # part starts counting at 1
    t = []
    begin = (part - 1) * chars_per_line * lines_per_part + 1
    end = begin + psize - 1
    header = '=ybegin part=%d line=%d size=%d name=%s\r\n=ypart begin=%d end=%d\r\n' % (part, chars_per_line, fsize, name, begin, end)
    t.append(header)
    t.append(encdata) # assume encdata is from nntpyencpart and therefore ends with CRLF
    footer = '\r\n=yend size=%d part=%d pcrc32=%s' % (psize, part, pcrc32)
    t.append(footer)
    return ''.join(t)

def nntpyencpart(data, chars_per_line):
    bytes = len(data)
    encdata = yencode(data)
    crcstr = '%08X' % (zlib.crc32(data) & 0xFFFFFFFF)
    lines = []
    pointer = 0
    while 1:
        try:
            if encdata[pointer] == '.':
                lines.append('=\x6e')
                lines.append(encdata[pointer + 1:pointer + chars_per_line - 1])
                pointer += chars_per_line - 1
            else:
                lines.append(encdata[pointer:pointer + chars_per_line])
                pointer += chars_per_line
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
    return (partstr, crcstr)
