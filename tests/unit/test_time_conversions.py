"""
tests/unit/test_time_conversions.py — Pruebas unitarias de manejo de zonas horarias y transiciones DST en Chile.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
import unittest

from src.shared.time_utils import (
    TZ_SANTIAGO,
    TZ_UTC,
    get_br_window_hours_for_date,
    get_utc_offset_hours,
    is_in_br_window,
    to_local,
    to_utc,
)


class TestTimeConversions(unittest.TestCase):
    def test_summer_winter_offsets(self) -> None:
        """Verifica que el offset UTC sea -3 en verano austral y -4 en invierno austral."""
        # Enero (verano): UTC-3
        dt_verano = datetime(2026, 1, 15, 15, 0, tzinfo=TZ_SANTIAGO)
        self.assertEqual(get_utc_offset_hours(dt_verano), -3)

        # Julio (invierno): UTC-4
        dt_invierno = datetime(2026, 7, 15, 15, 0, tzinfo=TZ_SANTIAGO)
        self.assertEqual(get_utc_offset_hours(dt_invierno), -4)

    def test_utc_roundtrip(self) -> None:
        """Verifica que la conversión local -> UTC -> local sea una biyección exacta."""
        dt_local = datetime(2026, 2, 6, 16, 30, tzinfo=TZ_SANTIAGO)
        dt_utc = to_utc(dt_local)
        dt_local_recup = to_local(dt_utc, target_tz=TZ_SANTIAGO)

        self.assertEqual(dt_local, dt_local_recup)
        self.assertEqual(dt_utc.hour, 19)  # 16:30 + 3h = 19:30 UTC en febrero

    def test_br_window_hours(self) -> None:
        """Verifica la generación de las 5 horas de la tarde (14:00, 15:00, 16:00, 17:00, 18:00)."""
        d = date(2026, 2, 6)
        hours = get_br_window_hours_for_date(d)
        self.assertEqual(len(hours), 5)
        self.assertEqual([h.hour for h in hours], [14, 15, 16, 17, 18])
        for h in hours:
            self.assertTrue(is_in_br_window(h))


if __name__ == "__main__":
    unittest.main()
