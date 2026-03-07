from everpure import *

def test_env_reader_instance():
    ev_list = ["FB_NAME", "MGT_IP", "API_TOKEN"]
    fbvars = EnvironmentReader(*ev_list)
    for v in ev_list:
        assert v.lower() == fbvars.get_var(v)

#def test_flashblade_api_instance():
#    fb = FlashBladeAPI()

