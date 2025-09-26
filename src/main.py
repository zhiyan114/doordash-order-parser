import sentry_sdk
import dotenv
import os
from sentry_sdk.types import Log, Hint
from gmailMGR import GmailMgr
from PDFParse import DDPDFParser


def log_handler(log: Log, hint: Hint):
    print(log["body"])

    # Probably sentry's own log
    if len(log["body"].split(":")) < 2:
        return None
    return log


if __name__ == "__main__":
    dotenv.load_dotenv()
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN", "http://dead@localhost/0000000"),
        traces_sample_rate=1.0,
        enable_logs=True,
        before_send_log=log_handler
    )
    # mailMgr = GmailMgr()
    parserMgr = DDPDFParser()
    # mailMgr.fetch_token()
    # mailMgr.download_attachments()
    parserMgr.parseDir()
    print(parserMgr.computeTotals())
