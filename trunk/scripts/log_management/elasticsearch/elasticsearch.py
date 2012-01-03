#! /usr/bin/env python

# Copyright (c) 2011 Xavier Garcia  http://www.shellguardians.com
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
# POSSIBILITY OF SUCH DAMAGE

import re
import sys
import fileinput
import getopt
import os.path
import os
import calendar
import datetime
import time
import json
import urllib2



client_regexp_postfix=re.compile("^(\\w{1,3}\\s{1,2}\\d{1,2} \\d{2}:\\d{2}:\\d{2}) (\w+) postfix/smtpd\[\d+\]: (\w{1,11}): client=([\w\.\-\_]+\[[0-9.]+\]).*$")
from_regexp_postfix=re.compile("^(\\w{1,3}\\s{1,2}\\d{1,2} \\d{2}:\\d{2}:\\d{2}) \w+ postfix/qmgr\[\d+\]: (\w{1,11}): from=<(.*)>.*$")
removed_regexp_postfix=re.compile("^(\\w{1,3}\\s{1,2}\\d{1,2} \\d{2}:\\d{2}:\\d{2}) \w+ postfix/qmgr\[\d+\]: (\w{1,11}): removed")
msgid_regexp_postfix=re.compile("^(\\w{1,3}\\s{1,2}\\d{1,2} \\d{2}:\\d{2}:\\d{2}) \w+ postfix/cleanup\[\d+\]: (\w{1,11}): message-id=<(.*)>$")
to_regexp_postfix=re.compile("^(\\w{1,3}\\s{1,2}\\d{1,2} \\d{2}:\\d{2}:\\d{2}) \w+ postfix/smtp\[\d+\]: (\w{1,11}): to=<(.*)>, relay=([\w\.]+\[[0-9.]+\]:\d{1,5}), delay=[0-9.]{1,4}, delays=[0-9.]{1,4}/[0-9.]{1,4}/[0-9.]{1,4}/[0-9.]{1,4}, dsn=[0-9.]{5}, status=(\w+ \(.+\))$")
local_regexp_postfix=re.compile("^(\\w{1,3}\\s{1,2}\\d{1,2} \\d{2}:\\d{2}:\\d{2}) \w+ postfix/local\[\d+\]: (\w{1,11}): to=<(.*)>, relay=(.+), delay=[0-9.]{1,4}, delays=[0-9.]{1,4}/[0-9.]{1,4}/[0-9.]{1,4}/[0-9.]{1,4}, dsn=[0-9.]{5}, status=(\w+ \(.+\))$")

from_regex_sendmail= re.compile("(\\w{1,3}\\s{1,2}\\d{1,2} \\d{2}:\\d{2}:\\d{2}) (\w+).*? (\\S+?): from=<?(.*?)>?, size=(.*?), class=(.*?),(?: pri=(.*?),)? nrcpts=(.*?),(?: msgid=<?(.*?)>?,)? (?:bodytype=(.*?), )?(?:proto=(.*?), )?(?:daemon=(.*?), )?relay=(.* \\[.*\\]).*$")
to_regex_sendmail=re.compile("(\\w{1,3}\\s{1,2}\\d{1,2} \\d{2}:\\d{2}:\\d{2}).*? (\\S+?): to=<?(.*?)>?,(?: ctladdr=<?(.*?)>? [^,]*,)? delay=(.*?),(?: xdelay=(.*?),)? mailer=(.*?),(?: pri=(.*?),)?(?: relay=(.*?) \\[(.*?)\\],)?(?: dsn=(.*?),)? stat=(\\w+):? (.*)");




def parse_logs(logfile):
	transactions={}
	
	if logfile=="-":
		for line in sys.stdin.readlines():
			parse_postfix_extract_info(line.strip('\n'),transactions) or parse_sendmail_extract_info(line.strip('\n'),transactions)
	else:
		for line in fileinput.input(logfile):
			parse_postfix_extract_info(line.strip('\n'),transactions) or parse_sendmail_extract_info(line.strip('\n'),transactions)
	return transactions



def parse_postfix_extract_info(log_line,transactions):
	tmp_dict={}
	trans_id=""


	value=client_regexp_postfix.match(log_line)
	if value!=None:
		trans_id=value.groups()[2]
		if trans_id not in transactions:
			transactions[trans_id] = initialize_trans_entry()
		transactions[trans_id]['date']=value.groups()[0]
		transactions[trans_id]['client']=value.groups()[3]
		transactions[trans_id]['host']=value.groups()[1]
		return True

	value=msgid_regexp_postfix.match(log_line)
	if value!=None:
		trans_id=value.groups()[1]
		if trans_id not in transactions:
			transactions[trans_id] = initialize_trans_entry()
		transactions[trans_id]['msgid']=value.groups()[2]
		return True

	value=from_regexp_postfix.match(log_line)
	if value!=None:
		trans_id=value.groups()[1]
		if trans_id not in transactions:
			transactions[trans_id] = initialize_trans_entry()
		transactions[trans_id]['from']=value.groups()[2]
		return True


	value=to_regexp_postfix.match(log_line)
	if value!=None:
		trans_id=value.groups()[1]
		if trans_id not in transactions:
			transactions[trans_id] = initialize_trans_entry()
		transactions[trans_id]['to'].append({'recipient': value.groups()[2],'relay':value.groups()[3],'status': value.groups()[4]})
		return True

	value=local_regexp_postfix.match(log_line)
	if value!=None:
		trans_id=value.groups()[1]
		if trans_id not in transactions:
			transactions[trans_id] = initialize_trans_entry()
		transactions[trans_id]['to'].append({'recipient': value.groups()[2],'relay':value.groups()[3],'status': value.groups()[4]})
		return True


	value=removed_regexp_postfix.match(log_line)
	if value!=None:
		trans_id=value.groups()[1]
		if trans_id not in transactions:
			transactions[trans_id] = initialize_trans_entry()
		return True
	return False

