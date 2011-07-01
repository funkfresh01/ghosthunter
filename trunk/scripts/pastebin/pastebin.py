#! /usr/bin/env python


# 
# Copyright (c) 2011 Xavier Garcia
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

import urllib
import re
import time
import fileinput
import sys
import signal
import os



regular_expressions=[]
seen_pasties=[]
max_pasties=500
matches=[]


def purge_old_pasties(size):
	global seen_pasties
	while len(seen_pasties) > size:
		seen_pasties.pop(0)


def fetch_regexp(file):
	global regular_expressions

	regular_expressions=[]
	print "[!] Loading regular expressions"
	for line in fileinput.input(file):
		regular_expressions.append(line.strip())


def list_pastes():
	try:
		f = urllib.urlopen('http://pastebin.com/archive')
		result=re.findall('<td class="icon"><a href="/(\w+)">.+</a></td>', f.read())
		f.close()
		return result
	except IOError:
		print "[!] Error fetching the list of pasties"
		return []


def fetch_paste(paste):
	params = urllib.urlencode({'i': paste})
	f = urllib.urlopen("http://pastebin.com/raw.php?%s" % params)
	data=f.read()
	f.close()
	return data

def analyze_paste(paste,data):
	matched_re={}
	for pattern in regular_expressions:
		length=len(re.findall(pattern, data,re.IGNORECASE))
		if length > 0:
			matched_re[pattern]=length

	return matched_re

def action(paste,patterns):
	pattern_list=""
	for elem in patterns:
		pattern_list=pattern_list+"%s [%s times] || " % (elem,patterns[elem])
	print "[!] Found Match.  http://pastebin.com/raw.php?i=%s :  %s; " % (paste, pattern_list)
	


def dump_matches(signum, stack):
	print "\n\nDumping stored matches:"
	for entry in matches:
		action(entry[0],entry[1])
	print "End of dump\n\n"

def reload_regexp(signum,stack):
	fetch_regexp(sys.argv[1])
	
		
def exit(signum,stack):
	print "[!] Quit"
	sys.exit(0)

def main():
	global regular_expressions
	global seen_pasties
	global max_pasties
	global matches
	status=""


	if len(sys.argv) !=2:
		print "%s  regular_expressions_file.txt" % sys.argv[0]
		return 3

	
	signal.signal(signal.SIGUSR1, dump_matches)
	signal.signal(signal.SIGHUP, reload_regexp)
	signal.signal(signal.SIGINT, exit)
	print '[!] My PID is:', os.getpid()
	fetch_regexp(sys.argv[1])


	while True:
		status=""
		for paste in list_pastes():
			if not paste in seen_pasties:
				try:
					patterns=analyze_paste(paste,fetch_paste(paste))
					if len(patterns) > 0:
						matches.append([paste,patterns])
						action(paste,patterns)
					seen_pasties.append(paste)
					time.sleep(2)
				except IOError:
					print "[!] Error fetching paste %s" % paste
		purge_old_pasties(max_pasties)
		time.sleep(30)

if __name__ == "__main__":
	sys.exit(main())

