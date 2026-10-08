"""Dependency-free compatibility tests for the proposed Classic contract."""
import importlib.util
from pathlib import Path
import unittest

path = Path(__file__).resolve().parents[1] / 'custom_components/mupibox/classic_contract.py'
spec = importlib.util.spec_from_file_location('classic_contract', path)
contract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contract)


class ClassicContractTests(unittest.TestCase):
    def test_legacy_ng_discovery_is_unchanged(self):
        self.assertEqual(contract.discovery_generation({'id': 'ng-existing'}), 'ng')

    def test_classic_discovery_supports_avahi_bytes(self):
        self.assertEqual(contract.discovery_generation({'generation': b'classic'}), 'classic')
        self.assertEqual(contract.classic_identity({'device_id': b'stable-123'}), 'stable-123')

    def test_classic_identity_must_match(self):
        info = {'generation': 'classic', 'api_version': 1, 'device_id': 'stable-123'}
        self.assertEqual(contract.validate_classic_info(info, 'stable-123'), 'stable-123')
        with self.assertRaises(ValueError):
            contract.validate_classic_info(info, 'different')

    def test_unsupported_protocol_is_rejected(self):
        with self.assertRaises(ValueError):
            contract.validate_classic_info({'generation': 'classic', 'api_version': 2, 'device_id': 'abc'})

    def test_state_mapping(self):
        result = contract.normalize_classic_state({'playback': {'state': 'playing', 'title': 'Music', 'volume': 42}})
        self.assertEqual(result['queue'][0]['title'], 'Music')
        self.assertEqual(result['max_volume'], 100)
        self.assertEqual(result['volume'], 42)


if __name__ == '__main__':
    unittest.main()
