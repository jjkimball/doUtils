#!/usr/bin/env python3

import os
import sys
import logging
import digitalocean
from doUtils.keypair import Keypair

# Some useful utilities to support operations on a Digital Ocean
# droplet (VPS).
#
# API:
#    https://developers.digitalocean.com/documentation/v2/
#    https://developers.digitalocean.com/guides/
# python-digitalocean:
#    https://www.digitalocean.com/community/projects/python-digitalocean
#    https://github.com/koalalorenzo/python-digitalocean


###############################################################################

ModuleName = __name__ if __name__ != '__main__' else os.path.basename(__file__)
log = logging.getLogger(ModuleName)

###############################################################################



class SshKeypair(Keypair):
    """
    SshKeypair is a rsa keypair, with the derived ssh key, and the
    username that owns the key. This add some useful stuff to Keypair
    for use with Digital Ocean droplets.
    """

    def __init__(self, username):
        """
        Generate a keypair for the specified username.

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
# API token stuff.

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
    """Get the python-digitalocean manager object, so we can do
    operations.

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


if __name__ == "__main__":   # pragma: no cover
    if len(sys.argv) > 1 and sys.argv[1].lower() == "--unittest":
        # 'THIS.py --unitTest' or 'THIS.py --unitTest -v'
        import doctest
        logging.basicConfig(level=logging.INFO)    # default to stderr. alt: filename='unittest-{}.log'.format(ModuleName)
        doctest.testmod()
        log.info("tests done")
