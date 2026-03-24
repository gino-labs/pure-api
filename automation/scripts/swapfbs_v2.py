import os

from everpure import FlashBladeAPI
from everpure import EnvironmentReader

### SETUP ###

# Environment variables
gen1_vars = EnvironmentReader("FB1_NAME", "FB1_MGT", "FB1_TOKEN")
s200_vars = EnvironmentReader("FB2_NAME", "FB2_MGT", "FB2_TOKEN")

# FlashBlade API instances
gen1 = FlashBladeAPI(*gen1_vars)
s200 = FlashBladeAPI(*s200_vars)

# File systems
gen1_filesystems = gen1.get_filesystems()
s200_filesystems = s200.get_filesystems()

# Replication links
g1_replica_links = gen1.get_filesystem_replica_links()
g1_replica_filesystems = [link["local_file_system"]["name"] for link in g1_replica_links]

# Network interfaces
g1_interfaces = gen1.get_network_interfaces()
s2_interfaces = s200.get_network_interfaces()

# Ansible
ansible_dir = '../ansible/'
os.makedirs(f"{ansible_dir}/inventory", exist_ok=True)
os.makedirs(f"{ansible_dir}/vars", exist_ok=True)


### Functions ###

def take_snapshots():
    pass

def create_client_inventory():
    pass

def dump_production_vars():
    pass

def dump_secondary_vars():
    pass

def demote_gen1_flashblade():
    pass

def swap_production_vars_to_s200():
    pass

def promote_s200_flashblade():
    pass

def delete_replication_links():
    pass

def remount_nfs_clients():
    pass

if __name__ == "__main__":
    pass

