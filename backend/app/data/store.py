from __future__ import annotations

from datetime import date, datetime, timedelta

from app.models.domain import Booking, Court, Member, TimeSlot


def _parse_time(time_str: str) -> int:
    hours, minutes = map(int, time_str.split(":"))
    return hours * 60 + minutes


def _format_time(minutes: int) -> str:
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def _generate_slot_labels(open_time: str, close_time: str, slot_duration: int) -> list[str]:
    open_min = _parse_time(open_time)
    close_min = _parse_time(close_time)
    labels = []
    current = open_min
    while current + slot_duration <= close_min:
        end = current + slot_duration
        labels.append(f"{_format_time(current)}-{_format_time(end)}")
        current = end
    return labels


def _is_peak(label: str, peak_start: str, peak_end: str) -> bool:
    slot_start = _parse_time(label.split("-")[0])
    peak_start_min = _parse_time(peak_start)
    peak_end_min = _parse_time(peak_end)
    return peak_start_min <= slot_start < peak_end_min


class InMemoryStore:
    def __init__(self) -> None:
        self.courts: dict[int, Court] = {}
        self.members: dict[int, Member] = {}
        self.time_slots: dict[int, TimeSlot] = {}
        self.bookings: dict[int, Booking] = {}
        self._next_slot_id = 1
        self._next_booking_id = 1
        self._seed()

    def next_booking_id(self) -> int:
        booking_id = self._next_booking_id
        self._next_booking_id += 1
        return booking_id

    def next_slot_id(self) -> int:
        slot_id = self._next_slot_id
        self._next_slot_id += 1
        return slot_id

    def _seed(self) -> None:
        self.courts = {
            1: Court(id=1, name="A1 标准场", surface="木地板", indoor=True, open_time="08:00", close_time="21:00", slot_duration=120),
            2: Court(id=2, name="A2 标准场", surface="木地板", indoor=True, open_time="08:00", close_time="21:00", slot_duration=120),
            3: Court(id=3, name="B1 训练场", surface="PVC", indoor=True, open_time="09:00", close_time="22:00", slot_duration=60),
            4: Court(id=4, name="C1 竞赛场", surface="专业地胶", indoor=True, open_time="07:00", close_time="23:00", slot_duration=120),
        }
        self.members = {
            1: Member(id=1, name="散客", level="普通", discount_rate=1.0, phone=""),
            2: Member(id=2, name="李明", level="银卡", discount_rate=0.9, phone="13800000001"),
            3: Member(id=3, name="王悦", level="金卡", discount_rate=0.8, phone="13800000002"),
            4: Member(id=4, name="陈教练", level="教练", discount_rate=0.7, phone="13800000003"),
        }

        peak_start = "19:00"
        peak_end = "21:00"
        default_price = 80.0
        peak_price = 120.0
        off_peak_price = 60.0

        today = date.today()
        for day_offset in range(7):
            current_day = today + timedelta(days=day_offset)
            for court in self.courts.values():
                slot_labels = _generate_slot_labels(court.open_time, court.close_time, court.slot_duration)
                for label in slot_labels:
                    if _is_peak(label, peak_start, peak_end):
                        price = peak_price
                    elif _is_peak(label, "12:00", "14:00"):
                        price = off_peak_price
                    else:
                        price = default_price
                    slot_id = self.next_slot_id()
                    self.time_slots[slot_id] = TimeSlot(
                        id=slot_id,
                        court_id=court.id,
                        date=current_day.isoformat(),
                        label=label,
                        price=price,
                        status="available",
                    )


store = InMemoryStore()
