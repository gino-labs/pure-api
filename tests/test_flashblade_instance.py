from everpure import *
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_env_reader_instance():
    ev_list = ["FB_NAME", "MGT_IP", "API_TOKEN"]
    fbenv = EnvironmentReader(*ev_list)
    for v in ev_list:
        assert v.lower() == fbenv.get_var(v)

def test_flashblade_api_instance():
    fbenv = EnvironmentReader("AZFB_NAME", "AZFB_MGT", "AZFB_TOKEN")
    assert fbenv.azfb_name
    assert fbenv.azfb_mgt
    assert fbenv.azfb_token
    fbvars = [fbenv.azfb_name, fbenv.azfb_mgt, fbenv.azfb_token]
    fb = FlashBladeAPI(*fbvars)

