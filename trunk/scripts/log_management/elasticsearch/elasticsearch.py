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
from datetime import datetime
import time
import json
import urllib2
import urllib



client_regexp_postfix=re.compile("^(\w+) postfix/smtpd\[\d+\]: (\w{1,11}): client=([\w\.\-\_]+\[[0-9.]+\]).*$")
from_regexp_postfix=re.compile("^\w+ postfix/qmgr\[\d+\]: (\w{1,11}): from=<(.*)>.*$")
removed_regexp_postfix=re.compile("^\w+ postfix/qmgr\[\d+\]: (\w{1,11}): removed")
msgid_regexp_postfix=re.compile("^\w+ postfix/cleanup\[\d+\]: (\w{1,11}): message-id=<(.*)>$")
to_regexp_postfix=re.compile("^\w+ postfix/smtp\[\d+\]: (\w{1,11}): to=<(.*)>, relay=([\w\.]+\[[0-9.]+\]:\d{1,5}), delay=[0-9.]{1,4}, delays=[0-9.]{1,4}/[0-9.]{1,4}/[0-9.]{1,4}/[0-9.]{1,4}, dsn=[0-9.]{5}, status=(\w+ \(.+\))$")
local_regexp_postfix=re.compile("^\w+ postfix/local\[\d+\]: (\w{1,11}): to=<(.*)>, relay=(.+), delay=[0-9.]{1,4}, delays=[0-9.]{1,4}/[0-9.]{1,4}/[0-9.]{1,4}/[0-9.]{1,4}, dsn=[0-9.]{5}, status=(\w+ \(.+\))$")

from_regex_sendmail= re.compile("(\w+).*? (\\S+?): from=<?(.*?)>?, size=(.*?), class=(.*?),(?: pri=(.*?),)? nrcpts=(.*?),(?: msgid=<?(.*?)>?,)? (?:bodytype=(.*?), )?(?:proto=(.*?), )?(?:daemon=(.*?), )?relay=(.* \\[.*\\]).*$")
to_regex_sendmail=re.compile(".*? (\\S+?): to=<?(.*?)>?,(?: ctladdr=<?(.*?)>? [^,]*,)? delay=(.*?),(?: xdelay=(.*?),)? mailer=(.*?),(?: pri=(.*?),)?(?: relay=(.*?) \\[(.*?)\\],)?(?: dsn=(.*?),)? stat=(\\w+):? (.*)");


def query_server(query):
	global server
	global port
	global number_results

	dict_response=[]
	try:

		req = urllib2.Request('http://%s:%s/graylog2/message/_search?size=%s' % (server,port,number_results), query , {'Content-Type': 'application/json'})
		f = urllib2.urlopen(req,timeout=300)
		response = f.read()
		dict_response=json.loads(response)
		f.close()
	except urllib2.URLError:
		print "Query failed timeout"
	return dict_response


def write_server(key,trans_dict):
	global server
	global port
	try:
		req = urllib2.Request('http://%s:%s/email_transactions/transactions/%s' % (server,port,key), json.dumps(trans_dict[key]), {'Content-Type': 'application/json'})
		f = urllib2.urlopen(req,timeout=300)
		response = f.read()
		f.close()
	except TypeError:
		print "%s failed" %key
		pass
	except urllib2.HTTPError:
		print "%s failed HTTPError" %key
		pass
	except urllib2.URLError:
		print "%s failded timeout"

def build_simple_query():
	global time_frame
	mytime=(time.time() - (60*time_frame)) #delta time used to search the logs
        return '{"from":0,"filter":{"range":{"created_at":{"gt":%s,"lt":null}}},"sort":[{"created_at":"desc"}],"query":{"bool":{"must":[{"query_string":{"query":"message:postfix OR sendmail"}}]}}}' % str(mytime)


def simple_search():
	results=[]
	dict_response=[]
	dict_response=query_server(build_simple_query())
	try:
		results=dict_response['hits']['hits']
	except KeyError:
		pass
	except TypeError:
		pass
	return results


def parse_logs():
	transactions={}

	for log_line in simple_search():
		#We add the host to the log line
		timestamp=int(log_line['_source']['created_at'])
		#trans=log_line['_source']['full_message'].split(" ")
		trans=log_line['_source']['message'].split(" ")
		trans.insert(0,log_line['_source']['host'])
		line=" ".join(trans)
		parse_postfix_extract_info(line.strip('\n'),timestamp,transactions) or parse_sendmail_extract_info(line.strip('\n'),timestamp,transactions)

	return transactions



