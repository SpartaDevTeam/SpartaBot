import enum


class AutoModFeatures(enum.Enum):
    LINKS = "Bans links from being sent to this server"
    IMAGES = "Bans attachments from being sent to this server"
    SPAM = "Temporarily mutes users who are spamming mentions in this server"
