#! /usr/bin/python
from pytor import *
import os

# this script generates the public/private keys
# that can be used with the reverse shell

print "Generating the key pair. It may take some time"
pub_key, priv_key= rsa.gen_pubpriv_keys(1024)
print "Writing the keys"

pub_fd=open('./pub.txt','w')
pub_fd.write(str(pub_key))
pub_fd.close()


priv_fd=open('./priv.txt','w')
priv_fd.write(str(priv_key))
priv_fd.close()
