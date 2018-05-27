"""
.. module:: doUtils
   :platform: Unix
   :synopsis: Configure and create a Digital Ocean virtual private server ("droplet"), execute commands on it, and transmit files to/from it.

.. moduleauthor:: John Kimball <jjkimball@acm.org>

This module consists of the classes and routines defined in:  cloudConfig, droplet, sshConn, and utils.

(Only exercised on Unix so far.)
"""

from doUtils.cloudConfig import makeUserData, waitUntilCloudInitDone
from doUtils.droplet import isUp, myDroplets, myImages, appImages, distroImages, makeDroplet, shutdownAllDroplets, destroyAllDroplets

from doUtils.sshConn import SshConn    # SshConn: do, get, put

from doUtils.utils import SshKeypair, getApiToken, getManager, ApiTokenIsMissingError
