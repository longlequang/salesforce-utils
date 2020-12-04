# coding: utf-8
import sys
import os
from io import BytesIO
from datetime import datetime
from traceback import print_exc
from smb.SMBConnection import SMBConnection
import shutil

class SmbClient:
    def __init__(self, conf):
        # set configuration
        self.__username = conf["username"]
        self.__password = conf["password"]
        self.__domain = conf["domain"]
        self.__remote_host = conf["remote_host"]
        self.__remote_port = conf["remote_port"]
        # resolve host name
        import socket
        self.__remote_addr = socket.gethostbyname(conf["remote_host"])
        self.__client = socket.gethostname()

    @staticmethod
    def sample_conf():
        return {"username": os.getlogin(),
                "password": "P@ssw0rd",
                "domain": "WORKGROUP",
                "remote_host": "remotehost.local",
                "remote_port": 445}

    def list_shares(self):
        session = self.__get_connection()
        shares = session.listShares()
        for share in shares:
            if not share.isSpecial and share.name in ['ROOT_DIR_FILE_SERVER']:
                sharedfiles = session.listPath(
                    share.name, 'A_SHARED_OR_PUBLIC_PATH_ON_FILE_SERVER')
                for sharedfile in sharedfiles:
                    print(sharedfile.filename)

        session.close()

    def download(self, service_name, remote_path, local_filename,buffersize=None, callback=None, local_path=None):
        session = self.__get_connection()

        try:
            #attr = session.getAttributes(service_name, remote_path)
            file_obj = BytesIO()
            dirname = os.path.dirname(local_path)
            saveFilePath =  os.path.join(local_path,local_filename)
            if local_path:
                fw = open(saveFilePath, 'wb')
            else:
                fw = open(saveFilePath, 'wb')
            offset = 0
            transmit = 0
            while True:
                if not buffersize:
                    file_attributes, filesize = session.retrieveFile(
                        service_name, remote_path, file_obj)
                else:
                    file_attributes, filesize = session.retrieveFileFromOffset(
                        service_name, remote_path, file_obj, offset=offset, max_length=buffersize)
                    if callback:
                        transmit = transmit + filesize
                        callback(transmit)
                file_obj.seek(offset)
                for line in file_obj:
                    fw.write(line)
                offset = offset + filesize
                if (not buffersize) or (filesize == 0):
                    break
            fw.close()

        except Exception as e:
            print('Error on line {}'.format(
                sys.exc_info()[-1].tb_lineno), type(e).__name__, e)

    def list_dir(self, svc_name, path_, recurse=False):
        try:
            self.__list = []
            session = self.__get_connection()
            # return object list if the path is existing remote directory
            if self.__check_dir(session, svc_name, path_):
                self.__get_files(session, svc_name, path_, recurse, True)

            session.close()
            return self.__list

        except:
            print_exc()
            session.close()
            return []

    def receive_items(self, local_dir, svc_name, path_, recurse=False, relative=True):
        # check if local path is valid
        if not os.path.isdir(local_dir):
            print("local directory is not available ({})".format(local_dir))
            return False

        try:
            self.__list = []
            session = self.__get_connection()
            # switch for the path is directory or file
            if self.__check_dir(session, svc_name, path_):
                remote_dir = path_ * relative
                self.__get_files(session, svc_name, path_, recurse)
            else:
                remote_dir = os.path.dirname(path_)
                self.__list = [{"path": path_}]
            # batch download
            for index, item in enumerate([x["path"] for x in self.__list]):
                print("\t[{}/{}] retrieving {}...".format(index + 1, len(self.__list),
                                                          os.path.basename(item)))
                self.__download(local_dir, session, svc_name, item, remote_dir)

            session.close()
            return True

        except:
            print_exc()
            session.close()
            return False

    def send_file(self, local_file, svc_name, remote_dir):
        # check if local path is valid
        if not os.path.isfile(local_file):
            print("invalid path: {}".format(local_file))
            return False

        try:
            session = self.__get_connection()
            if self.__check_dir(session, svc_name, remote_dir):
                print("sending file...")
                with open(local_file, 'rb') as f:
                    # store file to remote path
                    path_ = os.path.join(
                        remote_dir, os.path.basename(local_file))
                    session.storeFile(svc_name, path_, f)
            else:
                print("invalid remote path: {} - {}".format(svc_name, path_))
            session.close()
            return True

        except:
            print_exc()
            session.close()
            return False

    def __check_dir(self, connection, service_name, remote_path):
        return connection.getAttributes(service_name, remote_path).isDirectory

    def __get_connection(self):
        # build connection
        # connection = SMBConnection(username=self.__username, password=self.__password,
        #                            my_name=self.__client, remote_name=self.__remote_host,
        #                            domain=self.__domain)
        connection = SMBConnection(username=self.__username, password=self.__password,
                                    my_name=self.__client, remote_name=self.__remote_host, 
                                    domain=self.__domain, use_ntlm_v2=True, is_direct_tcp=True)
        # open connection
        connection.connect(self.__remote_addr, self.__remote_port)
        return connection

    def __get_files(self, connection, service_name, base_dir, recursive=True, include_dir=False):
        # sub funciton for formatting data
        # see https://msdn.microsoft.com/en-us/library/ee878573.aspx
        def _convert_obj(sf, base_dir):
            return {"path": os.path.join(base_dir, sf.filename),
                    "filename": sf.filename, "isDirectory": sf.isDirectory,
                    "last_write_time": "{:%Y-%m-%d, %H:%M:%S}".format(datetime.fromtimestamp(sf.last_write_time)),
                    "file_size": "{:,.1f} [KB]".format(sf.file_size / 1024),
                    "file_attributes": "0x{:08x}".format(sf.file_attributes)}
        # iterate paths
        for item in connection.listPath(service_name, base_dir):
            # skip aliases
            if item.filename == "." or item.filename == "..":
                continue

            if item.isDirectory:
                if include_dir:
                    self.__list.append(_convert_obj(item, base_dir))
                if recursive:
                    # call recursively for sub directory
                    self.__get_files(connection, service_name,
                                     os.path.join(base_dir, item.filename),
                                     recursive, include_dir)
            else:
                self.__list.append(_convert_obj(item, base_dir))

    def __download(self, local_base_dir, connection, service_name, remote_path, remote_base_dir=""):
        # calculate local path and create parent directory if not exist
        local_path = os.path.join(
            local_base_dir, os.path.relpath(remote_path, remote_base_dir))
        if not os.path.isdir(os.path.dirname(local_path)):
            os.makedirs(os.path.dirname(local_path))
        # download file from remote host
        with open(local_path, 'wb') as f:
            connection.retrieveFile(service_name, remote_path, f)
