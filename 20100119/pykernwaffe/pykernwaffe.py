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



import zipfile
import os.path
import os
import sys
import re

NQ_CAMPAIGN_PATTERN="^z_kwbig_cmpgn_\d{1,2}\.\d{2}\.pk3"
WOLF_HOME_DIR=os.environ['HOME']+"/.etwolf/"
WOLF_MAIN_DIR=WOLF_HOME_DIR+"etmain/"
NQ_MAIN_DIRS=['nq','noquarter']
CAMPAIGN_FILENAME_PATTERN="^scripts\/cmpgn_kw.+\.campaign"
SRVNAME_PATTERN='\s+name\s+"([\d\w\.]+)"'
MAPLIST_PATTERN='\s+maps\s+"([\d\w\._\-\;\[\]]+)"'


# return a list of campaing files
def getCampaignDefinitions():
	fileList=[]
	pattern=re.compile(NQ_CAMPAIGN_PATTERN)

	for directoryIndex in range(len(NQ_MAIN_DIRS)):
		if os.path.isdir(WOLF_HOME_DIR+NQ_MAIN_DIRS[directoryIndex]):
			dirListing=os.listdir(WOLF_HOME_DIR+NQ_MAIN_DIRS[directoryIndex])

		# we add the full path to the directory listing
		map(lambda x: WOLF_HOME_DIR+NQ_MAIN_DIRS[directoryIndex]+"/"+x, dirListing)
		
		# we use re to get the files that are campaing definition
		fileList.extend(filter(lambda x:os.path.isfile(x) and pattern.match(os.path.basename(x)) != None,\
			map(lambda x: WOLF_HOME_DIR+NQ_MAIN_DIRS[directoryIndex]+"/"+x, dirListing)))
	fileList.sort()
	return fileList


# true if the directories exist
def isNqInstalled():
	installed=False
	directoryIndex=0
	while directoryIndex < len(NQ_MAIN_DIRS) and not installed:
		installed=os.path.isdir(WOLF_HOME_DIR+NQ_MAIN_DIRS[directoryIndex]+"/")
		directoryIndex=directoryIndex+1

	return installed


# TO BE REVISED
def parseCmpgnFile(data):
	serverName=re.findall(SRVNAME_PATTERN,data,re.MULTILINE)[0]
	mapString=re.findall(MAPLIST_PATTERN,data,re.MULTILINE)[0]
	return serverName , mapString.strip(';').split(';')


def fetchMaps(zipFile):
	patternFile=re.compile(CAMPAIGN_FILENAME_PATTERN)
	campaingList=[]
	zipPointer=zipfile.ZipFile(zipFile, "r")
	for name in zipPointer.namelist():
		if patternFile.match(name) != None:
			serverName, mapList=parseCmpgnFile(zipPointer.read(name))
			campaingList.extend(mapList)
	zipPointer.close()

	return serverName, campaingList


def createMapDict(fileList):
	mapDict={}
	for file in fileList:
		server,mapList=fetchMaps(file)
		mapDict[server]=mapList
	return mapDict


def listDownloadedMaps():
	dirListing=[]
	if os.path.isdir(WOLF_MAIN_DIR):
		dirListing=os.listdir(WOLF_MAIN_DIR)

	#return filter(lambda x:os.path.isfile(x) and re.match("pk3$",x) !=None and re.match("z_",x) ==None and re.match("pak\d.pk3$",x) !=None,dirListing)
	list=filter(lambda x:  re.match("^.*\.pk3$",x) !=None and re.match("^(z_|pak)",x) ==None ,dirListing)
	list.sort()
	return list
def getUnusedMaps(fullMapList,srvMapDic):
	badNameMap=[]
	for server in srvMapDic:
		for map in  srvMapDic[server]:
			try:
				fullMapList.remove(map+'.pk3')
			except:
				badNameMap.append(map+'.pk3')
	return badNameMap	

def main(argv=None):
	mapDict={}
	if not os.path.isdir(WOLF_HOME_DIR):
		print WOLF_HOME_DIR+" directory does not exist. Are you sure you are playing ET? ^^"
		sys.exit(1)
	
	if not os.path.isdir(WOLF_MAIN_DIR):
		print WOLF_MAIN_DIR+" directory does not exist. Are you sure you are playing ET? ^^"
		sys.exit(1)

	if not isNqInstalled():
		print "Are you sure you play in Kernwaffe? I can't found any NQ installation!"
		sys.exit(1)

	fileList=getCampaignDefinitions()
	if fileList == None:
		print "Ops I can't find the campaing files!! oO"
		sys.exit(1)
	mapDict=createMapDict(fileList)
	mapList=listDownloadedMaps()

	print ""
	print "MAPS LOADED IN KERNWAFFE SERVERS"
	print "--------------------------------"
	print ""

	for server in mapDict:
		print "Map listing for server %s:\n%s\n" % (server,' '.join((mapDict[server])))


	# used maps that we were unable to delete from the map list.
	# It may happen if:
	# - the same map is being played in more than one server
	# - the map name and the file name are different 
	badNames=getUnusedMaps(mapList,mapDict)

	
	print ""
	print "MAPS THAT YOU MAY NOT BE USING"
	print "------------------------------"
	print ""
	print "Errors found:"
	print """I tried to delete the following maps from the unused list but an error was found. It may happen if:
	- the same map is being played in more than one server
	- the map name and the file name in etmain folder are different"""
	print "\nCheck carefully the maps marked as not being used, before deletting anything. I am not responsible if you break your config!! :p\n"
	print "maps marked as 'broken':\n%s" %(' '.join(badNames))
	print "\n\n"
	print "Maps not being used:\n\n%s:\n" % ('\n'.join(mapList))

if __name__ == "__main__":
	sys.exit(main())





