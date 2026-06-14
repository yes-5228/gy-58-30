from datetime import date, datetime, timedelta
from typing import Iterable

from fastapi import HTTPException

from app.data.store import store
from app.models.domain import Court, TimeSlot
from app.schemas import CourtCreate, GenerateTimeSlotsRequest, TimeSlotCreate, TimeSlotUpdate


def _parse_time(time_str: str) -> int:
    hours, minutes = map(int, time_str.split(":"))
    return hours * 60 + minutes


def _format_time(minutes: int) -> str:
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def _generate_slot_labels(court: Court) -> list[str]:
    open_min = _parse_time(court.open_time)
    close_min = _parse_time(court.close_time)
    if close_min <= open_min:
        raise HTTPException(status_code=400, detail="关门时间必须晚于开门时间")
    labels = []
    current = open_min
    while current + court.slot_duration <= close_min:
        end = current + court.slot_duration
        labels.append(f"{_format_time(current)}-{_format_time(end)}")
        current = end
    return labels


def _is_peak(label: str, peak_start: str | None, peak_end: str | None) -> bool:
    if not peak_start or not peak_end:
        return False
    slot_start = _parse_time(label.split("-")[0])
    peak_start_min = _parse_time(peak_start)
    peak_end_min = _parse_time(peak_end)
    return peak_start_min <= slot_start < peak_end_min


def list_courts() -> list[Court]:
    return list(store.courts.values())


def create_court(payload: CourtCreate) -> Court:
    court_id = max(store.courts.keys(), default=0) + 1
    court = Court(id=court_id, **payload.model_dump())
    store.courts[court_id] = court
    return court


def list_time_slots(date: str | None = None, court_id: int | None = None) -> list[TimeSlot]:
    slots = list(store.time_slots.values())
    if date:
        slots = [slot for slot in slots if slot.date == date]
    if court_id:
        slots = [slot for slot in slots if slot.court_id == court_id]
    return sorted(slots, key=lambda slot: (slot.date, slot.court_id, slot.label))


def create_time_slot(payload: TimeSlotCreate) -> TimeSlot:
    if payload.court_id not in store.courts:
        raise HTTPException(status_code=404, detail="场地不存在")
    slot_id = store.next_slot_id()
    slot = TimeSlot(id=slot_id, status="available", **payload.model_dump())
    store.time_slots[slot_id] = slot
    return slot


def update_time_slot(slot_id: int, payload: TimeSlotUpdate) -> TimeSlot:
    slot = store.time_slots.get(slot_id)
    if not slot:
        raise HTTPException(status_code=404, detail="时段不存在")
    update_data = payload.model_dump(exclude_unset=True)
    next_status = update_data.get("status")
    if slot.status == "booked" and next_status and next_status != "booked":
        raise HTTPException(status_code=409, detail="已预约时段不可直接变更状态")
    updated = slot.model_copy(update=update_data)
    store.time_slots[slot_id] = updated
    return updated


def generate_time_slots(payload: GenerateTimeSlotsRequest) -> list[TimeSlot]:
    court = store.courts.get(payload.court_id)
    if not court:
        raise HTTPException(status_code=404, detail="场地不存在")
    try:
        start_dt = datetime.strptime(payload.start_date, "%Y-%m-%d").date()
        end_dt = datetime.strptime(payload.end_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式无效")
    if end_dt < start_dt:
        raise HTTPException(status_code=400, detail="结束日期不能早于开始日期")
    slot_labels = _generate_slot_labels(court)
    existing_keys = {(s.date, s.court_id, s.label) for s in store.time_slots.values()}
    created = []
    current = start_dt
    while current <= end_dt:
        date_str = current.isoformat()
        for label in slot_labels:
            key = (date_str, payload.court_id, label)
            if key in existing_keys:
                continue
            price = payload.peak_price if _is_peak(label, payload.peak_start, payload.peak_end) and payload.peak_price else payload.default_price
            slot_id = store.next_slot_id()
            slot = TimeSlot(
                id=slot_id,
                court_id=payload.court_id,
                date=date_str,
                label=label,
                price=price,
                status="available",
            )
            store.time_slots[slot_id] = slot
            existing_keys.add(key)
            created.append(slot)
        current += timedelta(days=1)
    return created
