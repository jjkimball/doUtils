#!/usr/bin/env python3

import os
import sys
import time
import socket
import logging
# import pdb
import digitalocean
import doUtils.utils
from doUtils.cloudConfig import makeUserData

# Operations on a Digital Ocean droplet (VPS).
#
# These are just a slight increase in abstraction over what's already
# in python-digitialocean. (And a small subset thereof!)
#
# API:
#    https://developers.digitalocean.com/documentation/v2/
#    https://developers.digitalocean.com/guides/
# python-digitalocean:
#    https://www.digitalocean.com/community/projects/python-digitalocean
#    https://github.com/koalalorenzo/python-digitalocean
#    https://digitalocean.readthedocs.io/en/latest/

###############################################################################

ModuleName = __name__ if __name__ != '__main__' else os.path.basename(__file__)
log = logging.getLogger(ModuleName)

###############################################################################


def isUp(ipAddr, port=22, nTries=3):
    '''Waiting until a server is up.

    port : int
        The port to try to connect to.

    nTries : int
        How many times to check. Number of seconds between checks
        increases each time.

    Returns: bool
        True if host is up before run out of nTries, else false.

    '''
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(3)
        triesLeft = nTries
        while triesLeft:
            time.sleep((nTries-triesLeft)**2)
            triesLeft -= 1
            try:
                res = sock.connect_ex((ipAddr, port))
                if res == 0:
                    return True    # port is open
                else:
                    log.info("connect to {} failed, errno={} '{}' triesLeft={}".format(ipAddr, res, os.strerror(res), triesLeft))
            except socket.timeout:
                log.info("socket timeout on connect to {} triesLeft={}".format(ipAddr, triesLeft))
    return False

###############################################################################


def myDroplets():
    """
    Get a list of existing droplets (vps's).

    Returns: list of Droplet objects (see python-digitalocean)
        List of droplets existing in this account.

    >>> droplets = myDroplets()
    >>> type(droplets) == list
    True

    """
    manager = doUtils.getManager()
    return manager.get_all_droplets()


def myImages():
    """
    Get a list of existing custom images.

    Returns: list of Image objects (see python-digitalocean)
        List of custom images in this account.

    >>> images = myImages()
    >>> type(images) == list
    True

    """
    manager = doUtils.getManager()
    return [(i.id, i.name) for i in manager.get_my_images()]


def appImages():
    """Get a list of provided "app images" (images preconfigured
    for particular apps). 

    Returns : list of tuples (id, distribution, name)
        Each tuple is three fields extracted from an Image object --
        we're interested in the image id, the Linux distro, and the
        name (indicating the app).

    >>> appImages = appImages()
    >>> type(appImages) == list and len(appImages) > 0
    True

    """
    manager = doUtils.getManager()
    return [(i.id, i.distribution, i.name) for i in manager.get_app_images()]


def distroImages():
    """
    Get a list of provided "distro images" (images preconfigured for
    particular Linux distros).

    Returns : list of tuples (id, distribution, name)
        Each tuple is three fields extracted from an Image object --
        we're interested in the image id, the Linux distro, and the
        name  (indicating the version and other particulars).

    >>> distroImages = distroImages()
    >>> type(distroImages) == list and len(distroImages) > 0
    True

    """
    manager = doUtils.getManager()
    return [(i. id, i.distribution, i.name) for i in manager.get_distro_images()]

###############################################################################


def makeDroplet(imageID, sudoUserKeys=[], userData=None):
    """Create a running droplet.

    imageID : string
        ID for the desired VPS image, eg from distroImages().

    sudoUserKeys  : list of string
        List of users to be created with the ability to
        sudo.  List of one or more SshKeypairs (see Keypair.py). If
        None provided, adds one for "adminuser".

    userData : string
        Startup user data for the VPS, eg for cloud-config.
        May be created by makeUserData (see cloudConfig.py).

    Returns : dictionary
        Dictionary has useful info about the created droplet: 'ip
        address', username (associated with ssh key), keyname (of ssh
        key), userData (used for cloud initialization),
        pemFilePathname for the local key file, 'ssh command' to ssh
        to the droplet, and droplet (Droplet object). All are strings
        except for the last.

    >>> ubuntuImages = [img for img in distroImages() if img[1] == 'Ubuntu']
    >>> id = ubuntuImages[0][0]
    >>> dropletParms = makeDroplet(id)  # doctest: +ELLIPSIS
    ...
    >>> dropletParms['username'] == 'adminutil' and dropletParms['ssh command'].startswith('ssh -i')
    True

    """

    doToken = doUtils.getApiToken()
    if not userData:
        userData, sudoUserKeys = makeUserData(sudoUserKeys=sudoUserKeys)
    keyIds = [k.doSshKey.id for k in sudoUserKeys]
    droplet = digitalocean.Droplet(token=doToken, name='dropletFromAPI02', region='sfo2', image=imageID, size_slug='512mb', backups=False, ssh_keys=keyIds, user_data=userData)

    log.info("create droplet...")
    droplet.create()

    log.info("awaiting actions...")
    actions = droplet.get_actions()
    actions[0].load()
    log.info(actions)
    actions[0].wait(10)  # ??
    log.info(actions)

    droplet.load()
    return {'ip address': droplet.ip_address,
            'username': sudoUserKeys[0].username,
            'keyname': sudoUserKeys[0].doSshKey.name,
            'userData': userData,
            'pemFilePathname': sudoUserKeys[0].pemFilePathnameAsStr,
            'ssh command': "ssh -i {} {}@{}".format(sudoUserKeys[0].doSshKey.name, sudoUserKeys[0].username, droplet.ip_address),
            'droplet': droplet}

###############################################################################


def shutdownAllDroplets():
    """
    Stop all droplets from running.

    Returns : list of strings
        List of IDs of stopped droplets

    >>> stoppees = shutdownAllDroplets()  # doctest: +ELLIPSIS
    ...
    >>> type(stoppees) == list
    True

    """
    droplets = myDroplets()
    stoppedOnes = []
    for d in droplets:
        log.info("shutdown {}...".format(d.id))
        d.shutdown()
        stoppedOnes.append(d.id)
    return stoppedOnes

###############################################################################


def destroyAllDroplets():
    """
    Unrecoverably delete all droplets.

    Returns : list of strings
        List of IDs of destroyed droplets

    >>> gone = destroyAllDroplets()  # doctest: +ELLIPSIS
    ...
    >>> type(gone) == list
    True

    """
    droplets = myDroplets()
    goneOnes = []
    for d in droplets:
        log.info("destroying {}...".format(d.id))
        d.destroy()
        goneOnes.append(d.id)
    return goneOnes




###############################################################################


if __name__ == "__main__":   # pragma: no cover
    if len(sys.argv) > 1 and sys.argv[1].lower() == "--unittest":
        # 'THIS.py --unitTest' or 'THIS.py --unitTest -v'
        import doctest
        logging.basicConfig(level=logging.INFO)    # default to stderr. alt: filename='unittest-{}.log'.format(ModuleName)
        doctest.testmod()
        log.info("tests done")

