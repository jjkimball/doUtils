#!/usr/bin/env python3

"""
.. module:: doUtils.cloudConfig
   :platform: Unix
   :synopsis: Configure a Digital Ocean droplet at startup using cloud-config and YAML.

.. moduleauthor:: John Kimball <jjkimball@acm.org>

Configure a Digital Ocean droplet at startup using cloud-config and YAML.

See:

    * https://www.digitalocean.com/community/tutorials/an-introduction-to-cloud-config-scripting
    * https://www.brightbox.com/docs/guides/cloud-init/
    * https://cloudinit.readthedocs.io/en/latest/topics/examples.html

    * http://pyyaml.org/wiki/PyYAMLDocumentation
    * https://stackoverflow.com/questions/6866600/yaml-parsing-and-python

Further cloud-config capabilities not yet scripted here:

    Add custom trusted certs. Configure
    resolv.conf's list of dns servers. Shutdown or reboot after
    specified delay. Define group.  Change password. More.

Note:

    Output of cloud config on the server gets written to standard output
    and to the /var/log/cloud-init-output.log file.

"""

import sys
import os
import time
import logging
import json
import yaml
import doUtils




###############################################################################

ModuleName = __name__ if __name__ != '__main__' else os.path.basename(__file__)
log = logging.getLogger(ModuleName)

###############################################################################
# Templates for building cloud config data structures:

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
    """Create textual cloud-config user data for initializing a VPS.

    sudoUserKeys : list of SshKeypairs (see utils.py and keypair.py)
        List of users to be created with the ability to sudo.  If list
        is empty, adds one for "adminuser".

    CustomRepos : list of string
        List of one or more custom repositories to fetch
        packages from.

    installPkgs : list of string
        List of packages to install.

    Files : List of dicts {'path': "/path/to/file", 'content':
        "contents of file"}
        List of files to be created.

    returns : string, list of SshKeypairs
        Return userData string created, and list of sudoUserKeys used.

    EG: Default with no parameters is to create sudo user adminuser and no
    custom packages installed or files created:

    >>> udata1,ukeys1 = makeUserData()
    >>> "name: adminutil" in udata1 and "ssh-authorized-keys: [ssh-rsa " in udata1
    True
    >>> type(ukeys1[0]) == doUtils.SshKeypair
    True

    EG: Create a custom file, and install two special packages, one from
    a custom repo:

    >>> Repos = ['ppa:unit193/encryption']
    >>> PkgsToInstall = ['build-essential', 'veracrypt']
    >>> Lines = "Tis but a scratch.\\nA scratch? Your arm's off!\\n"
    >>> FilesToCreate = [{'path': "/tmp/dialog.txt", 'content': Lines}]
    >>> udata2,ukeys2 = makeUserData(customRepos=Repos, installPkgs=PkgsToInstall, files=FilesToCreate)
    >>> "name: adminutil" in udata2
    True
    >>> type(ukeys2[0]) == doUtils.SshKeypair
    True
    >>> "\\nwrite_files:\\n- {content: 'Tis but a scratch.\\n" in udata2
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
    """Has cloud init finished running?

    sshConn : SshConn object (see sshConn.py)
        We need an ssh connection to the droplet (sshConn.py).

    nTries : int
        How many times to check. Number of seconds between
        checks increases each time.

    Returns : dict { 'done': bool, MORE }
        If success, 'done' is True, and MORE is
            'summaryResult': contents of /run/cloud-init/result.json
            'passesResults': contents of /run/cloud-init/status.json
        If failure, 'done' is False and MORE is
            'log': contents of /var/log/cloud-init-output.log
    """
    triesLeft = nTries
    while triesLeft:
        time.sleep((nTries-triesLeft)**2)
        triesLeft -= 1
        # How do we know if cloud init is done, and whether it succeeded?
        # https://github.com/number5/cloud-init/blob/master/doc/status.txt
        # Besides checking for nonzero (ie fail) exit status from cat,
        # could also do errLines = resErr.readlines(), and check for
        # (errLines and "No such file or directory" in errLines[0])
        _in, resOut, _err = sshConn.do('cat /run/cloud-init/result.json')
        if resOut.channel.recv_exit_status() != 0:
            log.info("Cloud init not done ({} tries left)...".format(triesLeft))
        else:
            resContents = resOut.read()
            if type(resContents) == bytes:
                resContents = resContents.decode('utf-8')
            _in, statOut, _err = sshConn.do('cat /run/cloud-init/status.json')
            statContents = statOut.read()
            if type(statContents) == bytes:
                statContents = statContents.decode('utf-8')
            return {'done': True, 'summaryResult': json.loads(resContents), 'phasesResults': json.loads(statContents)}
    _in, logOut, _err = sshConn.do('cat /var/log/cloud-init-output.log')
    logContents = logOut.readlines()
    return {'done': False, 'log': logContents}


###############################################################################


if __name__ == "__main__":   # pragma: no cover
    if len(sys.argv) > 1 and sys.argv[1].lower() == "--unittest":
        # 'THIS.py --unitTest' or 'THIS.py --unitTest -v'
        import doctest
        logging.basicConfig(level=logging.INFO)    # default to stderr. alt: filename='unittest-{}.log'.format(ModuleName)
        doctest.testmod()
        log.info("tests done")

