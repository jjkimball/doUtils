#!/usr/bin/env python

import os
import logging
import paramiko

###############################################################################

ModuleName = __name__ if __name__ != '__main__' else os.path.basename(__file__)
log = logging.getLogger(ModuleName)

###############################################################################


class SshConn:
    """
    - https://gist.github.com/mlafeldt/841944
    - https://gist.github.com/mlafeldt/841944
    - https://stackoverflow.com/questions/865115/how-do-i-correctly-clean-up-a-python-object
    """

    def __init__(self, host, user, passwd=None, keyFname=None):
        port = 22
        self.sshClient = paramiko.SSHClient()
        self.sshClient.load_system_host_keys()
        self.sshClient.set_missing_host_key_policy(paramiko.WarningPolicy)
        # connect() --
        # Raises: BadHostKeyException – if the server’s host key could not be verified
        # Raises: AuthenticationException – if authentication failed
        # Raises: SSHException – if there was any other error connecting or establishing an SSH session
        # Raises: socket.error – if a socket error occurred while connecting        
        self.sshClient.connect(host, port=port, username=user, password=passwd, key_filename=keyFname)
        self.sftpClient = self.sshClient.open_sftp()

    def __enter__(self):
        return self

    def do(self, cmd, envDict=None):
        # Raises: SSHException – if the server fails to execute the command
        return self.sshClient.exec_command(cmd, environment=envDict)    # stdin, stdout, stderr

    def get(self, remoteFpath, localfPath):
        return self.sftpClient.get(remoteFpath, localfPath)

    def put(self, localFpath, remoteFpath):
        return self.sftpClient.put(localFpath, remoteFpath)

    def __exit__(self, exc_type, exc_value, traceback):
        self.sftpClient.close()
        self.sshClient.close()




