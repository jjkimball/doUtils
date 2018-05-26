#!/usr/bin/env python3

import os
import sys
import logging
import datetime
import re
import random


###############################################################################
# class Keypair, to make an RSA keypair, eg for ssh. (See also class
# SshKeypair in utils.py.)
#
# https://cryptography.io/en/latest/x509/tutorial/


import cryptography
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

###############################################################################

ModuleName = __name__ if __name__ != '__main__' else os.path.basename(__file__)
log = logging.getLogger(ModuleName)

###############################################################################


class Keypair():
    """
    Generate an RSA keypair.

    >>> kp = Keypair()
    >>> kp.name.endswith(".pem")
    True
    >>> type(kp.key) == cryptography.hazmat.backends.openssl.rsa._RSAPrivateKey
    True
    >>> kp.writeToDisk()
    >>> kp.pemFilePathnameAsStr.endswith(".pem")
    True

    """

    def __init__(self):
        timestamp = "{:%Y%m%d_%H%M.%f}".format(datetime.datetime.now())
        self.name = "key" + timestamp + ".pem"
        # generate rsa key:
        self.key = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())
        # get handy serialized versions too.
        # public key in OpenSSH format:
        self.publicKeyOpensshAsBytes = self.key.public_key().public_bytes(serialization.Encoding.OpenSSH, serialization.PublicFormat.OpenSSH)
        # private key in PEM container format (with no passphrase):
        self.privateKeyPemAsBytes = self.key.private_bytes(encoding=serialization.Encoding.PEM, format=serialization.PrivateFormat.TraditionalOpenSSL, encryption_algorithm=serialization.NoEncryption())
        # Can decode AsBytes to AsStr (to printable string) via .decode('utf-8')

    def genPassphrase(self):
        """
        Make a passphrase, if none is specified.
        """
        word_file = "/usr/share/dict/words"
        wordlist = open(word_file).read().splitlines()
        words = [random.SystemRandom().choice(wordlist) for _ in range(4)]
        words = [re.sub('[\W_]+', '', w).lower() for w in words]
        return " ".join(words)

    def writeToDisk(self, passPhrase="GENERATE", pemFilePathname=None):
        """
        Save the generated key to disk as a .pem file.

        passPhrase -- Used to encrypt the file. Can be 'GENERATE', so
            that a random one is generated.  Or can be '', in which
            no encryption is used.  Or can be a user-chosen passphrase.

        pemFilePathname -- Where to put the .pem file.  Defaults to
        HOME/Downloads.

        """
        self.pemFilePathnameAsStr = pemFilePathname or os.path.join(os.environ["HOME"], "Downloads", self.name)
        self.passphraseAsStr = self.genPassphrase() if passPhrase == "GENERATE" else passPhrase
        if self.passphraseAsStr == "":
            privateKeyPemAsBytes = self.privateKeyPemAsBytes    # no passphrase -- no encryption
        else:
            privateKeyPemAsBytes = self.key.private_bytes(encoding=serialization.Encoding.PEM, format=serialization.PrivateFormat.TraditionalOpenSSL, encryption_algorithm=serialization.BestAvailableEncryption(self.passphraseAsStr.encode('utf-8')))
        with open(self.pemFilePathnameAsStr, "wb") as f:
            f.write(privateKeyPemAsBytes)
        os.chmod(self.pemFilePathnameAsStr, 0o400)


###############################################################################
if __name__ == '__main__':   # pragma: no cover
    if len(sys.argv) > 1 and sys.argv[1].lower() == "--unittest":
        # 'THIS.py --unitTest' or 'THIS.py --unitTest -v'
        import doctest
        logging.basicConfig(level=logging.INFO)    # default to stderr. alt: filename='unittest-{}.log'.format(ModuleName)
        doctest.testmod()
        log.info("tests done")
    else:
        keypair = Keypair()
        keypair.writeToDisk()
        print("//Wrote key to", keypair.pemFilePathnameAsStr)
        print("//Passphrase:",  keypair.passphraseAsStr)
        print("//Public key:", keypair.publicKeyOpensshAsBytes.decode('utf-8'))