def parse_sendmail_extract_info(log_line,transactions):
	tmp_dict={}
	trans_id=""
	global to_filter


	value=from_regex_sendmail.match(log_line)
	if value != None:
		trans_id=value.groups()[2]
		if trans_id not in transactions:
			transactions[trans_id] = initialize_trans_entry()

		transactions[trans_id]['from']=value.groups()[3].replace('>',"").replace('<',"")
		transactions[trans_id]['msgid']=value.groups()[8]
		transactions[trans_id]['client']=value.groups()[12]
		transactions[trans_id]['host']=value.groups()[1]
		return True
			


	value=to_regex_sendmail.match(log_line)
	if value != None:
		trans_id=value.groups()[1]
		if trans_id not in transactions:
			transactions[trans_id] = initialize_trans_entry()
	
		transactions[trans_id]['relay']=value.groups()[8]
		transactions[trans_id]['status']=value.groups()[11]
		transactions[trans_id]['date']=value.groups()[0]
		for email in value.groups()[2].replace('>',"").replace('<',"").split(','):
			transactions[trans_id]['to'].append({'recipient': email,'relay':value.groups()[8],'status': "%s %s" % (value.groups()[11],value.groups()[12])})
				
		return True

	return trans_id != ""
		
			
def initialize_trans_entry():
	return {'from': '',
	'to': [],
	'msgid': '',
	'date': '',
	'client': '',
	'host': ''
	}




def help():
	print "%s is a script that parses Sendmail and Postfix logs looking for e-mail transactions.\n" % os.path.basename(sys.argv[0])
	print "-l  log file to parse.  - when the log file is piped to stdin"
	print "-s server where we want to store the transactions"
	print "-p port where the server is listening"
	print "-y We are indexing logs from previous year. Syslog has no year field :p"

	


def main():
	global months
	months=dict((v,k) for k,v in enumerate(calendar.month_abbr))
	trans_dict={}
	logfile=""
	server="127.0.0.1"
	port="9200"
	prevYear=False
	pidfile = "/var/tmp/elasticsearch_indexer.pid"


	try:
		options, args = getopt.getopt(sys.argv[1:], 'l:s:p:r:y')
	except getopt.GetoptError:
		    help()
		    sys.exit(1)
	try:
		for o, a in options:
			if o=="-l":
				logfile=a
			elif o=="-s": 
				server=a
			elif o=="-p": 
				port=a
			elif o=="-y": 
				prevYear=True
			else:
				help()
				sys.exit(1)
	except ValueError:
		help()
		print "getopt failed"
		sys.exit(1)



	pid = str(os.getpid())
	if os.path.isfile(pidfile):
		fd=open(pidfile,"r")
		old_pid=fd.readline().strip("\n")
		fd.close()
		if os.path.exists("/proc/%s" % old_pid):
			print "%s already exists, exiting" % pidfile
			sys.exit(1)
		else:
			"pidfile %s found but the process is not running" %pidfile
			os.unlink(pidfile)
	file(pidfile, 'w').write(pid)

	try:
		trans_dict = parse_logs(logfile)
		today=datetime.date.today().timetuple()
		for msg in trans_dict:
		
			# avoid malformed messages	
			if trans_dict[msg]['client']!= "" and  trans_dict[msg]['host']!="" and trans_dict[msg]['date']!="":
				ttuple=datetime.datetime.strptime("%s %s" % (datetime.date.today().year,trans_dict[msg]['date']),"%Y %b %d %H:%M:%S").timetuple()
				
				# Special case when today is January 1st and we index December 31st
				if prevYear or (ttuple[1]==12 and ttuple[2]==31 and today[1]==1 and today[2]==1):
					ttuple=datetime.datetime.strptime("%s %s" % (datetime.date.today().year-1,trans_dict[msg]['date']),"%Y %b %d %H:%M:%S").timetuple()

				trans_dict[msg]['date']=time.strftime("%Y-%m-%dT%H:%M:%S",ttuple)
				req = urllib2.Request('http://%s:%s/email_transactions/transactions/%s' % (server,port,msg), json.dumps(trans_dict[msg]), {'Content-Type': 'application/json'})
				f = urllib2.urlopen(req)
				response = f.read()
				f.close()
		os.unlink(pidfile)
	except IOError:
		os.unlink(pidfile)
		print "the log file does not exist"
		help()
		sys.exit(1)
	


if __name__ == "__main__":
	sys.exit(main())
