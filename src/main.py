import sentry_sdk
from sentry_sdk.types import Log, Hint
from gmailMGR import GmailMgr


def log_handler(log: Log, hint: Hint):
    print(log["body"])
    return log


if __name__ == "__main__":
    sentry_sdk.init(
        dsn="http://dead@localhost/0000000",
        traces_sample_rate=1.0,
        enable_logs=True,
        before_send_log=log_handler
    )
    mailMgr = GmailMgr()
    mailMgr.fetch_token()
    mailMgr.download_attachments()