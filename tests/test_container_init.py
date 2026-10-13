"""Container init preserves the worker parent-lifetime contract."""
import unittest,os
from pathlib import Path
from unittest.mock import patch
import yaml
from lic_dsf.worker import parent_probe
class ContainerInit(unittest.TestCase):
    def test_recipe_has_init_and_guard_still_rejects_pid_one(self):
        recipe=yaml.safe_load((Path(__file__).parents[1]/'deploy/compose.yaml').read_text())
        self.assertIs(recipe['services']['calculator']['init'],True)
        with patch('lic_dsf.worker.os.getppid',return_value=1):
            with self.assertRaisesRegex(ValueError,'parent_unavailable'):parent_probe(1)
    @unittest.skipIf(os.name=='nt','Hosted container parent check is POSIX.')
    def test_normal_parent_identity_is_checked(self):
        with patch('lic_dsf.worker.os.getppid',return_value=42):
            alive,close=parent_probe(42)
            self.assertTrue(alive());close()
            with self.assertRaisesRegex(ValueError,'parent_unavailable'):parent_probe(41)
if __name__=='__main__':unittest.main()
