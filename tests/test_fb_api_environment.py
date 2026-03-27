from everpure import *
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_flashblade_api_instance():
    fbenv = EnvironmentReader("AZFB_NAME", "AZFB_MGT", "AZFB_TOKEN")
    assert fbenv.name
    assert fbenv.mgt
    assert fbenv.token
    fbvars = [fbenv.name, fbenv.mgt, fbenv.token]
    fb = FlashBladeAPI(*fbvars)
    assert fb.name == fbenv.name
    assert fb.session.mgt == fbenv.mgt
    assert fb.session.token == fbenv.token

    arrays = fb.get_arrays()
    assert isinstance(arrays, list)
    assert len(arrays) > 0