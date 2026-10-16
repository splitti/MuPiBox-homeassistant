"""Timer contract tests without an installed Home Assistant distribution."""

import importlib.util
from pathlib import Path
import unittest

path = Path(__file__).resolve().parents[1] / "custom_components/mupibox/sleep_timer_contract.py"
spec = importlib.util.spec_from_file_location("sleep_timer_contract", path)
contract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contract)


class SleepTimerContractTests(unittest.TestCase):
    def test_inactive_timer(self):
        timer = contract.normalize_sleep_timer({"active": False, "ends_at": None, "remaining_s": 0})
        self.assertEqual(contract.remaining_minutes(timer), 0)
        self.assertIsNone(contract.end_datetime(timer))

    def test_remaining_is_rounded_up(self):
        timer = contract.normalize_sleep_timer(
            {"active": True, "ends_at": "2026-10-17T00:45:00+02:00", "remaining_s": 540}
        )
        self.assertEqual(contract.remaining_minutes(timer), 9)
        self.assertIsNotNone(contract.end_datetime(timer).utcoffset())
        timer["remaining_s"] = 1
        self.assertEqual(contract.remaining_minutes(timer), 1)

    def test_reject_missing_or_malformed_state(self):
        for item in (None, {}, {"active": False},
                     {"active": True, "ends_at": "2026-10-17T01:00:00", "remaining_s": 60},
                     {"active": True, "ends_at": "2026-10-17T01:00:00Z", "remaining_s": -1},
                     {"active": True, "ends_at": "2026-10-17T01:00:00Z", "remaining_s": True}):
            with self.subTest(item=item), self.assertRaises((TypeError, ValueError)):
                contract.normalize_sleep_timer(item)


if __name__ == "__main__":
    unittest.main()
