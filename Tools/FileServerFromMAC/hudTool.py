# -*- coding: utf-8 -*-
import csv
import os, errno
import getpass
from SMBClient import SmbClient
# get default config
conf = SmbClient.sample_conf()
# ドメイン環境でSMB2
conf = {"username": "YOUR_NAME_INLOCAL_NETWORK",
        "password": "PSW_INLOCAL_NETWORK",
        "domain": "open.local",
        "remote_host": "FILE_SERVER_IP",
        "remote_port": 445}


# path to UNC '\\{remotehost}\{svc_name}\{remote_path}'
svc_name = "情報システム部"
remote_path = "非公開用"

smb_client = SmbClient(conf)
# print list of files at the root of the share 
#smb_client.list_shares()

BASE_URL='A_SHARED_OR_PUBLIC_PATH_ON_FILE_SERVER'
OUTPUT_DIR = 'OUTPUT'
# smb_client = SMBClient(ip='FILE_SERVER_IP', username='YOUR_NAME_INLOCAL_NETWORK', password='PSW_INLOCAL_NETWORK', servername=BASE_URL)
# smb_client._connect()

def makeOutputDir():
    try:
        os.makedirs(OUTPUT_DIR)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

def makePropertyDir(name):
    isFolder = os.path.isdir(OUTPUT_DIR + '/' + name) 
    if isFolder:
        print('***********EXIST**********')
        return OUTPUT_DIR + '/' + name
    else:
        print("***********NOT EXIST**********")
        try:
            os.makedirs(OUTPUT_DIR + '/' + name)
            return OUTPUT_DIR + '/' + name
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

def copyFile(fromFile,toFile):
    print('COPY FILE')
    shutil.copy2(fromFile, toFile)

makeOutputDir()
#makePropertyDir()


with open('hud.csv') as f:
    f_csv = csv.reader(f) 
    headers = next(f_csv) 
    for row in f_csv:
        filePath = row[12]
        fileName = row[13]
        propertyAddress = row[28]
        downloadPath = BASE_URL + filePath
        savePath=makePropertyDir(propertyAddress)
        print("PATH:"+filePath)
        print("NAME:"+fileName)
        print("DOWNLOAD:"+downloadPath)
        print("LOCAL PATH: " + savePath)
        # download files
        res = smb_client.download(service_name = svc_name,local_path = savePath ,local_filename=fileName, remote_path=downloadPath)
        if (res != None):
            print(res)
        else: 
            print("DOWNLOAD : " + downloadPath)
    print("===============FINISH DOWNLOAD===============")


