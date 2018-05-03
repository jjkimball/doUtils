#!/usr/bin/env python

import paramiko


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




# def scp(host, user, passwd, source, dest, keyFname):
#     ## https://gist.github.com/mlafeldt/841944
#     port = 22
#     try:
#         t = paramiko.Transport((host, port))
#         t.connect(username=user, password=passwd, key_filename=keyFname)
#         sftpClient = paramiko.SFTPClient.from_transport(t)
#         sftpClient.get(source, dest)
#     finally:
#         t.close()
# 
# 
# def ssh(host, user, passwd, cmd, keyFname):
#     ## https://gist.github.com/mlafeldt/841944
#     port = 22
#     try:
#         sshClient = paramiko.SSHClient()
#         sshClient.load_system_host_keys()
#         # also AutoAddPolicy
#         sshClient.set_missing_host_key_policy(paramiko.WarningPolicy)
#         sshClient.connect(host, port=port, username=user, password=passwd, key_filename=keyFname)
#         stdin, stdout, stderr = sshClient.exec_command(cmd)
#         print(stdout.read())
#     finally:
#         sshClient.close()

        # alt
        # https://medium.com/@keagileageek/paramiko-how-to-ssh-and-file-transfers-with-python-75766179de73
        # stdin.write(‘mypassword\n’)
        # print(stdout.readlines())
        # print(stderr.readlines())
        #
        # ftp_client=ssh_client.open_sftp()
        # ftp_client.get(‘remotefileth’,’localfilepath’)
        # ftp_client.close()
        ## Downloading a file from remote machine
        # ftp_client=ssh_client.open_sftp()
        # ftp_client.get(‘remotefileth’,’localfilepath’)
        # ftp_client.close()
        ## Uploading file from local to remote machine
        # ftp_client=ssh.open_sftp()
        # ftp_client.put(‘localfilepath’,remotefilepath’)
        # ftp_client.close()
