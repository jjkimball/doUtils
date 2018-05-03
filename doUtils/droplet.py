#!/usr/bin/env python3

import os
import sys
import time
import socket
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


def isUp(ipAddr, port=22, nTries=3):
    '''
    Utility routine for scripting.  Waiting until a server is up.
    '''
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(3)
        triesLeft = nTries
        while triesLeft:
            time.sleep(nTries+1-triesLeft)
            triesLeft -= 1
            try:
                res = sock.connect_ex((ipAddr, port))
                if res == 0:
                    return True    # port is open
                else:
                    print("//connect to {} failed, errno={} '{}' triesLeft={}".format(ipAddr, res, os.strerror(res), triesLeft), file=sys.stderr)
            except socket.timeout:
                print("//socket timeout on connect to {} triesLeft={}".format(ipAddr, triesLeft), file=sys.stderr)
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

    print("//create droplet...", file=sys.stderr)
    droplet.create()

    print("//awaiting actions...", file=sys.stderr)
    actions = droplet.get_actions()
    actions[0].load()
    print(actions, file=sys.stderr)
    actions[0].wait(10)  # ??
    print(actions, file=sys.stderr)

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
        print("//shutdown", d.id, "...", file=sys.stderr)
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
        print("//destroying", d.id, "...", file=sys.stderr)
        d.destroy()
        goneOnes.append(d.id)
    return goneOnes

###############################################################################


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].lower() == "--unittest":
        # 'THIS.py --unitTest' or 'THIS.py --unitTest -v'
        import doctest
        doctest.testmod()
        print("//tests done", file=sys.stderr)


# - add non-root user w/ sudo
# then rm ssh priv fr/ root: chk /etc/ssh/sshd_config: PermitRootLogin change yes to no ; chk AllowUsers to permit new user ; service ssh restart

# possibles, things to check:
# ? sudo apt-get update && sudo apt-get upgrade
# ?? sudo apt-get install curl
# // sudo ufw status ; sudo ufw app list
# /etc/php/7.0/fpm/php.ini -- set commented-out cgi.fix_pathinfo
#  line to: cgi.fix_pathinfo=0
#  then do: sudo systemctl restart php7.0-fpm
# ? chk /etc/nginx/sites-available/default per
#   https://www.digitalocean.com/community/tutorials/how-to-install-linux-nginx-mysql-php-lemp-stack-in-ubuntu-16-04
# ? dns and mx?
# ? ssl-cert?
# ? password control to sections of nginx server?

# dbox:
# cd ~ ; curl -Lo dropbox-linux-x86_64.tar.gz https://www.dropbox.com/download?plat=lnx.x86_64
# sudo mkdir -p /opt/dropbox ; sudo tar xzfv dropbox-linux-x86_64.tar.gz --strip 1 -C /opt/dropbox
# interactive:  /opt/dropbox/dropboxd ; provides url must visit (in desktop) to link
# ^C to quit server temply
# can install as daemon "set up service script" https://www.digitalocean.com/community/tutorials/how-to-install-dropbox-client-as-a-service-on-ubuntu-14-04
# cli:
# cd ~ ; curl -LO https://www.dropbox.com/download?dl=packages/dropbox.py
# chmod +x ~/dropbox.py ; ln -s /opt/dropbox ~/.dropbox-dist

# vnc:
# sudo apt install xfce4 xfce4-goodies tightvncserver
# interactive: vncserver   to enter and verify a passwd and a view-only passwd
#  (eg f/ demos)
# config vnc server:  vncserver -kill :1 ; cp -p ~/.vnc/xstartup ~/.vnc/xstartup.ORIG ;
# ~/.vnc/xstartup :
#  #!/bin/bash
#  xrdb $HOME/.Xresources
#  startxfce4 &
# sudo chmod +x ~/.vnc/xstartup ; vncserver
# https://www.digitalocean.com/community/tutorials/how-to-install-and-configure-vnc-on-ubuntu-16-04
# for testing, for making a service

#  - possible to (using normal keypair) launch a remote-use droplet?
#    - what needed
#      - dropbox
#      - vnc?


##droplet.shutdown()
