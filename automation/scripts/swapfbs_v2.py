from everpure import FlashBladeAPI
from everpure import EnvironmentReader


gen1_env = EnvironmentReader()
s200_env = EnvironmentReader()

gen1 = FlashBladeAPI() # Todo
s200 = FlashBladeAPI() # Todo

gen1_filesystems = gen1.get_filesystems()
s200_filesystems = s200.get_filesystems()

