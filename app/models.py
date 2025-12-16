from __future__ import annotations
from datetime import datetime, date
from sqlalchemy import String, Integer, DateTime, Boolean, ForeignKey, Date, UniqueConstraint, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base

class Staff(Base):
    __tablename__ = "staff"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str | None] = mapped_column(String(254), nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    team: Mapped[str | None] = mapped_column(String(100), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user: Mapped["User" | None] = relationship(back_populates="staff", uselist=False)
    rota_entries: Mapped[list["RotaEntry"]] = relationship(back_populates="staff")

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="Staff", nullable=False)  # Admin/Manager/Staff
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    staff_id: Mapped[int | None] = mapped_column(ForeignKey("staff.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    staff: Mapped["Staff" | None] = relationship(back_populates="user")

class ShiftType(Base):
    __tablename__ = "shift_types"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    rota_entries: Mapped[list["RotaEntry"]] = relationship(back_populates="shift_type")

class RotaEntry(Base):
    __tablename__ = "rota_entries"
    __table_args__ = (
        UniqueConstraint("shift_date", "shift_type_id", name="uq_rota_date_shift_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    shift_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    shift_type_id: Mapped[int] = mapped_column(ForeignKey("shift_types.id"), nullable=False)
    staff_id: Mapped[int | None] = mapped_column(ForeignKey("staff.id"), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    shift_type: Mapped["ShiftType"] = relationship(back_populates="rota_entries")
    staff: Mapped["Staff" | None] = relationship(back_populates="rota_entries")
