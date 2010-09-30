#! /usr/bin/env python
import socket, sys, time, android

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




class EtServer:
	max_clients=0
	server_name=""
	port_number=0
	map_name="unknown"
	mod=""
	mod_version=""
	sv_punkbuster=[]
	timelimit=0
	newmap_flag=False
	error_flag=False
	continous_error_flag=False
	full_flag=False

	def __init__(self,server,port):
		self.server_name=server
		self.port_number=port

	def fetchData(self):
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		s.settimeout(10)
		MSG = "\xFF\xFF\xFF\xFFgetstatus\x00"
		details=[]
		try:
			s.connect((self.server_name,self.port_number))
			if len(MSG) != s.send(MSG):
				# where to get error message "$!".
				print "cannot send to %s(%d):" % (HOSTNAME,PORTNO)
				raise SystemExit(1)
			
			data = s.recv(20480)
			s.close()
			self.error_flag=False
			self.continous_error_flag=False
			details=data.split("\\")
			
			for item in range(1, len(details)):
				value=details[item]
				if value=="mod_version":
					self.mod_version=details[item+1]
				elif value=="gamename":
					self.mod=details[item+1]
				elif value=="mapname":
					if self.map_name!= details[item+1]:
						self.newmap_flag=True
					self.map_name=details[item+1]
				elif value=="sv_maxclients":
					self.max_clients=details[item+1]
				elif value=="sv_punkbuster":
					self.sv_punkbuster=details[item+1].split("\n")
					self.sv_punkbuster.pop(0)
					self.sv_punkbuster.pop(len(self.sv_punkbuster)-1)
				elif value=="timelimit":
					self.timelimit=details[item+1]
		except:
			if not self.error_flag:
				self.error_flag=True
				self.map_name="unknown"
			else:
				self.continous_error_flag=True

	def resetNewMapFlag(self):
		self.newmap_flag=False
	
	def getNewMapFlag(self):
		return self.newmap_flag

	def getErrorFlag(self):
		return self.error_flag

	def getContinousErrorFlag(self):
		return self.continous_error_flag

	def resetErrorFlag(self):
		self.error_flag=False


	def getMapName(self):		
		return self.map_name

	def getMaxClients(self):
		return self.max_clients

	def getCurrentClients(self):
		return len(self.sv_punkbuster)

	def getCurrentTime(self):
		return self.timelimit

	def getHostname(self):
		return self.server_name




class DisplayManager:

	@staticmethod
	def notification(title,msg):
		droid.notify(title,msg)
	@staticmethod
	def onScreenNotification(msg):
		droid.makeToast(msg)

	@staticmethod
	def sendAlarm(title,msg):
		droid.notify(title,msg)
		id, result,error= droid.checkRingerSilentMode()
		if not result:
			droid.ttsSpeak(msg)
		droid.vibrate()

def checkStatus(servers,initial):
	for entry in servers.keys():
		servers[entry].fetchData()
		if servers[entry].getErrorFlag():
			if  not servers[entry].getContinousErrorFlag():
				msg="error connecting to the server %s" % entry
				DisplayManager.sendAlarm("Kernwaffe status",msg)
		else:
		#It is the first pass and we do not care about new maps
			if initial:
				servers[entry].resetNewMapFlag()
				msg="%s:%s|%s/%s" % (entry,servers[entry].getMapName(),servers[entry].getCurrentClients(),servers[entry].getMaxClients())
				DisplayManager.notification("Kernwaffe status",msg)
			else:
				if servers[entry].getNewMapFlag():
					servers[entry].resetNewMapFlag()
					msg="%s:%s|%s/%s" % (entry,servers[entry].getMapName(),servers[entry].getCurrentClients(),servers[entry].getMaxClients())
					DisplayManager.notification("Kernwaffe status",msg)
				
			


droid = android.Android()
def main(argv=None):
	notify=False
	newmap=False
	config={"kw1":"","kw2":"","kw3":""}
	config["kw1"]={"hostname":"et.kernwaffe.de" , "port":27960}
	config["kw2"]={"hostname":"et2.kernwaffe.de", "port":27960}
	config["kw3"]={"hostname":"et3.kernwaffe.de", "port":27960}
	timer=60 #controls when we are going to do the next iteration

	servers={}


	#we create the server instances
	for entry in config.keys():
		servers[entry]=EtServer(config[entry]["hostname"],config[entry]["port"])

	DisplayManager.onScreenNotification("Kernwaffe monitor initialized")
	checkStatus(servers,initial=True)

	while True:
		time.sleep(timer)
		checkStatus(servers,initial=False)
	
	


if __name__ == "__main__":
        sys.exit(main())

