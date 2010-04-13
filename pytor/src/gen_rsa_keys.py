#! /usr/bin/python
import rsa

# this script generates the public/private keys
# that can be used with the reverse shell

print  "public=%s\nprivate=%s" % rsa.gen_pubpriv_keys(1024)
