##############################################################################
# Copyright (c) 2010 Hajime Nakagami <nakagami@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#  THE SOFTWARE.
#=============================================================================

"""
arc4 encoding and decoding.
>>> from py3 import Arc4
>>> a1 = Arc4(b'a key')
>>> enc = a1.translate(b'plain text')
>>> [hex(c) for c in enc]
['0x4b', '0x4b', '0xdc', '0x65', '0x2', '0xb3', '0x8', '0x17', '0x48', '0x82']
>>> a2 = Arc4(b'a key')
>>> a2.translate(enc)
b'plain text'
>>>
draft-kaukonen-cipher-arcfour-03.txt Appendix A
A-1.
>>> p = bytes([0, 0, 0, 0, 0, 0, 0, 0])
>>> k = bytes([0x01, 0x23, 0x45, 0x67, 0x89, 0xab, 0xcd, 0xef])
>>> a3 = Arc4(k)
>>> enc = a3.translate(p)
>>> [hex(c) for c in enc]
['0x74', '0x94', '0xc2', '0xe7', '0x10', '0x4b', '0x8', '0x79']
>>>
A-2.
>>> p = bytes([0xdc, 0xee, 0x4c, 0xf9, 0x2c])
>>> k = bytes([0x61, 0x8a, 0x63, 0xd2, 0xfb])
>>> a4 = Arc4(k)
>>> enc = a4.translate(p)
>>> [hex(c) for c in enc]
['0xf1', '0x38', '0x29', '0xc9', '0xde']
>>>
"""

class Arc4:
    def __init__(self, key):
        state = list(range(256))
        index1 = 0
        index2 = 0

        for i in range(256):
            index2 = (key[index1] + state[i] + index2) % 256
            (state[i], state[index2]) = (state[index2], state[i])
            index1 = (index1 + 1) % len(key)

        self.state = state
        self.x = 0
        self.y = 0

    def translate(self, plain):
        state = self.state
        enc=b''
        for i in range(len(plain)):
            self.x = (self.x + 1) % 256
            self.y = (self.y + state[self.x]) % 256
            (state[self.x], state[self.y]) = (state[self.y], state[self.x])
            xorIndex = (state[self.x]+state[self.y]) % 256
            enc += bytes([plain[i] ^ state[xorIndex]])
        return enc

    def decrypt(self, plain):
        return self.translate(plain)

    def encrypt(self, plain):
        return self.translate(plain)

if __name__ == "__main__":
    import doctest
    doctest.testmod()

