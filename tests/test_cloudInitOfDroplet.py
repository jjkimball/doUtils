# Exercise cloud init of droplet
# Uses:
#    from doUtils: distroImages makeUserData makeDroplet isUp
#    SshConn waitUntilCloudInitDone AllDroplets myDroplets

import time
import logging
import doUtils

logging.basicConfig(level=logging.INFO)


def test_cloudInitOfDroplet():

    log = logging.getLogger('test_cloudInitOfDroplet')

    log.info("We'll need the id of an image...")
    ubuntu16Images = [img for img in doUtils.distroImages() if img[1] == 'Ubuntu' and img[2].startswith('16.04')]
    iId = ubuntu16Images[0][0]

    log.info("Make user data specifying a custom repository and a package to install from it...")
    uData, uKeys = doUtils.makeUserData(customRepos=['ppa:kelleyk/emacs'], installPkgs=['emacs25'])

    log.info("Make the droplet VPS...")
    dParms = doUtils.makeDroplet(iId, sudoUserKeys=uKeys, userData=uData)
    isUp = doUtils.isUp(dParms['ip address'], nTries=7)
    assert isUp

    log.info("Now we need to wait until cloud init has completed...")
    time.sleep(15)

    log.info("Make an ssh connection to the droplet, for checking...")
    sConn = doUtils.SshConn(dParms['ip address'], 'adminutil', keyFname=dParms['pemFilePathname'])

    log.info("Wait until cloud init is done (hopefully)...")
    isDone = doUtils.waitUntilCloudInitDone(sConn)
    assert isDone['done']

    log.info("See if emacs25 got installed...")
    _, whOut, _ = sConn.do('which emacs25')
    whOutLines = whOut.readlines()
    assert whOutLines and '/usr/bin/emacs25' in whOutLines[0]

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
