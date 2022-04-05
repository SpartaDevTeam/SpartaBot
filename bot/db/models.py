from sqlalchemy import Column, JSON, String, BigInteger, Integer
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Guilds(Base):
    __tablename__ = "guilds"

    id = Column(BigInteger, primary_key=True)
    infractions = Column(JSON, default="[]", nullable=False)
    mute_role = Column(BigInteger, default=None, nullable=True)
    activated_automod = Column(JSON, default="[]", nullable=False)

    welcome_message = Column(String, default=None, nullable=True)
    leave_message = Column(String, default=None, nullable=True)

    welcome_channel = Column(BigInteger, default=None, nullable=True)
    leave_channel = Column(BigInteger, default=None, nullable=True)

    auto_role = Column(BigInteger, default=None, nullable=True)
    prefix = Column(String, default="s!", nullable=False)
    clear_cap = Column(Integer, default=None, nullable=True)


class AFK(Base):
    __tablename__ = "afks"

    user_id = Column(BigInteger, primary_key=True)
    message = Column(String, nullable=False)
