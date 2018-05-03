#!/usr/bin/env python3

import os
import sys
import digitalocean
from doUtils.keypair import Keypair

# API: https://developers.digitalocean.com/documentation/v2/
#      https://developers.digitalocean.com/guides/
# python-digitalocean: https://www.digitalocean.com/community/projects/python-digitalocean
#                      https://github.com/koalalorenzo/python-digitalocean

###############################################################################


class SshKeypair(Keypair):
    """
    SshKeypair is a rsa keypair, with the derived ssh key, and the username that owns the key.
    """

    def __init__(self, username):
        """
        >>> key = SshKeypair('Bob')
        >>> key.username == 'Bob' and type(key.pemFilePathnameAsStr) == str and type(key.doSshKey) == digitalocean.SSHKey
        True
        """
        super(SshKeypair, self).__init__()
        self.writeToDisk(passPhrase="")
        publicKey = self.publicKeyOpensshAsBytes.decode('utf-8')
        self.username = username
        self.doSshKey = digitalocean.SSHKey()
        self.doSshKey.token = getApiToken()
        self.doSshKey.public_key = publicKey
        self.doSshKey.name = os.path.basename(self.pemFilePathnameAsStr)
        self.doSshKey.create()

###############################################################################
# The environment variable DOTOKEN needs to be set to the user's
# Digital Ocean API token:


class ApiTokenIsMissingError(Exception):
    message = "No Digital Ocean API access token in environment"


def getApiToken():
    """
    Fetch the user's Digital Ocean API key from the environment.
    >>> doToken = getApiToken()
    >>> type(doToken) == str and len(doToken) == 64
    True
    """
    try:
        return getApiToken.apiKey
    except AttributeError:
        try:
            getApiToken.apiKey = os.environ["DigitalOceanApiKey"]
            return getApiToken.apiKey
        except KeyError:
            raise ApiTokenIsMissingError

###############################################################################        


def getManager():
    """
    Get the manager object.
    >>> manager = getManager()
    >>> type(manager) == digitalocean.Manager
    True
    """
    try:
        return getManager.manager
    except AttributeError:
        doToken = getApiToken()
        getManager.manager = digitalocean.Manager(token=doToken)
        return getManager.manager

###############################################################################


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].lower() == "--unittest":
        # 'THIS.py --unitTest' or 'THIS.py --unitTest -v'
        import doctest
        doctest.testmod()
        print("//tests done", file=sys.stderr)

