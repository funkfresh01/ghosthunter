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

import json
import urllib2
import urllib
import sys
import datetime
import getopt
import os.path
import re


def display_transaction(trans_id,trans_dict):
	print "transaction: %s " % trans_id
	print "client:\t%s" %trans_dict['client']
	print "from:\t%s" %trans_dict['from']
	print "msgid:\t%s" %trans_dict['msgid']
	print "date:\t%s" % datetime.datetime.strptime(trans_dict['date'],"%Y-%m-%dT%H:%M:%S") 
	for entry in trans_dict['to']:
	        print "to:\trecipent='%s' , relay='%s', status='%s'" % (entry['recipient'],entry['relay'],entry['status'])
	print "host:\t%s" %trans_dict['host']
	print


def query_server(query):
	global server
	global port
	global number_results

	req = urllib2.Request('http://%s:%s/email_transactions/transactions/_search?size=%s' % (server,port,number_results), query, {'Content-Type': 'application/json'})
	f = urllib2.urlopen(req)
	response = f.read()
	dict_response=json.loads(response)
	f.close()
	return dict_response





def build_simple_query(pattern,field):
	return '{ \
		"sort": [ { "date" : "desc" } ], \
		"query": { \
			"query_string" : { \
				"query" : "%s","default_field" : "%s"} \
			} \
		}' %(pattern,field)


def build_complex_query(dict,start_date_filter,finish_date_filter):
	strTmp=[]
	d1=[]
	d2=[]



	for query in dict:
		strTmp.append ('{ "field":{ "%s":{"query": "%s", "type" : "phrase" } } }' %(query['field'],query['pattern']))


	if start_date_filter!="" and finish_date_filter!="":
		d1=re.compile("^(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}:\d{2})$").match(start_date_filter).groups()
		d2=re.compile("^(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}:\d{2})$").match(finish_date_filter).groups()
		mydate='{"range":{ "date":{"from": "%sT%s" ,"to": "%sT%s"}}}' % (d1[0],d1[1],d2[0],d2[1])
		strTmp.append(mydate)

	return '{ \
			"sort": [ { "date" : "desc" } ], \
			"query": { \
				"bool": { \
					"must":[ %s ] \
				} \
			} \
		}' % (','.join(strTmp))


def simple_search(dict):
	results=[]
	dict_response=[]
	dict_response=query_server(build_simple_query(dict['pattern'],dict['field']))
	try:
		results=dict_response['hits']['hits']
	except KeyError:
		pass
	return results

def complex_search(dict,start_date_filter,finish_date_filter):
	results=[]
	dict_response=[]
	dict_response=query_server(build_complex_query(dict,start_date_filter,finish_date_filter))
	try:
		results=dict_response['hits']['hits']
	except KeyError:
		pass
	return results

def help():
	print "%s is a script that parses Sendmail and Postfix logs looking for e-mail transactions.\n" % os.path.basename(sys.argv[0])
	print "-f sender filter"
	print "-t recipient filter"
	print "-i msgid filter"
	print "-h host filter"
	print "-d start date in ISO format: 2011-12-08 21:49:32"
	print "-D finish date in ISO format: 2011-12-08 21:49:32"
	print "-s server to which we send the query. 127.0.0.1 by default"
	print "-p port on which the server is listening on. 9200 by default"
	print "-r maximum number of records to display. 200 by default"
	print "\n At least the -l flag and one filter are required to perform the search"

def main():
	global server
	global port
	global number_results

	server="127.0.0.1"
	port="9200"
	number_results="200"

	results=[]
	from_filter=""
	to_filter=""
	host_filter=""
	start_date_filter=""
	finish_date_filter=""
	msgid_filter=""
	dict=[]

	try:
		options, args = getopt.getopt(sys.argv[1:], 'f:t:i:d:D:s:p:r:h:')
	except getopt.GetoptError:
		    help()
		    sys.exit(1)
	try:
		for o, a in options:
			if o=="-f":
				from_filter=a.replace("@"," AND ")
			elif o=="-t":
				to_filter=a.replace("@"," AND ")
			elif o=="-i":
				msgid_filter=a.replace("@"," AND ")
			elif o=="-d":
				if re.compile("^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$").match(a) == None:
					help()
					sys.exit(1)
				start_date_filter=a
			elif o=="-D":
				if re.compile("^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$").match(a) == None:
					help()
					sys.exit(1)
				finish_date_filter=a
			elif o=="-s":
				server=a
			elif o=="-p":
				port=a
			elif o=="-r":
				number_results=a
			elif o=="-h":
				host_filter=a
			else:
				help()
				sys.exit(1)
	except ValueError:
		help()
		print "getopt failed"
		sys.exit(1)


	if from_filter =="" and to_filter=="" and msgid_filter=="" and host_filter=="":
		print "No filter specified"
		help()
		sys.exit(1)

	if start_date_filter!="" or finish_date_filter!="":
		if not (start_date_filter!="" and finish_date_filter!=""):
			print "When specifying date filters, you must specify the start and the finish dates"
			help()
			sys.exit(1)



	if from_filter!="":
		dict.append({"field": "from", "pattern":from_filter})
	if to_filter!="":
		dict.append({"field": "to.recipient", "pattern":to_filter})
	if msgid_filter!="":
		dict.append({"field": "msgid", "pattern":msgid_filter})
	if host_filter!="":
		dict.append({"field": "host", "pattern":host_filter})



	if len(dict) > 1:
		results=complex_search(dict,start_date_filter,finish_date_filter)
	elif len(dict) == 1 and (start_date_filter!="" and finish_date_filter!=""):
		results=complex_search(dict,start_date_filter,finish_date_filter)
	else:
		results=simple_search(dict[0])


	for key in  results:
		display_transaction(key['_id'],key['_source'])

if __name__ == "__main__":
	sys.exit(main())
