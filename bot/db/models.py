from sqlalchemy import Column, JSON, String, BigInteger, Integer, DateTime
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


class ReactionRoles(Base):
    __tablename__ = "reaction_roles"

    id = Column(String, primary_key=True)
    guild_id = Column(BigInteger, nullable=False)
    channel_id = Column(BigInteger, nullable=False)
    message_id = Column(BigInteger, nullable=False)
    emoji = Column(String, nullable=False)
    role_id = Column(BigInteger, nullable=False)


class Reminders(Base):
    __tablename__ = "reminders"

    id = Column(String, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    message = Column(String, nullable=False)
    start = Column(DateTime, nullable=False)
    due = Column(DateTime, nullable=False)


class Webhooks(Base):
    __tablename__ = "webhooks"

    channel_id = Column(BigInteger, primary_key=True)
    webhook_url = Column(String, nullable=False)


class AutoResponses(Base):
    __tablename__ = "auto_responses"

    id = Column(String, primary_key=True)
    activation = Column(String, nullable=False)
    response = Column(String, nullable=False)