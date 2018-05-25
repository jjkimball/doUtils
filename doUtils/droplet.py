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

# TODO
#
# do('curl http://169.254.169.254/latest/user-data')
# do('curl http://169.254.169.254/latest/meta-data')
#
# this now looks to be working:
# makeDroplet(imageID, customRepos=['ppa:jonathonf/ffmpeg-3'], installPkgs=['ffmpeg', 'libav-tools', 'x264', 'x265'])
# do('cat /var/log/cloud-init-output.log')
#
# block ssh to root not done?
# other sec stuff

# API: https://developers.digitalocean.com/documentation/v2/
#      https://developers.digitalocean.com/guides/
# python-digitalocean: https://www.digitalocean.com/community/projects/python-digitalocean
#                      https://github.com/koalalorenzo/python-digitalocean

###############################################################################

ModuleName = __name__ if __name__ != '__main__' else os.path.basename(__file__)
log = logging.getLogger(ModuleName)

###############################################################################


def isUp(ipAddr, port=22, nTries=3):
    '''
    Utility routine for scripting.  Waiting until a server is up.
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
    >>> droplets = myDroplets()
    >>> type(droplets) == list
    True
    """
    manager = doUtils.getManager()
    return manager.get_all_droplets()


def myImages():
    """
    Get a list of existing custom images.
    >>> images = myImages()
    >>> type(images) == list
    True
    """
    manager = doUtils.getManager()
    return [(i.id, i.name) for i in manager.get_my_images()]


def appImages():
    """
    Get a list of provided "app images" (images preconfigured
    for particular apps). We're interested in the id, the
    Linux distro, and the name (indicating the app).
    >>> appImages = appImages()
    >>> type(appImages) == list and len(appImages) > 0
    True
    """
    manager = doUtils.getManager()
    return [(i. id, i.distribution, i.name) for i in manager.get_app_images()]


def distroImages():
    """
    Get a list of provided "distro images" (images preconfigured for
    particular Linux distros). We're interested in the id, the distro,
    and the name (indicating the version and other particulars).
    >>> distroImages = distroImages()
    >>> type(distroImages) == list and len(distroImages) > 0
    True
    """
    manager = doUtils.getManager()
    return [(i. id, i.distribution, i.name) for i in manager.get_distro_images()]

###############################################################################


def makeDroplet(imageID, sudoUserKeys=[], userData=None):
    """
    Create a running droplet.
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


###############################################################################


if __name__ == "__main__":   # pragma: no cover
    if len(sys.argv) > 1 and sys.argv[1].lower() == "--unittest":
        # 'THIS.py --unitTest' or 'THIS.py --unitTest -v'
        import doctest
        logging.basicConfig(level=logging.INFO)    # default to stderr. alt: filename='unittest-{}.log'.format(ModuleName)
        doctest.testmod()
        log.info("tests done")

