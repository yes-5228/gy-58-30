from pydantic import BaseModel, Field


class CourtCreate(BaseModel):
    name: str = Field(min_length=1)
    surface: str = Field(min_length=1)
    indoor: bool = True
    open_time: str = Field(default="08:00", pattern=r"^\d{2}:\d{2}$")
    close_time: str = Field(default="21:00", pattern=r"^\d{2}:\d{2}$")
    slot_duration: int = Field(default=120, ge=30, le=240, multiple_of=30)


class GenerateTimeSlotsRequest(BaseModel):
    court_id: int
    start_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    end_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    default_price: float = Field(gt=0)
    peak_price: float | None = Field(default=None, gt=0)
    peak_start: str | None = Field(default=None, pattern=r"^\d{2}:\d{2}$")
    peak_end: str | None = Field(default=None, pattern=r"^\d{2}:\d{2}$")


class TimeSlotCreate(BaseModel):
    court_id: int
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    label: str = Field(min_length=3)
    price: float = Field(gt=0)


class TimeSlotUpdate(BaseModel):
    price: float | None = Field(default=None, gt=0)
    status: str | None = Field(default=None, pattern="^(available|blocked|booked)$")


class BookingCreate(BaseModel):
    slot_id: int
    member_id: int = 1
    contact_name: str = Field(min_length=1)
