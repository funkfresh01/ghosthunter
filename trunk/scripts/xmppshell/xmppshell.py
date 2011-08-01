#!/usr/bin/python

import sys
import xmpp
import time
import subprocess
import re
import os

commands={}
i18n={'en':{}}
i18n['en']['HELP']="Available commands: %s"
def helpHandler(user,command,args,mess):
    lst=commands.keys()
    lst.sort()
    return "HELP",', '.join(lst)

i18n['en']['EMPTY']="%s"
i18n['en']['EXEC']='Exec Response:\n %s'
def execHandler(user,command,args,mess):
    return "EXEC",execCommand(args)

i18n['en']["UNKNOWN COMMAND"]='Unknown command "%s". Try "help"'

def execCommand(cmd):

	try:
		proc = subprocess.Popen(cmd, shell=True,
			stdout=subprocess.PIPE, stderr=subprocess.PIPE,
			stdin=subprocess.PIPE)
		output= proc.stdout.read() + proc.stderr.read()
		return output

	except Exception:
		return "" 


def messageCB(conn,mess):
    text=mess.getBody()
    user=mess.getFrom()
    user.lang='en'      # dup
  
    account =str(user).split("/")[0]
    if account in VALID_ACCOUNTS:
 
    	if text.find(' ')+1: command,args=text.split(' ',1)
    	else: command,args=text,''
    	cmd=command.lower()

    	if commands.has_key(cmd): reply=commands[cmd](user,command,args,mess)
    	else: reply=("UNKNOWN COMMAND",cmd)

    	if type(reply)==type(()):
    	    key,args=reply
    	    if i18n[user.lang].has_key(key): pat=i18n[user.lang][key]
    	    elif i18n['en'].has_key(key): pat=i18n['en'][key]
    	    else: pat="%s"
    	    if type(pat)==type(''): reply=pat%args
    	    else: reply=pat(**args)
    	else:
    	    try: reply=i18n[user.lang][reply]
    	    except KeyError:
    	        try: reply=i18n['en'][reply]
    	        except KeyError: pass
    	if reply: 
		msgBuffer= reply.split("\n")
		msgBufferOffset=10
		for index in range(0,len(msgBuffer),msgBufferOffset):
			conn.send(xmpp.Message(mess.getFrom(),"\n".join(msgBuffer[index:index+msgBufferOffset])))
			time.sleep(0.5)


def LoadCommandHandlers():
	
	for i in globals().keys():
	    if i[-7:]=='Handler' and i[:-7].lower()==i[:-7]: commands[i[:-7]]=globals()[i]

############################# bot logic stop #####################################

def StepOn(conn):
    try:
        conn.Process(1)
    except KeyboardInterrupt: return 0
    return 1

def GoOn(conn):
    while StepOn(conn): pass

def LoadParams():
	jidparams={}
	if os.access(CONFIG_FILE,os.R_OK):
	    for ln in open(CONFIG_FILE).readlines():
	        if not ln[0] in ('#',';'):
	            key,val=ln.strip().split('=',1)
	            jidparams[key.lower()]=val
	for mandatory in ['jid','password']:
	    if mandatory not in jidparams.keys():
	        open(CONFIG_FILE,'w').write('#Uncomment fields before use and type in correct credentials.\n#JID=user@example.com/resource\n#PASSWORD=mypassword\n')
	        print 'Please point %s config file to valid JID for sending messages.' % CONFIG_FILE
	        sys.exit(0)

	return jidparams

CONFIG_FILE=os.environ['HOME']+'/.xsend'

#XMPP account that can send commands to our shell
VALID_ACCOUNTS=["valid.account@example.com"]

def main():
	
	params=LoadParams()
	LoadCommandHandlers()
	
	jid=xmpp.JID(params['jid'])
	user,server,password=jid.getNode(),jid.getDomain(),params['password']
	
	conn=xmpp.Client(server,debug=[])
	conres=conn.connect()
	if not conres:
	    print "Unable to connect to server %s!"%server
	    sys.exit(1)
	if conres<>'tls':
	    print "Warning: unable to estabilish secure connection - TLS failed!"
	    sys.exit(1)
	authres=conn.auth(user,password)
	if not authres:
	    print "Unable to authorize on %s - check login/password."%server
	    sys.exit(1)
	if authres<>'sasl':
	    print "Warning: unable to perform SASL auth os %s. Old authentication method used!"%server
	conn.RegisterHandler('message',messageCB)
	conn.sendInitPresence()
	GoOn(conn)


if __name__ == "__main__":
        sys.exit(main())
