"""Temporary acceptance probe: removed after verifying GitHub blocks the PR."""
import unittest


class GateProbe(unittest.TestCase):
    def test_protected_merge_gate(self):
        self.fail('Intentional acceptance probe: main must not accept this commit')
