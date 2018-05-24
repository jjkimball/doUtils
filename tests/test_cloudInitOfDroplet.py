# Exercise cloud init of droplet
# Uses:
#    from doUtils: distroImages makeUserData makeDroplet isUp
#    SshConn waitUntilCloudInitDone AllDroplets myDroplets

import time
import logging
import doUtils

logging.basicConfig(level=logging.INFO)

ListOfPackages = """Custom packages installed:
  - emacs35
    - ppa:kelleyk/emacs
  - build-essential
  - keepassx
  - veracrypt
    - ppa:unit193/encryption
"""
Repos = ['ppa:kelleyk/emacs', 'ppa:unit193/encryption']
Pkgs = ['emacs25', 'build-essential', 'keepassx', 'veracrypt']
Fname = '/tmp/ListOfPackages'
Files = [{'path': Fname, 'content': ListOfPackages}]


def test_cloudInitOfDroplet():

    log = logging.getLogger('test_cloudInitOfDroplet')

    log.info("We'll need the id of an image...")
    ubuntu16Images = [img for img in doUtils.distroImages() if img[1] == 'Ubuntu' and img[2].startswith('16.04')]
    iId = ubuntu16Images[0][0]

    log.info("Make user data specifying custom repositories,  packages to install, and a file to create...")
    uData, uKeys = doUtils.makeUserData(customRepos=Repos, installPkgs=Pkgs, files=Files)

    log.info("Make the droplet VPS...")
    dParms = doUtils.makeDroplet(iId, sudoUserKeys=uKeys, userData=uData)
    isUp = doUtils.isUp(dParms['ip address'], nTries=7)
    assert isUp
    log.info("ssh cmd: {}".format(dParms['ssh command']))

    log.info("Now we need to wait until cloud init has completed...")
    time.sleep(15)

    log.info("Make an ssh connection to the droplet, for checking...")
    sConn = doUtils.SshConn(dParms['ip address'], 'adminutil', keyFname=dParms['pemFilePathname'])

    log.info("Wait until cloud init is done (hopefully)...")
    isDone = doUtils.waitUntilCloudInitDone(sConn)
    assert isDone['done']
    log.info("summary result: {}".format(isDone['summaryResult']))

    _, catOut, _ = sConn.do('cat ' + Fname)
    contents = catOut.read()
    assert contents.decode("utf-8") == ListOfPackages

    log.info("See if emacs25 got installed...")
    _, whOut, _ = sConn.do('which emacs25')
    whOutLines = whOut.readlines()
    assert whOutLines and '/usr/bin/emacs25' in whOutLines[0]

    log.info("See if build-essential got installed...")
    _, whOut, _ = sConn.do('which ld')
    whOutLines = whOut.readlines()
    assert whOutLines and '/usr/bin/ld' in whOutLines[0]

    log.info("See if keepassx got installed...")
    _, whOut, _ = sConn.do('which keepassx')
    whOutLines = whOut.readlines()
    assert whOutLines and '/usr/bin/keepassx' in whOutLines[0]

    log.info("See if veracrypt got installed...")
    _, whOut, _ = sConn.do('which veracrypt')
    whOutLines = whOut.readlines()
    assert whOutLines and '/usr/bin/veracrypt' in whOutLines[0]

    # Cleanup:
    log.info("Shut the droplet down...")
    doUtils.shutdownAllDroplets()

    log.info("And destroy it...")
    dParms['droplet'].destroy()

    log.info("Check that it's gone...")
    time.sleep(3)
    ds = doUtils.myDroplets()
    assert dParms['droplet'].id not in ds

    log.info("DONE")
