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
MAPLIST_PATTERN='\s+maps\s+"(.+)"'
DETECT_MAPFILE_PATTERN="(.+\.arena)$"
MAP_NAME_PATTERN="map\s+\"(.+)\""


# returns a tuple with map name and the fila associated
def mapNameAndFileRelation(zipFile):
	detectMapRE=re.compile(DETECT_MAPFILE_PATTERN,re.IGNORECASE)
	getMapNameRE=re.compile(MAP_NAME_PATTERN,re.IGNORECASE)
	index=0
	matched=False
	mapName=""
	arenaFile=""

	if not zipfile.is_zipfile(WOLF_MAIN_DIR+zipFile):
		return "CORRUPTED_ZIP",zipFile
	try:
	        zipPointer=zipfile.ZipFile(WOLF_MAIN_DIR+zipFile, "r")
		fileList=zipPointer.namelist()
		while index < len(fileList) and not matched:
			arenaFile=detectMapRE.findall(fileList[index])
			matched=len(arenaFile) > 0
			index=index+1

	        zipPointer.close()
	except:
		print "OOPS!! Error while reading file "+WOLF_MAIN_DIR+zipFile
		return "CORRUPTED_ZIP",zipFile
	if matched:
		# we have the file that contains the REAL map name!! :DDDD
	        zipPointer=zipfile.ZipFile(WOLF_MAIN_DIR+zipFile, "r")
		mapName=getMapNameRE.findall(zipPointer.read(arenaFile[0]))[0]
	        zipPointer.close()
		return mapName.lower(), zipFile
	else:
		return "PATCHES_OR_ADDONS",zipFile


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
		mapDict[server]=map(lambda x: x.lower(),mapList)
	return mapDict


def listDownloadedMaps():
	dirListing=[]
	if os.path.isdir(WOLF_MAIN_DIR):
		dirListing=os.listdir(WOLF_MAIN_DIR)

	#return filter(lambda x:os.path.isfile(x) and re.match("pk3$",x) !=None and re.match("z_",x) ==None and re.match("pak\d.pk3$",x) !=None,dirListing)
	list=filter(lambda x:  re.match("^.*\.pk3$",x) !=None and re.match("^(z_|pak)",x) ==None ,dirListing)
	list.sort()
	return list


def deleteUsedMaps(mapDict,storedMaps):
	for server in mapDict:
		for  mapName in mapDict[server]:
			try: storedMaps.pop(mapName)
			except: pass



def downloadedMapsDictionary():
	storedMaps={}
	mapName=""
	mapFile=""
	for mapName, mapFile in map(mapNameAndFileRelation,listDownloadedMaps()):
		try: storedMaps[mapName].append(mapFile)
		except: storedMaps[mapName]=[mapFile]
	return storedMaps



def main(argv=None):
	mapDict={}
	storedMaps={}

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
	storedMaps=downloadedMapsDictionary()

	print """
 __                                       _____  _____       
|  | __ ___________  ______  _  _______ _/ ____\/ ____\____  
|  |/ // __ \_  __ \/    \ \/ \/ /\__  \\\   __\\\   __\/ __ \ 
|    <\  ___/|  | \/   |  \     /  / __ \|  |   |  | \  ___/ 
|__|_ \\\___  >__|  |___|  /\/\_/  (____  /__|   |__|  \___  >
     \/    \/           \/             \/                 \/ 

Rulez (tm)
"""
	print ""
	print "MAPS LOADED IN KERNWAFFE SERVERS"
	print "--------------------------------"
	for server in mapDict:
		print "\nMap listing for server %s:" % (server)
		for mapName in mapDict[server]:
			try:
				# It will fail if we are using a original map, like fueldump
				# upper case problems, etc. WET SUCKS :DD
				print "%s ==> %s" % (mapName,' '.join((storedMaps[mapName])))
			except:
				print "ERR map name '%s' does not correspond to any downloaded map in etmain folder. Weird, no?" % (mapName)
				

	deleteUsedMaps(mapDict,storedMaps)

	print ""
	print "CORRUPTED MAPS DETECTED"
	print "-----------------------"
	print "We were unable to open the following maps (zip files):"
	try:
		print "%s" % ('\n'.join((storedMaps['CORRUPTED_ZIP'])))
		storedMaps.pop('CORRUPTED_ZIP')
	except: pass

	print ""
	print "FILES DETECTED AS SERVICE PACKS OR ADDONS"
	print "-----------------------------------------"
	try:
		print "%s" % ('\n'.join((storedMaps['PATCHES_OR_ADDONS'])))
		storedMaps.pop('PATCHES_OR_ADDONS')
	except: pass

	print ""
	print "MAPS NOT BEING USED"
	print "-------------------"
	try:
		for unusedMap in storedMaps: print "%s ==> %s" % (unusedMap,' '.join((storedMaps[unusedMap])))
	except: pass


if __name__ == "__main__":
	sys.exit(main())


