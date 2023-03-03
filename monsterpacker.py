# Core MeatPack methods
# Packs a data stream, byte by byte
from array import array

# For faster lookup and access
MeatPackLookupTablePackable = array('B', 256 * [0])
MeatPackLookupTableValue = array('B', 256 * [0])
MeatPackSpaceReplacedCharacter = 'E'
# MonsterPacker - notice that we remove whitespace at all times

# MonsterPacker - decoding lut, handy
MeatPackDecodeLUT = {}
MeatPackReverseLookupTbl = {
    '0': 0b00000000,
    '1': 0b00000001,
    '2': 0b00000010,
    '3': 0b00000011,
    '4': 0b00000100,
    '5': 0b00000101,
    '6': 0b00000110,
    '7': 0b00000111,
    '8': 0b00001000,
    '9': 0b00001001,
    '.': 0b00001010,
    'Y': 0b00001011, # compare to space in MeatPack
    '\n': 0b00001100,
    'G': 0b00001101,
    'X': 0b00001110,
    '\0': 0b00001111  # never used, 0b1111 is used to indicate next 8-bits is a full character
}

ArraysInitialized = False


def initialize_arrays():
    global ArraysInitialized
    global MeatPackLookupTablePackable
    global MeatPackLookupTableValue

    if not ArraysInitialized:
        for i in range(0, 255):
            MeatPackLookupTablePackable[i] = MeatPackLookupTableValue[i] = 0

        for char, value in MeatPackReverseLookupTbl.items():
            c = ord(char)
            MeatPackLookupTablePackable[c] = 1
            MeatPackLookupTableValue[c] = value

        ArraysInitialized = True


def initialize_decode_array():
    for char, value in MeatPackReverseLookupTbl.items():
        c = ord(char)
        MeatPackDecodeLUT[value] = c


"""
Command Words:

0xFF (0b11111111) x 2 == Command Word

Operation: send command word (0xFF 0xFF), send command byte, send close byte (0xFF)
"""

MPCommand_None = 0
# MPCommand_TogglePacking     = 253 -- Currently unused, byte 253 can be reused later.
MPCommand_EnablePacking = 251
MPCommand_DisablePacking = 250
MPCommand_ResetAll = 249
MPCommand_QueryConfig = 248
MPCommand_EnableNoSpaces = 247
MPCommand_SignalByte = 0xFF


MeatPack_BothUnpackable = 0b11111111


# -------------------------------------------------------------------------------
def initialize():
    initialize_arrays()
    initialize_decode_array()


# -------------------------------------------------------------------------------
def pack_chars(low, high):
    highord = ord(high)
    highpack = MeatPackLookupTableValue[highord] & 0xF
    loword = ord(low)
    lowpack = MeatPackLookupTableValue[loword] & 0xF

    highshift = highpack << 4
    pack = highshift | lowpack
    result = int(pack)

    return result

# -------------------------------------------------------------------------------


def is_packable(char):
    return False if MeatPackLookupTablePackable[ord(char)] == 0 else True


# -------------------------------------------------------------------------------
def get_command_bytes(command):
    out = bytearray()
    out.append(MPCommand_SignalByte)
    out.append(MPCommand_SignalByte)
    out.append(command)
    return out


# -------------------------------------------------------------------------------
def _unified_method(line):
    # Notice how much I skip here, checksums are not up to this layer/protocol
    stripped = line.replace('e', 'E').replace(
        'x', 'X').replace('g', 'G').replace(' ', '')
    return stripped


# -------------------------------------------------------------------------------
def pack_line(line, logger=None):
    bts = bytearray()

    if line[0] == ';':
        return bts
    elif line[0] == '\n':
        return bts
    elif line[0] == '\r':
        return bts
    elif len(line) < 2:
        return bts
    elif ';' in line:
        line = line.partition(';')[0].rstrip() + "\n"

    line = _unified_method(line)

    if logger:
        logger.info("[Test] Line sent: {}".format(line))

    line_len = len(line)

    for line_idx in range(0, line_len, 2):
        skip_last = False
        if line_idx == (line_len - 1):
            skip_last = True

        char_1 = line[line_idx]

        # If we are at the last character and it needs to be skipped,
        # pack a benign character like \n into it.
        char_2 = '\n' if skip_last else line[line_idx + 1]

        c1_p = is_packable(char_1)
        c2_p = is_packable(char_2)

        if c1_p:
            if c2_p:
                bts.append(pack_chars(char_1, char_2))
            else:
                bts.append(pack_chars(char_1, "\0"))
                bts.append(ord(char_2))
        else:
            if c2_p:
                bts.append(pack_chars("\0", char_2))
                bts.append(ord(char_1))
            else:
                bts.append(MeatPack_BothUnpackable)
                bts.append(ord(char_1))
                bts.append(ord(char_2))

    return bts


