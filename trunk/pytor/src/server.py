#! /usr/bin/python
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

