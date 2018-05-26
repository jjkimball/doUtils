#!/usr/bin/env python

import os
import logging
import paramiko

###############################################################################
# class SshConn -- an ssh connection.
#
# Wrap it up in an object to provide a bit higher level of abstraction
# than paramiko.
#
#     http://www.paramiko.org/
#     https://gist.github.com/mlafeldt/841944 (paramiko examples)


###############################################################################

ModuleName = __name__ if __name__ != '__main__' else os.path.basename(__file__)
log = logging.getLogger(ModuleName)

###############################################################################


class SshConn:
    """
    An ssh connection to a host.

    Operations:
        do -- execute a command
        get -- fetch a file from the host
        put -- send a file to the host
    """

    def __init__(self, host, user, passwd=None, keyFname=None):
        """"
        Create an ssh connection object.
        
        host -- the other end of the connection

        user -- who to log in as

        passwd -- password for the user, if needed

        keyFname -- an ssh key file, as an alternative to the
            password.

        """
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
        """"
        Execute a shell command on the connected host, return
        stdin, stdout, and stderr for the command.

        envDict -- Dictionary of environment variables, if desired
        """
        # Raises: SSHException – if the server fails to execute the command
        return self.sshClient.exec_command(cmd, environment=envDict)    # stdin, stdout, stderr

    def get(self, remoteFpath, localfPath):
        """"
        Get file at remoteFpath on the host at the other
        end of the connection, save it at localfPath locally.
        """
        return self.sftpClient.get(remoteFpath, localfPath)

    def put(self, localFpath, remoteFpath):
        """
        Put the file at localFpath on the local host, to the
        host at the other end of the connection, at remoteFpath.
        """
        return self.sftpClient.put(localFpath, remoteFpath)

    def __exit__(self, exc_type, exc_value, traceback):
        self.sftpClient.close()
        self.sshClient.close()



