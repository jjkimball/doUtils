#!/usr/bin/env python

"""
.. module:: doUtils.sshConn
   :platform: Unix, Windows
   :synopsis: class SshConn -- an ssh connection.

.. moduleauthor:: John Kimball <jjkimball@acm.org>

class SshConn -- an ssh connection.

Wrap it up in an object to provide a bit higher level of abstraction
than paramiko. (And a tiny subset thereof!)

See:

    * http://www.paramiko.org/
    * https://gist.github.com/mlafeldt/841944 (paramiko examples)

"""

import os
import logging
import paramiko

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
        Create an ssh connection object (including an sshClient
        connection and an sftpClient connection).

        host : string
            The other end of the connection

        user : string
            Who to log in as

        passwd : string
            Password for the user, if needed

        keyFname : string
            An ssh key file, as an alternative to the
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
        Execute a shell command on the connected host.

        cmd : string

        envDict : dictionary
             Dictionary of environment variables, if desired

        Returns: tuple
            3-tuple: stdin, stdout, and stderr for the command.
        """
        # Raises: SSHException – if the server fails to execute the command
        return self.sshClient.exec_command(cmd, environment=envDict)    # stdin, stdout, stderr

    def get(self, remoteFpath, localfPath):
        """"
        Get file at remoteFpath on the host at the other
        end of the connection, save it at localfPath locally.

        remoteFpath : string
        localFpath : string
        """
        return self.sftpClient.get(remoteFpath, localfPath)

    def put(self, localFpath, remoteFpath):
        """
        Put the file at localFpath on the local host, to the
        host at the other end of the connection, at remoteFpath.

        localFpath : string
        remoteFpath : string
        """
        return self.sftpClient.put(localFpath, remoteFpath)

    def __exit__(self, exc_type, exc_value, traceback):
        self.sftpClient.close()
        self.sshClient.close()



