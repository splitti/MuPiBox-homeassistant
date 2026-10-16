"""Dependency-free checks for distinct Zeroconf discovery card names."""

import importlib.util
from pathlib import Path
import unittest

path = Path(__file__).resolve().parents[1] / "custom_components/mupibox/discovery_label.py"
spec = importlib.util.spec_from_file_location("discovery_label", path)
labels = importlib.util.module_from_spec(spec)
spec.loader.exec_module(labels)


class DiscoveryLabelTests(unittest.TestCase):
    def test_classic_advertised_name(self):
        self.assertEqual(
            labels.discovery_title({"name": b"JanBox"}, "classic",
                "MuPiBox._mupibox._tcp.local.", "janbox.home."),
            "MuPiBox Classic – JanBox",
        )

    def test_ng_advertised_name_different_from_host(self):
        self.assertEqual(
            labels.discovery_title({"name": "Felix Musikbox"}, "ng",
                "MuPiBox NG Secure pi110._mupibox._tcp.local.", "pi110.local."),
            "MuPiBox NG – Felix Musikbox (pi110.local)",
        )

    def test_ng_existing_service_instance_without_txt_name(self):
        self.assertEqual(
            labels.discovery_title({}, "ng",
                "MuPiBox NG Secure pi110._mupibox._tcp.local.", "pi110.local."),
            "MuPiBox NG – pi110",
        )

    def test_classic_generic_name_falls_back_to_hostname(self):
        self.assertEqual(
            labels.discovery_title({"name": "MuPiBox"}, "classic",
                "MuPiBox._mupibox._tcp.local.", "classicbox.home."),
            "MuPiBox Classic – classicbox.home",
        )

    def test_fallback_on_legacy_missing_fields(self):
        self.assertEqual(
            labels.discovery_title({}, "ng", "MuPiBox._mupibox._tcp.local.",
                                  "192.168.2.110"),
            "MuPiBox NG – 192.168.2.110",
        )

    def test_sanitize_control_chars(self):
        self.assertEqual(
            labels.discovery_title({"name": b"Kinder\nBox\x00"}, "classic",
                                   "MuPiBox._mupibox._tcp.local.", "janbox.local."),
            "MuPiBox Classic – KinderBox (janbox.local)",
        )

    def test_generation_is_always_displayed(self):
        props = {"name": "Musikzimmer"}
        classic = labels.discovery_title(props, "classic", "MuPiBox", "a.local")
        ng = labels.discovery_title(props, "ng", "MuPiBox", "a.local")
        self.assertNotEqual(classic, ng)


if __name__ == "__main__":
    unittest.main()
