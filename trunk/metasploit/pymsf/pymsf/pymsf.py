#! /usr/bin/env python


# 
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




import xmlrpclib
import fileinput
import random
import string
import sys
from time import sleep
import base64
import readline
import threading

	
class MsfBase:
	def __init__(self):
		self.proxy=""
		self.token=""
		self.console_id=""

	def login(self,username,password):
		try:
			self.proxy = xmlrpclib.ServerProxy("http://localhost:55553")
			
			ret = self.proxy.auth.login(username,password)
			if ret['result'] == 'success':
				self.token = ret['token']
			else:
				print "Could not login\n"
				sys.exit(10)
		except Exception:
			print "Could not login: exception\n"
			sys.exit(0)
	

class MsfThreadFetchOutput(threading.Thread):
		leave=False
		consPtr=""
		def setCons(self,MsfCons):
			self.consPtr=MsfCons

		def run(self):
			while not self.leave:
				output= self.consPtr.fetch_console_output()
				if output!="":
					print output
				sleep(1)
		def kill(self):
			self.leave=True


class MsfConsole(MsfBase):
	prompt=""
	busy=False
	leave=False



	def isBusy(self):
		return self.busy

	def setBusy(self):
		self.busy=True

	def unsetBusy(self):
		self.busy=False
		

	def getPrompt(self):
		return self.prompt

	def setPrompt(self,prompt):
		self.prompt=prompt

	def create_console(self):
		cons=self.proxy.console.create(self.token)
		self.console_id=cons['id']
	
	
	def fetch_console_output(self):
		read={}
		read = self.proxy.console.read(self.token,self.console_id)
		data=""
	
		try:

			if read['busy']:
				self.setBusy()
			else:
				self.unsetBusy() 

			if self.getPrompt()!= base64.b64decode(read['prompt']):
					self.setPrompt(base64.b64decode(read['prompt']))
			data=base64.b64decode(read['data'])
		except KeyError:
			# session closed
			self.leave=True
			data=""

		return data
	
	
	def interact(self):
		input_buffer=""
		readline.parse_and_bind("tab: complete")
		readline.set_completer(self.command_completion)


		thrOutput=MsfThreadFetchOutput()
		thrOutput.setCons(self)
		thrOutput.start()
		sleep(1) # waiting for the thread to start fetching data
		while not self.leave:
			if not  self.isBusy():
				try:
					input_buffer= raw_input(self.prompt)
				except EOFError:
					self.leave=True
					break
				write = input_buffer + "\n"
				if write != '\n':
					n = self.proxy.console.write(self.token,self.console_id,base64.b64encode(write))
			sleep(1)
		thrOutput.kill()
	
	
	def destroy(self):
		self.proxy.console.destroy(self.token,self.console_id)


	
	def aux(self,module,opts,background=False):
		run=""
		if background:
			run="run -j\n"
		else:
			run="run \n"

		n = self.proxy.console.write(self.token,self.console_id,base64.b64encode("use %s\n"% module))
		for var in opts.keys():
			n = self.proxy.console.write(self.token,self.console_id,base64.b64encode("set %s %s\n"% (var,opts[var]) ))
		n = self.proxy.console.write(self.token,self.console_id,base64.b64encode("run\n"))

	def exploit(self,module,opts,background=False):
		run=""
		if background:
			run="run -j\n"
		else:
			run="run \n"
		n = self.proxy.console.write(self.token,self.console_id,base64.b64encode("use %s\n"% module))
		for var in opts.keys():
			n = self.proxy.console.write(self.token,self.console_id,base64.b64encode("set %s %s\n"% (var,opts[var]) ))
		n = self.proxy.console.write(self.token,self.console_id,base64.b64encode("exploit\n"))


	def command_completion(self,text,state):
		result=self.proxy.console.tabs(self.token,self.console_id,text)
		commands=result['tabs']
		for cmd in commands:
		        if cmd.startswith(text):
		            if not state:
               			 return cmd
			    else:
				state -= 1

class MsfBatch(MsfBase):

	def aux(self,module,opts):
		self.proxy.module.execute(self.token,"auxiliary",module,opts)

	def numJobs(self):
		return len(self.proxy.job.list(self.token)['jobs'].keys())

	def pendingJobs(self):
		return self.numJobs()!=0

	def waitJobsFinished(self):
		while self.pendingJobs():
			sleep(5)

	def numSessions(self):	
		sessions=self.proxy.session.list(self.token)
		if sessions=={}:
			return 0
		else:
			return len(self.proxy.session.list(self.token).keys())
	def listSessions(self):
		sessions=self.proxy.session.list(self.token)
		if sessions!={} :
			for key in sessions.keys():
				print "%s  :: %s" % (sessions[key]['via_exploit'],sessions[key]['target_host'])