def parse_postfix_extract_info(log_line,timestamp,transactions):
	tmp_dict={}
	trans_id=""

	value=client_regexp_postfix.match(log_line)
	if value!=None:
		trans_id=value.groups()[1]
		if trans_id not in transactions:
			transactions[trans_id] = initialize_trans_entry()
		transactions[trans_id]['date']=time.strftime("%Y-%m-%dT%H:%M:%S",datetime.fromtimestamp(timestamp).timetuple())

		transactions[trans_id]['client']=value.groups()[2]
		transactions[trans_id]['host']=value.groups()[0]
		return True

	value=msgid_regexp_postfix.match(log_line)
	if value!=None:
		trans_id=value.groups()[0]
		if trans_id not in transactions:
			transactions[trans_id] = initialize_trans_entry()
		transactions[trans_id]['msgid']=value.groups()[1]
		return True

	value=from_regexp_postfix.match(log_line)
	if value!=None:
		trans_id=value.groups()[0]
		if trans_id not in transactions:
			transactions[trans_id] = initialize_trans_entry()
		transactions[trans_id]['from']=value.groups()[1]
		return True


	value=to_regexp_postfix.match(log_line)
	if value!=None:
		trans_id=value.groups()[0]
		if trans_id not in transactions:
			transactions[trans_id] = initialize_trans_entry()
		transactions[trans_id]['to'].append({'recipient': value.groups()[1],'relay':value.groups()[2],'status': value.groups()[3]})
		return True

	value=local_regexp_postfix.match(log_line)
	if value!=None:
		trans_id=value.groups()[0]
		if trans_id not in transactions:
			transactions[trans_id] = initialize_trans_entry()
		transactions[trans_id]['to'].append({'recipient': value.groups()[1],'relay':value.groups()[2],'status': value.groups()[3]})
		return True


	value=removed_regexp_postfix.match(log_line)
	if value!=None:
		trans_id=value.groups()[0]
		if trans_id not in transactions:
			transactions[trans_id] = initialize_trans_entry()
		return True
	return False

def parse_sendmail_extract_info(log_line,timestamp,transactions):
	tmp_dict={}
	trans_id=""
	global to_filter


	value=from_regex_sendmail.match(log_line)
	if value != None:
		trans_id=value.groups()[1]
		if trans_id not in transactions:
			transactions[trans_id] = initialize_trans_entry()

		transactions[trans_id]['from']=value.groups()[2].replace('>',"").replace('<',"")
		transactions[trans_id]['msgid']=value.groups()[7]
		transactions[trans_id]['client']=value.groups()[11]
		transactions[trans_id]['host']=value.groups()[0]
		return True
			


	value=to_regex_sendmail.match(log_line)
	if value != None:
		trans_id=value.groups()[0]
		if trans_id not in transactions:
			transactions[trans_id] = initialize_trans_entry()
	
		transactions[trans_id]['relay']=value.groups()[7]
		transactions[trans_id]['status']=value.groups()[10]
		transactions[trans_id]['date']=time.strftime("%Y-%m-%dT%H:%M:%S",datetime.fromtimestamp(timestamp).timetuple())
		for email in value.groups()[1].replace('>',"").replace('<',"").split(','):
			transactions[trans_id]['to'].append({'recipient': email,'relay':value.groups()[7],'status': "%s %s" % (value.groups()[10],value.groups()[11])})
				
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
	print "-s server runnning elastic search"
	print "-p port where the server is listening"
	print "-r number of results to request to the elasticsearch server. 1000000 by default"
	print "-t time frame in minutes. ie. -t 60 would request the logs from the last 60 minutes"

	


def main():
	global months
	global server
	global port
	global number_results
	global time_frame

	server="127.0.0.1"
	port="9200"
	number_results="1000000"
	trans_dict={}
	server="127.0.0.1"
	port="9200"
	time_frame=60
	pidfile = "/var/tmp/elasticsearch_indexer.pid"


	try:
		options, args = getopt.getopt(sys.argv[1:], 'p:r:t:')
	except getopt.GetoptError:
		    help()
		    sys.exit(1)
	try:
		for o, a in options:
			if o=="-p": 
				port=a
			elif o=="-r": 
				number_results=a
			elif o=="-t": 
				time_frame=int(a)
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

	trans_dict = parse_logs()

	for key in trans_dict:
		if trans_dict[key]['client']!= "" and  trans_dict[key]['host']!="" and trans_dict[key]['date']!="":
			write_server(key,trans_dict)
	os.unlink(pidfile)
	


if __name__ == "__main__":
	sys.exit(main())
