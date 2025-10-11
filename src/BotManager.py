import discord
import os
import datetime
from zoneinfo import ZoneInfo
from sentry_sdk import logger
from discord import app_commands
from MailService import MailService


class BotManager(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

        # Initialize mailgun client
        MSKey = os.getenv("MAILSERVICE_KEY", None)
        self.mailDNS = os.getenv("MAILGUN_DNS", None)
        self.MSClient = MailService(MSKey) if MSKey and self.mailDNS else None

    async def on_ready(self):
        logger.info('BotManager.on_ready: Bot {botUser} initialized!', botUser=self.user)
        guildID = os.getenv("DISCORD_GUILD_ID")
        await self.tree.sync(guild=discord.utils.get(self.guilds, id=guildID))
        logger.info("BotManager.on_ready: Slash Command Synced with guild: {guild_id}", guild_id=guildID)

    def createReportEmbed(self, computedData: dict):
        embed = discord.Embed(
            title="Doordash Financial Report",
            description=f"Processed `{computedData["orderCnt"]}` orders",
            color=0x00FFFF
        )
        embed.add_field(name="Subtotal", value=f"${computedData["subtotal"]}")
        embed.add_field(name="Tax", value=f"${computedData["tax"]}")
        embed.add_field(name="Total", value=f"${computedData["total"]}")
        embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
        return embed

    def sendMailReport(self, computedData: dict, email: str = None):
        email = email or os.getenv("CRON_EMAIL", None)
        if not email:
            logger.error("BotManager.sendMailReport: No email provided for report.")
            return
        if not self.MSClient:
            logger.error("BotManager.sendMailReport: MailService client not initialized. Missing API Key or Domain?")
            return

        email = email.strip().split(",")
        date = datetime.datetime.now(ZoneInfo("America/New_York")).strftime("%m/%d/%Y")

        logger.info("BotManager.sendMailReport: Sending email report")
        req = self.MSClient.sendMail(opt={
            "from": f"DoorDash Parser <noreply@{self.mailDNS}>",
            "to": email,
            "subject": f"{date} Doordash Financial Report",
            "text": f"Today's Doordash Report\nTotal Orders: {computedData["orderCnt"]}\nSubtotal: ${computedData["subtotal"]}\nTax: ${computedData["tax"]}\nTotal: ${computedData["total"]}"
        })
        logger.info("BotManager.sendMailReport: Mailgun API Response -> {res}", res=req.text)
