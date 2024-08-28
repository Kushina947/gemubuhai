import discord

class Team:
    def __init__(self, guild: discord.Guild, channel_id, role_id) -> None:
        self.channel = guild.get_channel(channel_id)
        self.role = guild.get_role(role_id)