import logging
import sentry_sdk
import dotenv
import os
import asyncio
import discord
import sys
from sentry_sdk.types import Log, Hint
from sentry_sdk import logger, capture_exception
from gmailMGR import GmailMgr
from PDFParse import DDPDFParser
from BotManager import BotManager
from sentry_sdk.integrations.logging import SentryLogsHandler
from sentry_sdk.integrations.logging import LoggingIntegration

botMGR = BotManager()


def log_handler(log: Log, hint: Hint):
    print(log["body"], file=sys.stdout, flush=True)
    return log


@botMGR.tree.command(name="generate", description="Generate today's doordash Financial Report")
@discord.app_commands.describe(email="Email Address to send the report to (comma for multiple)")
async def generate(interaction: discord.Interaction):
    try:
        await interaction.response.defer()

        logger.info("botMGR.tree.command.generate: {username} requested Doordash Financial Report", username=interaction.user.name)
        mailMgr = GmailMgr()
        parserMgr = DDPDFParser()
        mailMgr.fetch_token()
        mailMgr.download_attachments()
        parserMgr.parseDir(delProcFile=True)

        await interaction.followup.send(embed=botMGR.createReportEmbed(parserMgr.computeTotals()))
    except Exception as ex:
        capture_exception(ex)


async def main():
    discord.utils.setup_logging(handler=SentryLogsHandler(level=logging.DEBUG))
    await botMGR.start(os.getenv("DISCORD_TOKEN", None))

if __name__ == "__main__":
    dotenv.load_dotenv()
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN", "http://dead@localhost/0000000"),
        traces_sample_rate=0.0,
        send_default_pii=True,
        enable_logs=True,
        before_send_log=log_handler,
        default_integrations=False,
        disabled_integrations=[
            LoggingIntegration()
        ]
    )
    asyncio.run(main())
