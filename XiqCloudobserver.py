#!/usr/bin/python3
##############################################################################
# Bell Computer Netzwerke GmbH
# Note: Change MACs/IPs from Infoblox in XMC/NAC groups
# Softwarename : XiqCloudobserver.py
# Version : 0.1
# Last Updated : October 25, 2025
# Written by: Stephan Harrer
#
# Purpose:  Add XIQ data to EIP cloud observer
#
#
# Copyright 2023
#
# Urheberrechtshinweis
# Alle Inhalte dieses Computerprogramms sind urheberrechtlich geschuetzt.
# Das Urheberrecht liegt bei der Bell Computer-Netzwerke GmbH.
# Eine Weitergabe und Veroeffentlichung, auch in Auszuegen ist untersagt
#
# Copyright notice
# All contents of this computer program are protected by copyright.
# The copyright is owned by Stephan Harrer Bell Computer-Netzwerke GmbH.
# A distribution and publication, even in extracts is prohibited.
#
##############################################################################

########################################################################
# Imports
########################################################################
import json
import sys
import time
import subprocess
import os
import copy

########################################################################
# Imports own
########################################################################
sys.path.append("/usr/local/custom/classes")
sys.path.append("/usr/local/custom/xiq")
import XIQ_API
import READ_PASSWORD



#Einschalten fuer debugging
debug = True

#EIP UUID
uuid = "8C531FF9-4751-4D97-ADB1-F1F47E500CDC"
folderName = "Meine"


def writeFile(newPassword):

    with open("psk.txt", "w") as file: #Anpassen
        file.write(psk)


def getItems(xiqCall,callType):

    pages = 1
    pagecounter = 1
    itemInfo = []

    if callType == "devices":
        viewType = "DETAIL"
    elif callType == "clients":
        viewType = "FULL"

    while(pagecounter <= pages):
        print("<<<<")
        print("There are " + str(pages))
        print(pagecounter)
        print("<<<<")
        if callType == "devices":
            response = xiqCall.getDevices(pagecounter,viewType)
        elif callType == "clients":
            response = xiqCall.getClients(pagecounter,viewType)
        items = response.json()

        if debug:
            #print(devices)
            print(json.dumps(items, indent=4))

        pages = items['total_pages']

        for item in items["data"]:
            itemInfo.append(item)
        
        pagecounter += 1
    
    print("------------")
    print("------------")
    print(json.dumps(itemInfo, indent=4))
    print("------------")
    print("------------")

    return itemInfo


def createWorker(currentTime,uuid):

    worker = {
        "type" : "worker",
        "uuid" : uuid,
        "ts" : currentTime
    }

    print(worker)
    return worker

def createFolder(folderName):

    folder = {
        "type" : "folder",
        "id" : folderName,
        "name" : folderName,
        "status" : "up"
    }

    print(folder)
    return folder

def createInstances(deviceInfo,folderName):

    instances = []

    for device in deviceInfo:

        if device["connected"] == True:
            deviceStatus = "up"
        else:
            deviceStatus = "down"

        if "hostname" in device:
            name = device["hostname"]
        else:
            name = device["mac_address"]

        instance = {
            "type" : "instance",
            "folder_id" : folderName,
            "id" : device["id"],
            "name" : name,
            "status" : deviceStatus
        }

        instances.append(instance)

    print (instances)
    return instances

def  createIp(deviceInfo,folderName):

    ipObjects = []
    ipLinks = []

    for device in deviceInfo:

        if device["connected"] == True:
            deviceStatus = "up"
        else:
            deviceStatus = "down"

        if "ip_address" in device:
            ipObject = {
                "type" : "ip",
                "folder_id" : folderName,
                "id" : device["ip_address"],
                "addr4" : device["ip_address"],
                "addr6" : "",
                "mac" : device["mac_address"],
                "status" : deviceStatus              
            }

            ipLink = {
                "type" : "linkipinstance",
                "ip_id" : device["ip_address"],
                "instance_id" : device["id"]                
            }

            ipObjects.append(ipObject)
            ipLinks.append(ipLink)

    return ipObjects,ipLinks


def createFile(deviceInfo,uuid,folderName):

    currentTime = int(time.time())

    worker = createWorker(currentTime,uuid)

    folder = createFolder(folderName)

    instances = createInstances(deviceInfo,folderName)

    ipObjects,ipLinks = createIp(deviceInfo,folderName)


    #{"type":"worker","uuid":"8C531FF9-4751-4D97-ADB1-F1F47E500CDC","ts":"1729195999"}
    #{"type":"folder","id":"folder-ext-1","name":"folder-ext-1","status":"1"}    
    #{"type":"instance","folder_id":"folder-ext-1","id":"instance-ext-1-1","name":"instance-ext-1-1","status":"up"}
    #{"type":"ip","folder_id":"folder-1","id":"ip-1","addr4":"1.1.1.1","addr6":"","mac":"00:00:01:01:01:01","status":"ok"}
    #{"type":"linkipinstance","ip_id":"ip-1","instance_id":"instance-1"}

    filename = uuid + "." + str(currentTime)
    with open(filename, "w") as file:
        file.write(json.dumps(worker) + "\n")
        file.write(json.dumps(folder) + "\n")
        for instance in instances:
            file.write(json.dumps(instance) + "\n")
        for ipObject in ipObjects:
            file.write(json.dumps(ipObject) + "\n")
        for ipLink in ipLinks:
            file.write(json.dumps(ipLink) + "\n")

    return filename

def copyFile(filename):

    
    p = subprocess.Popen(["scp", filename, "scp@10.80.0.11:/data1/tmp/cloud_observer"])
    sts = os.waitpid(p.pid, 0)   

    print(sts)

#Passwoerter lesen
pwType = "xiq"
pw = READ_PASSWORD.READ_PASSWORD()
xiqCreds = pw.loginData(pwType)

#Session in die Cloud aufbauen
try:
    xiqCall = XIQ_API.XIQ_API(xiqCreds['xiqUser'],xiqCreds['xiqPw']) # Login für XIQ
except TypeError as e:
    print(e)
    raise SystemExit
except:
    print("Unknown Error: Failed to generate token")
    raise SystemExit

callType = "devices"
deviceInfo = getItems(xiqCall,callType)

if len(deviceInfo) < 1:
    print("---->No devices read<----")
    exit()

callType = "clients"
clientInfo = getItems(xiqCall,callType)

if len(clientInfo) < 1:
    print("---->No devices read<----")
    exit()

itemInfo = deviceInfo + clientInfo

print("###################################################")
print(itemInfo)
print("###################################################")

filename = createFile(itemInfo,uuid,folderName)

copyFile(filename)