# -------------------------------------------------------------------------------
def pack_file(in_filename, out_filename, remove_g1=False):
    in_file = open(in_filename, "r")
    out_file = open(out_filename, "wb")

    if not in_file.readable():
        raise IOError("cannot read input file")
    if not out_file.writable():
        raise IOError("cannot write to output file")

    file_data_lines = in_file.readlines()
    bts = bytearray()
    bts.append(MPCommand_SignalByte)
    bts.append(MPCommand_SignalByte)
    bts.append(MPCommand_EnablePacking)

    for line in file_data_lines:
        # MonsterPacker - slight optimization
        if remove_g1:
            line = line.replace('G1 ', '')
        bts += pack_line(line)

    bts.append(MPCommand_SignalByte)
    bts.append(MPCommand_SignalByte)
    bts.append(MPCommand_ResetAll)

    out_file.write(bts)
    out_file.flush()


# MonsterPacker - decoding nibbles
def decode_nibbles(n1, n2):
    return chr(MeatPackDecodeLUT[n1]), chr(MeatPackDecodeLUT[n2])

# MonsterPacker - decoding bytes
def unshift_byte(b):
    lowval = b >> 4
    highval = b & 0xF
    return (highval, lowval)

# MonsterPacker - decoding file
def decode_file(in_filename):
    escape = MeatPackReverseLookupTbl['\0']

    in_file = open(in_filename, "rb")

    preamble = in_file.read(3)
    if preamble[0] == MPCommand_SignalByte and preamble[1] == MPCommand_SignalByte:
        print("Preamble correct")
    if preamble[2] == MPCommand_EnablePacking:
        print("Packing enabled")

    fullstr = ""

    newline = True
    lineno = 0
    while True:
        bytevals = in_file.read(1)
        if len(bytevals) == 0: break
        b = bytevals[0]
        n1, n2 = unshift_byte(b)
        c1, c2 = decode_nibbles(n1, n2)

        str = ""
        if n1 == escape and n2 != escape:
            b2 = in_file.read(1)[0]
            c1 = chr(b2)  # overwrite dummy c1
            str += c1
            str += c2
        elif n1 != escape and n2 != escape:
            str += c1
            if c1 != '\n' or c2 != '\n':
                str += c2
        elif n1 != escape and n2 == escape:
            b2 = in_file.read(1)[0]
            c1 = c1
            c2 = chr(b2)  # overwrite dummy c2
            str += c1
            str += c2
        elif b == MeatPack_BothUnpackable:
            str += chr(in_file.read(1)[0])
            str += chr(in_file.read(1)[0])

        # Previously detected this char is newline
        if newline and str[0] in ['X', 'Y', 'Z', 'E', 'F', 'S']:
            str = "G1" + str
            # print("inflate", str)

        # Determine if we are progressing to the next line
        if '\n' in str:
            lineno += 1
            if len(str) == 1:
                newline = True
            elif len(str) == 2:
                newline = str[1] == '\n'
                if newline == False:
                    raise Exception('unwanted scenario, newline in between 2 decoded chars')
        else:
            newline = False
        if newline:
            lineno += 1

        fullstr += str
    return fullstr


def strip_comments(in_filename, out_filename):
    in_file = open(in_filename, "r")
    out_file = open(out_filename, "wb")

    if not in_file.readable():
        raise IOError("cannot read input file")
    if not out_file.writable():
        raise IOError("cannot write to output file")

    file_data_lines = in_file.readlines()

    for line in file_data_lines:
        if line[0] == ';':
            continue
        if line[0] == '\n':
            continue
        if line[0] == '\r':
            continue
        if len(line) < 2:
            continue
        if ';' in line:
            line = line.split(';')[0].rstrip() + "\n"
        out_file.write(line.encode("UTF-8"))
