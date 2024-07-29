import unittest
from main import decode_ibc_path, build_denom, CHAIN_CHANNELS, ORIGINAL_DENOMS


class TestMainFunctions(unittest.TestCase):
    def test_build_denom(self):
        origin_chain = "cosmoshub-4"
        dest_chain = "osmosis-1"
        base_denom = "uosmo"

        expected_hash = 'ibc/14F9BC3E44B8A9C1BE1FB08980FAB87034C9905EF17CF2F5008FC085218811CC'
        denom, _ = build_denom(origin_chain, dest_chain, base_denom)
        self.assertEqual(expected_hash, denom)

    def test_build_denom_multiple(self):
        original_denom = "factory/neutron1lzecpea0qxw5xae92xkm3vaddeszr278k7w20c/dAsset"
        origin_chain = "neutron-1"
        journey = ["stride-1", "osmosis-1", "stargaze-1", "neutron-1"]

        path = ''
        for dest_chain in journey:
            current_denom, new_path = build_denom(origin_chain, dest_chain, original_denom, path)
            origin_chain = dest_chain
            path = new_path
        self.assertEqual(current_denom, "ibc/C4A3E0BDA2A18D39FCB66C1D2945F6BF5A9714F0E5221D5E98976196B99F26E8")

    def test_decode_ibc_path(self):
        ibc_denom = "ibc/C4A3E0BDA2A18D39FCB66C1D2945F6BF5A9714F0E5221D5E98976196B99F26E8"
        self.assertEqual(["neutron", "stride", "osmosis", "stargaze", "neutron"],
                         decode_ibc_path(ibc_denom, "neutron-1", ORIGINAL_DENOMS, CHAIN_CHANNELS))


if __name__ == '__main__':
    unittest.main()
