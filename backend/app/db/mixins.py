from datetime import UTC, datetime

from sqlalchemy import TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column


def utc_now() -> datetime:
    """Return a timezone-naive datetime whose value is always UTC.

    Values are generated in UTC and use UTC_TIMESTAMP() for database-side
    defaults. MariaDB TIMESTAMP values are session-time-zone converted, so DB
    connections must use a UTC session time zone.
    """

    return datetime.now(UTC).replace(tzinfo=None)


class CreatedAtMixin:
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        default=utc_now,
        server_default=func.utc_timestamp(),
        nullable=False,
    )


class UpdatedAtMixin:
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        default=utc_now,
        server_default=func.utc_timestamp(),
        onupdate=utc_now,
        nullable=False,
    )


class SoftDeleteMixin:
    deleted_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP,
        nullable=True,
    )
