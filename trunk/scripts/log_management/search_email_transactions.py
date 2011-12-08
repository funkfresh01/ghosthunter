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
# POSSIBILITY OF SUCH DAMAGE.

import re
import sys
import fileinput
import getopt
import os.path
import os
import calendar
import datetime
import time



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
		transactions[trans_id]['to'][value.groups()[2]]={'relay':value.groups()[3],'status':value.groups()[4]}
		return True

	value=local_regexp_postfix.match(log_line)
	if value!=None:
		trans_id=value.groups()[1]
		if trans_id not in transactions:
			transactions[trans_id] = initialize_trans_entry()
		transactions[trans_id]['to'][value.groups()[2]]={'relay':value.groups()[3],'status':value.groups()[4]}
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
			transactions[trans_id]['to'][email]={'relay':value.groups()[8],'status': "%s %s" % (value.groups()[11],value.groups()[12])}
				
		return True

	return trans_id != ""
		
			
def initialize_trans_entry():
	return {'from': '',
	'to': {},
	'msgid': '',
	'date': '',
	'client': '',
	'host': ''
	}


def display_transaction(trans_id,trans_dict):
	print "transaction: %s " % trans_id
	print "client:\t%s" %trans_dict[trans_id]['client']
	print "from:\t%s" %trans_dict[trans_id]['from']
	print "msgid:\t%s" %trans_dict[trans_id]['msgid']
	print "date:\t%s" %trans_dict[trans_id]['date']
	for key in trans_dict[trans_id]['to']:
		print "to:\trecipent='%s' , relay='%s', status='%s'" % (key,trans_dict[trans_id]['to'][key]['relay'],trans_dict[trans_id]['to'][key]['status'])
	print "host:\t%s" %trans_dict[trans_id]['host']
	print



def find_by_msgid(msgid,trans_dict):
	return search_dict(msgid,trans_dict,"msgid")

def find_by_sender(sender,trans_dict):
	return search_dict(sender,trans_dict,"from")

def find_by_date(date,trans_dict):
	return search_dict(date,trans_dict,"date")

def find_by_recipient(recipient,trans_dict):
	dict={}
	pattern=re.compile(recipient)
	for key in trans_dict.iterkeys():
		try:
			for email in  trans_dict[key]['to']:
				if pattern.match(email) != None:
					dict[key]=trans_dict[key]
		except KeyError:
			print "key error"
		except re.error:
			print "regexp error"
	return dict

def search_dict(regexp,trans_dict,field):
	dict={}
	pattern=re.compile(regexp)
	for key in trans_dict.iterkeys():
		try:
			if pattern.match(str(trans_dict[key][field])) != None:
				dict[key]=trans_dict[key]
		except KeyError:
			print "key error"
		except re.error:
			print "regexp error"
	return dict



def filter_dict(dict):
	global from_filter
	global to_filter
	global date_filter
	global msgid_filter


	if msgid_filter !="":
		dict=find_by_msgid(msgid_filter,dict)
	if from_filter !="":
		dict=find_by_sender(from_filter,dict)
	if date_filter !="":
		dict=find_by_date(date_filter,dict)
	if to_filter !="":
		dict=find_by_recipient(to_filter,dict)

	return dict



def help():
	print "%s is a script that parses Sendmail and Postfix logs looking for e-mail transactions.\n" % os.path.basename(sys.argv[0])
	print "-l  log file to parse.  - when the log file is piped to stdin"
	print "-f sender filter"
	print "-t recipient filter"
	print "-i msgid filter"
	print "-d date filter as it would appear in a syslog file. ie Nov 29 04:39:15"
	print "\n At least the -l flag and one filter are required to perform the search"

def compare_transactions(x,y):
	xdate=(time.mktime(datetime.datetime.strptime("%s %s" % (datetime.date.today().year,x[1]['date']),"%Y %b %d %H:%M:%S").timetuple()))
	ydate=(time.mktime(datetime.datetime.strptime("%s %s" % (datetime.date.today().year,y[1]['date']),"%Y %b %d %H:%M:%S").timetuple()))

	if xdate > ydate: return 1
	elif xdate==ydate: return 0
	else: return -1

	


def main():
	global from_filter
	global to_filter
	global date_filter
	global msgid_filter
	global months
	months=dict((v,k) for k,v in enumerate(calendar.month_abbr))

	trans_dict={}
	from_filter=""
	to_filter=""
	date_filter=""
	msgid_filter=""
	logfile=""


	try:
		options, args = getopt.getopt(sys.argv[1:], 'l:f:t:i:d:')
	except getopt.GetoptError:
		    help()
		    sys.exit(1)
	try:
		for o, a in options:
			if o=="-l":
				logfile=a
			elif o=="-f":
				from_filter=a
			elif o=="-t":
				to_filter=a
			elif o=="-i":
				msgid_filter=a
			elif o=="-d":
				date_filter=a
			else:
				help()
				sys.exit(1)
	except ValueError:
		help()
		print "getopt failed"
		sys.exit(1)


	if from_filter =="" and to_filter=="" and to_filter=="" and date_filter=="" and msgid_filter=="":
		print "No filter specified"
		help()
		sys.exit(1)

	try:
		trans_dict = filter_dict(parse_logs(logfile))

		for msg in  sorted(trans_dict.iteritems(),compare_transactions ):
			display_transaction(msg[0],trans_dict)
	except IOError:
		print "the log file does not exist"
		help()
		sys.exit(1)
	


if __name__ == "__main__":
	sys.exit(main())
