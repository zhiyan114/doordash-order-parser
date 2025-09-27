import discord
import os
import datetime
from sentry_sdk import logger
from discord import app_commands


class BotManager(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def on_ready(self):
        logger.info('BotManager.on_ready: Bot {botUser} initialized!', botUser=self.user)
        guildID = os.getenv("DISCORD_GUILD_ID")
        await self.tree.sync(guild=discord.utils.get(self.guilds, id=guildID))
        logger.info("BotManager.on_ready: Slash Command Synced with guild: {guild_id}", guild_id=guildID)

    def createReportEmbed(self, computedData: dict):
        embed = discord.Embed(
            title="Doordash Financial Report",
            description="Today's doordash financial report",
            color=0x00FFFF
        )
        embed.add_field(name="Subtotal", value=f"${computedData["subtotal"]}")
        embed.add_field(name="Tax", value=f"${computedData["tax"]}")
        embed.add_field(name="Total", value=f"${computedData["total"]}")
        embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
        return embed
