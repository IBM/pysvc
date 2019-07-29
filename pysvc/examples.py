"""
Usage examples of the SVC CLI Client.
"""

from pysvc.unified.client import connect

# Connect storage array through SSH
# It supports two authentication methods
# 1) use SSH prviate key to login
#    Prerequisite:
#     configure SSH Public Key to the storage user (e.g. admin)
#     from storage GUI(Access --> Users --> Create user with the SSH Pubic Key)
svccli = connect('ip', username='admin', privatekey_filename=r'/local/key')

# 2) use username and password to login
svccli = connect('ip_address', username='username', password='password')

# Create volume
svccli.svctask.mkvolume(name="vol_name", pool="pool", size=1, unit='gb')

# Get Volume from storage
vol = svccli.svcinfo.lsvdisk(object_id='vol_name').as_single_element
print(vol.name)

# Get all the volumes from storage as a list element
vols = svccli.svcinfo.lsvdisk(bytes=True).as_list
for vol in vols:
    print(vol.name)

# Get Pool from storage
pool = svccli.svcinfo.lsmdiskgrp(object_id='pool_name').as_single_element
print(pool.name)

# Getting all of the pools from storage as a list element
pools = svccli.svcinfo.lsmdiskgrp().as_list
for p in pools:
    print(p.name)
