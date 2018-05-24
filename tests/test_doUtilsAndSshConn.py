
# End-to-end exercising.
# Uses:
#    distroImages, makeDroplet, isUp, sshConn, do, put, get,
#    shutdownAllDroplets, myDroplets.

import time
import logging
import doUtils

logging.basicConfig(level=logging.INFO)


def test_doUtilsAndSshConn():

    log = logging.getLogger('test_doUtilsAndSshConn')

    log.info("get the id of an image...")
    ubuntuImages = [img for img in doUtils.distroImages() if img[1] == 'Ubuntu']
    id = ubuntuImages[0][0]

    log.info("make a droplet VPS, wait for it to come up...")
    # (Note that network issues could cause this needed first
    # step to fail.)
    dParms = doUtils.makeDroplet(id)
    isUp = doUtils.isUp(dParms['ip address'], nTries=7)
    assert isUp

    log.info("make an ssh connection to the droplet...")
    sc = doUtils.SshConn(dParms['ip address'], 'adminutil', keyFname=dParms['pemFilePathname'])

    log.info("execute a command, get its output...")
    _, o, _ = sc.do('pwd')
    pwdOut = o.readlines()
    assert pwdOut == ['/home/adminutil\n']

    log.info("put a file to the droplet...")
    with open('_test.txt', 'w') as f:
        print("testing testing", file=f)
    sc.put('_test.txt', '_test2.txt')

    log.info("check that the new file is there...")
    _, o, _ = sc.do('ls')
    lsOut = o.readlines()
    assert lsOut == ['_test2.txt\n']

    log.info("get a file from the droplet...")
    sc.get('_test2.txt', '_test2.txt')
    with open('_test2.txt', 'r') as f:
        contents = f.readlines()
    assert contents == ['testing testing\n']

    # Cleanup:
    log.info("shut the droplet down...")
    doUtils.shutdownAllDroplets()

    log.info("and destroy it...")
    dParms['droplet'].destroy()

    log.info("check that it's gone...")
    time.sleep(3)
    ds = doUtils.myDroplets()
    assert dParms['droplet'].id not in ds

    log.info("DONE")
