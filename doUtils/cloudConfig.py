#!/usr/bin/env python3

import sys
import os
import time
import logging
import json
import yaml
import doUtils

# TODO
# makeUserData should accomodate multiple sudoable users


###############################################################################

ModuleName = __name__ if __name__ != '__main__' else os.path.basename(__file__)
log = logging.getLogger(ModuleName)

###############################################################################
# cloud config user_data (YAML)
#
# https://www.digitalocean.com/community/tutorials/an-introduction-to-cloud-config-scripting
# https://www.brightbox.com/docs/guides/cloud-init/
# https://cloudinit.readthedocs.io/en/latest/topics/examples.html
#
# http://pyyaml.org/wiki/PyYAMLDocumentation
# https://stackoverflow.com/questions/6866600/yaml-parsing-and-python
# pipenv install PyYAML
#
# also can:  add custom trusted certs. configure resolv.conf's list of
# dns servers. shutdown or reboot after specified delay. define group.
# change password. more.

# output will be written to standard out and to
# the /var/log/cloud-init-output.log file

CloudConfigHdr = "#cloud-config\n"

# Define a non-root sudo user who uses an ssh key.
# Each ssh-authorized key should look like:
# 'ssh-rsa AAAAB3NzLALALA user@example.com'
SudoUserListCCTpl = {'users': []}    # each user is one of these:
SudoUserCCTpl = {'name': None,
                 'groups': 'sudo',
                 'shell': '/bin/bash',
                 'sudo': ['ALL=(ALL) NOPASSWD:ALL'],
                 'ssh-authorized-keys': []}
# Update info on packages:
UpdatePkgInfoCCTpl = {'package_update': True}
# Force an "apt upgrade" to upgrade all.
UpgradeAllCCTpl = {'package_upgrade': True}
# Add one or more custom repositories.
# Each source in the list looks like {'source': 'ppa:example/random-ng'}
# is a quoted string.
AddCustomReposCCTpl = {'apt_sources': []}
# Packages to install.
# each package in the list is either 'package_1' or
# ['package_3', 'version_num']
InstallPackagesCCTpl = {'packages': []}
# Run arbitrary commands.
# Each command in the list either looks like 'touch /tmp/test.txt'
# or [ sed, -i, -e, 's/here/there/g', some_file]
RunCmdsCCTpl = {'runcmd': []}

# Create files.
# For multi-line content, start a block by using '|' on the
# content line, and indent the content.  For binary content,
# use "!!binary |" on the content line.
# (The pipe character indicates the block should be read as-is,
# with formatting maintained.)
# EG:
# write_files:
#   - path: /test.txt
#     content: |
#       Here is a line.
#       Another line is here.
WriteFileCCTpl = {
    'write_files': [
        # {'path': None,
        # 'content': None}
    ]
}

###############################################################################


def makeUserData(sudoUserKeys=[], customRepos=None, installPkgs=None, files=None):
    """
    Create textual cloud-config user data for initializing a VPS.
    >>> udata,ukeys = makeUserData()
    >>> "name: adminutil" in udata and "ssh-authorized-keys: [ssh-rsa " in udata
    True
    >>> type(ukeys[0]) == doUtils.SshKeypair
    True
    """
    ccParms = {}
    if not sudoUserKeys:
        sudoUserKeys.append(doUtils.SshKeypair(username='adminutil'))
    sudoUserListCC = dict(SudoUserListCCTpl)
    for k in sudoUserKeys:
        sudoUserListCC['users'].append(dict(SudoUserCCTpl))
        sudoUserListCC['users'][-1]['name'] = k.username
        sudoUserListCC['users'][-1]['ssh-authorized-keys'].append(k.doSshKey.public_key)
    ccParms.update(sudoUserListCC)
    if customRepos or installPkgs:
        ccParms.update(UpdatePkgInfoCCTpl)
    if customRepos:
        customReposCC = [{'source': r} for r in customRepos]
        addCustomReposCC = dict(AddCustomReposCCTpl)
        addCustomReposCC['apt_sources'] = customReposCC
        ccParms.update(addCustomReposCC)
    if installPkgs:
        installPackagesCC = dict(InstallPackagesCCTpl)
        installPackagesCC['packages'] = installPkgs
        ccParms.update(installPackagesCC)
    if files:
        writeFileCC = dict(WriteFileCCTpl)
        writeFileCC['write_files'] = files
        ccParms.update(writeFileCC)
    userData = CloudConfigHdr + yaml.dump(ccParms)
    return userData, sudoUserKeys

###############################################################################


def waitUntilCloudInitDone(sshConn, nTries=10):
    """
    Has cloud init finished running?
    """
    triesLeft = nTries
    while triesLeft:
        time.sleep((nTries-triesLeft)**2)
        triesLeft -= 1
        # https://github.com/number5/cloud-init/blob/master/doc/status.txt
        # Besides nonzero (ie fail) exit status from cat, could also do
        # errLines = resErr.readlines(), and check for
        # (errLines and "No such file or directory" in errLines[0])
        _in, resOut, _err = sshConn.do('cat /run/cloud-init/result.json')
        if resOut.channel.recv_exit_status() != 0:
            log.info("Cloud init not done ({} tries left)...".format(triesLeft))
        else:
            resContents = resOut.read()
            _in, statOut, _err = sshConn.do('cat /run/cloud-init/status.json')
            statContents = statOut.read()
            return {'done': True, 'summaryResult': json.loads(resContents), 'phasesResults': json.loads(statContents)}
    _in, logOut, _err = sshConn.do('cat /var/log/cloud-init-output.log')
    logContents = logOut.readlines()
    return {'done': False, 'log': logContents}


###############################################################################


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].lower() == "--unittest":
        # 'THIS.py --unitTest' or 'THIS.py --unitTest -v'
        import doctest
        doctest.testmod()
        log.info("tests done")

