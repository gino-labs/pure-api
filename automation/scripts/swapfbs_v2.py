from everpure import FlashBladeAPI
from everpure import EnvironmentReader

# Setup #
gen1_vars = EnvironmentReader("FB1_NAME", "FB1_MGT", "FB1_TOKEN")
s200_vars = EnvironmentReader("FB2_NAME", "FB2_MGT", "FB2_TOKEN")

gen1 = FlashBladeAPI(*gen1_vars)
s200 = FlashBladeAPI(*s200_vars)

# Fact gathering
gen1_filesystems = gen1.get_filesystems()
s200_filesystems = s200.get_filesystems()

