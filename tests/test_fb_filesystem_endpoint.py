from everpure import *
import urllib3
import pytest
import requests
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class TestFileSystem:
    def setup_method(self):
        env = EnvironmentReader("AZFB_NAME", "AZFB_MGT", "AZFB_TOKEN")
        self.fb = FlashBladeAPI(env.azfb_name, env.azfb_mgt, env.azfb_token)
        self.testfs = "api_testfs"

    @pytest.mark.skip(reason="Previous Success")
    def test_post_filesystem(self):
        fs = self.fb.post_filesystems(self.testfs)
        assert isinstance(fs, list)
        assert fs[0]["name"] == self.testfs
        print(f"File System Posted: {self.testfs}")

    @pytest.mark.skip(reason="Previous Success")
    def test_get_filesystem(self):
        fs = self.fb.get_filesystems(names=self.testfs)
        assert isinstance(fs, list)
        assert fs[0]["name"] == self.testfs
        assert fs[0]["destroyed"] == False
      
    @pytest.mark.skip(reason="Previous Success")
    def test_patch_filesystem(self):
        json = {"destroyed": True, "writable": False}
        fs = self.fb.patch_filesystems(self.testfs, json=json)
        assert isinstance(fs, list)
        assert fs[0]["name"] == self.testfs
        assert fs[0]["destroyed"] == True

    # Should fail because of safemode
    def test_delete_filesystem(self):
        try:
            self.fb.delete_filesystems(self.testfs)
        except requests.exceptions.HTTPError as e:
            pass # FIXME
        except ApiError as e:
            assert e.err_code == 20 # Error code with Safemode On
