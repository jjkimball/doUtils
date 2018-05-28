
doUtils Overview
================

doUtils provides a Python module to configure and create a Digital
Ocean virtual private server ("droplet"), execute commands on it, and
transmit files to/from it.


Motivation
**********

I want to run a compute-intensive script on erratic occasions, and I
don't want it to be contending for my laptop's processing power while
I'm trying to do other stuff.

Idea: A script that provisions a temporary virtual server with the
needed packages installed, and, via script, executes the
compute-intensive job and snarf the results.


Secondary goals
###############

* Learn more about python-digitalocean, paramiko for ssh, and
  cloud-init via pyyaml.

* Don't require the big guns:  the automated provisioning /
  infrastructure configuration management tools (ansible, chef,
  puppet, et al).


Installation
************

doUtils is a set of personal tools and a learning exercise. It's
not (yet?) set up as a simple-to-install module.

You can copy the doUtils folder somewhere on your system, and put that
containing folder on your PYTHONPATH environment variable. 
The prerequisite packages are in requirements.txt.

Note that you'll need a Digital Ocean API key -- see https://www.digitalocean.com/help/api/.

To generate the docs, do::

  cd ./docs
  make bootstrap-api
  make html

To run the tests and get a coverage report, do::

    pytest -s --doctest-modules --cov=doUtils
    coverage html

And then look at ./htmlcov/index.html.


Usage
*****

Here are some examples.

Import the package::

    import doUtils

Select an image to use for initializing a droplet::    

    ubuntuImages = [img for img in doUtils.distroImages() if img[1] == 'Ubuntu']
    id = ubuntuImages[0][0]

Create a droplet with that image, using the defaults for username,
etc; and wait until it's provisioned and responding::

    dParms = doUtils.makeDroplet(id)
    isUp = doUtils.isUp(dParms['ip address'], nTries=7)

Create a droplet; at initialization install some nonstandard
packages, and also create a file::

    Repos = ['ppa:kelleyk/emacs', 'ppa:unit193/encryption']
    Pkgs = ['emacs25', 'build-essential', 'keepassx', 'veracrypt']
    Fname = '/tmp/membership.txt'
    FContents = "Graham Chapman\nJohn Cleese\nTerry Gilliam\nEric Idle\nTerry Jones\nMichael Palin\n"
    Files = [{'path': Fname, 'content': FContents}]
    uData, uKeys = doUtils.makeUserData(customRepos=Repos, installPkgs=Pkgs, files=Files)
    dParms = doUtils.makeDroplet(iId, sudoUserKeys=uKeys, userData=uData)
  
Create an ssh connection to a droplet::

    sc = doUtils.SshConn(dParms['ip address'], 'adminutil', keyFname=dParms['pemFilePathname'])

Wait until cloud-init is done (nonstandard packages installed, etc)::

    isDone = doUtils.waitUntilCloudInitDone(sConn)
    assert isDone['done']
    log.info("summary result: {}".format(isDone['summaryResult']))    

Execute a command on the droplet and print its output::

    shIn, shOut, shErr = sc.do('pwd')
    print(shOut.readlines())

Put a file to the droplet::    

    sc.put('test.txt', 'test-on-droplet.txt')

Retrieve that file again::    

    sc.get('test-on-droplet.txt', 'test-fetched.txt')

See what droplets exist::

    ds = doUtils.myDroplets()

Shutdown all droplets::    

    doUtils.shutdownAllDroplets()

Destroy the droplet::    

    dParms['droplet'].destroy()




History
*******

* Version 0.1, June 2018. Pre-release.


License
*******

MIT (See LICENSE).



