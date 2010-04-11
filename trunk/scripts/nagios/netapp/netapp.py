#! /usr/bin/env python

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





import sys, os, getopt


def snmp_get_oid(host,oid):
	return os.popen("/usr/bin/snmpget -v1 -Cf  -Oqv -c public -m NETWORK-APPLIANCE-MIB   %s  %s" % (host , oid)).read()



def usage():
	print "usage: netapp -h <hostname> -t <test > (fan|power|battery|disks|temperature|support|cpu <-w,-c>)"
	print "-h hostname : Netapp appliance being monitored"
	print "-t test : test being performed"


def parameters():
	host=""
	test=""
	warning=""
	critical=""

	if len(sys.argv) <2 :
		usage()
	        sys.exit(status['UNKNOWN'])

	try:
	     opts, args = getopt.getopt(sys.argv[1:], "h:t:w:c:")
	except getopt.GetoptError, err:
		print str(err) 
		usage()
	        sys.exit(status['UNKNOWN'])
	output = None
	verbose = False
	
	for o, a in opts:
		if o == "-h":
			host=a
		elif o== "-t":
			test=a
		elif o== "-w":
			warning=a
		elif o== "-c":
			critical=a
	try:
		if int(warning) >= int(critical):
			print " Parameter -w <warning> must be lower than -c <critical> \n"
			usage()
	        	sys.exit(status['UNKNOWN'])
	except ValueError:
		#parameter not given in the command line
		pass


	if host=="" or test=="":
		usage()
	        sys.exit(status['UNKNOWN'])

	return host, test,warning,critical


def netapp_fan_check():


	FailedFanCount  = int(snmp_get_oid(host,'envFailedFanCount.0'))
	FanFailedMessage  = snmp_get_oid(host,'envFailedFanMessage.0').strip()


	if FailedFanCount > 0:
		print "CRITICAL -  Number of failed fans at %s: %s. MSG: %s" % (host,FailedFanCount,FanFailedMessage)
		sys.exit(status['CRITICAL'])
	else:
		print "OK -  Number of failed fans at %s: %s. MSG: %s" % (host,FailedFanCount,FanFailedMessage)
		sys.exit(status['OK'])


def netapp_powersupply_check():
	FailedPowerCount  = int(snmp_get_oid(host,'envFailedPowerSupplyCount.0'))
	PowerSupplyFailedMessage  = snmp_get_oid(host,'envFailedPowerSupplyMessage.0')
	if FailedPowerCount > 0 :
	        print "CRITICAL -  Number of nower Supplies failing at %s: %s. MSG: %s" % (host,FailedPowerCount,PowerSupplyFailedMessage)
	        sys.exit(status['CRITICAL'])
	else:
	        print "OK -  Number of nower Supplies failing at %s: %s. MSG: %s" % (host,FailedPowerCount,PowerSupplyFailedMessage)
	        sys.exit(status['OK'])


def netapp_battery_check():
	BatteryStatus  = snmp_get_oid(host,'nvramBatteryStatus.0').strip()
	if BatteryStatus !=  "ok":
	        print "CRITICAL -  Battery at %s not in perfect state. MSG: %s" % (host,BatteryStatus)
	        sys.exit(status['CRITICAL'])
	else:
	        print "OK -  Battery status at %s ok. MSG: %s" % (host,BatteryStatus)
	        sys.exit(status['OK'])

def netapp_disks_check():
	FailedCount  = int(snmp_get_oid(host,'diskFailedCount.0'))
	FailMessage  = snmp_get_oid(host,'diskFailedMessage.0')
	if FailedCount > 0 :
		print "CRITICAL -  Number of failed disks at %s: %s. MSG: %s" % (host,FailedCount,FailMessage)
		sys.exit(status['CRITICAL'])
	else:
		print "OK -  Number of failed disks at %s: %s. MSG: %s" % (host,FailedCount,FailMessage)
		sys.exit(status['OK'])


def netapp_support_check():
	SupportStatus  = snmp_get_oid(host,'autosupportStatus.0').strip()
	SupportFailedMessage  = snmp_get_oid(host,'autosupportStatusMessage.0')
	if SupportStatus !=  "ok":
	        print "CRITICAL -  Error in autosupport detected at %s. Status: %s" % (host,SupportFailedMessage)
	        sys.exit(status['CRITICAL'])
	else:
	        print "OK -  Autosupport at %s ok. Status: %s" % (host,SupportFailedMessage)
	        sys.exit(status['OK'])


def netapp_temperature_check():
	TemperatureStatus  = snmp_get_oid(host,'envOverTemperature.0').strip()
	if TemperatureStatus !=  "no":
	        print "CRITICAL -  High temperature detected at %s." % (host)
	        sys.exit(status['CRITICAL'])
	else:
	        print "OK -  Temperature at %s ok." % (host)
	        sys.exit(status['OK'])

def netapp_cpu_check():

	if warning=="" or critical =="":
		print " Parameters -w <warning> or -c <critical> are missing\n"
		usage()
	        sys.exit(status['UNKNOWN'])

	CpuStatus  = int(snmp_get_oid(host,'cpuBusyTimePerCent.0'))
	if 0 < CpuStatus < int(warning):
	        print "OK -  CPU at %s - cpu = %s%%" % (host,CpuStatus)
	        sys.exit(status['OK'])

	elif  int(warning) < CpuStatus < int(critical):
	        print "WARNING -  CPU at %s - cpu = %s%%" % (host,CpuStatus)
	        sys.exit(status['WARNING'])
	else:
	        print "CRITICAL -  CPU at %s - cpu = %s%%" % (host,CpuStatus)
	        sys.exit(status['CRITICAL'])

status = { 'OK' : 0 , 'WARNING' : 1, 'CRITICAL' : 2 , 'UNKNOWN' : 3}

host=""
test=""
warning=""
critical=""

host,test,warning,critical =parameters()

if test == "fan":
	netapp_fan_check()
elif test == "power":
	netapp_powersupply_check()
elif test == "battery":
	netapp_battery_check()
elif test == "disks":
	netapp_disks_check()
elif test == "temperature":
	netapp_temperature_check()
elif test == "support":
	netapp_support_check()
elif test == "cpu":
	netapp_cpu_check()
else:
	usage()
	sys.exit(2)
