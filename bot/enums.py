import enum


class AutoModFeatures(enum.Enum):
    LINKS = "Bans links from being sent to this server"
    IMAGES = "Bans attachments from being sent to this server"
    PING_SPAM = "Temporarily mutes users who are spamming pings in this server"
