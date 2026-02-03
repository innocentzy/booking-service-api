from datetime import datetime, date

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    ValidationInfo,
)

from app.models import UserRole, BookingStatus, PropertyStatus, Property


class UserCreate(BaseModel):
    first_name: str = Field(..., min_length=2, max_length=50)
    last_name: str = Field(..., min_length=2, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    email: EmailStr
    role: UserRole
    created_at: datetime


class PropertyBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=3, max_length=255)
    address: str = Field(..., min_length=3, max_length=255)
    city: str = Field(..., min_length=3, max_length=255)
    beds: int = Field(..., ge=1, le=10)
    price: float = Field(..., ge=0.0)


class PropertyCreate(PropertyBase):
    pass


class PropertyFilter(BaseModel):
    city: str | None
    beds: int | None
    min_price: float | None
    max_price: float | None

    @field_validator("min_price", "max_price")
    @classmethod
    def validate_price(cls, value: float) -> float:
        if value is None:
            return value
        if value < 0:
            raise ValueError("Price must be positive")
        return value


class PropertyUpdate(BaseModel):
    title: str | None = Field(None, min_length=3, max_length=255)
    description: str | None = Field(None, min_length=3, max_length=255)
    address: str | None = Field(None, min_length=3, max_length=255)
    city: str | None = Field(None, min_length=3, max_length=255)
    beds: int | None = Field(None, ge=1, le=10)
    price: float | None = Field(None, ge=0.0)


class PropertyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    host_id: int
    title: str
    description: str
    address: str
    city: str
    beds: int
    price: float
    status: PropertyStatus
    created_at: datetime
    user: UserResponse


class PaginatedProperties(BaseModel):
    items: list[PropertyResponse]
    total: int
    limit: int
    offset: int


class BookingCreate(BaseModel):
    property_id: int
    guests: int
    check_in: date
    check_out: date

    @field_validator("check_in")
    @classmethod
    def check_in_date_is_after_today(cls, v: date) -> date:
        if v < date.today():
            raise ValueError("Check-in date must be after today")
        return v

    @field_validator("check_out")
    @classmethod
    def check_out_must_be_after_start(cls, v: date, info: ValidationInfo) -> date:
        if "check_in" in info.data and v <= info.data["check_in"]:
            raise ValueError("Check-out must be after check-in")
        return v


class BookingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    guest_id: int
    property_id: int
    guests: int
    check_in: date
    check_out: date
    total_price: float
    status: BookingStatus
    created_at: datetime
    updated_at: datetime
    cancelled_at: datetime


class Token(BaseModel):
    value: str
    token_type: str
    token_sign: str = "bearer"


class TokensPair(BaseModel):
    access_token: Token
    refresh_token: Token


class TokenData(BaseModel):
    user_id: int | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
