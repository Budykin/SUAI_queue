from datetime import datetime
from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "Users" # Как на скриншоте

    # На скриншоте tg_id является первичным ключом
    tg_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    full_name: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String, default="student")

    queues: Mapped[list["Queue"]] = relationship(back_populates="user")

class Subject(Base):
    __tablename__ = "Subjects" # Как на скриншоте

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True)

    queues: Mapped[list["Queue"]] = relationship(back_populates="subject")

class Queue(Base):
    __tablename__ = "Queues" # Как на скриншоте

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("Users.tg_id", ondelete="CASCADE"))
    subject_id: Mapped[int] = mapped_column(ForeignKey("Subjects.id", ondelete="CASCADE"))
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    user: Mapped["User"] = relationship(back_populates="queues")
    subject: Mapped["Subject"] = relationship(back_populates="queues")