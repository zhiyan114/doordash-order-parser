import os
import base64
import math
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import datetime
from zoneinfo import ZoneInfo
from sentry_sdk import logger, trace, capture_exception

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Track Docs: https://googleapis.github.io/google-api-python-client/docs/dyn/gmail_v1.html


class GmailMgr:
    credPath: str = None
    gCred: Credentials = None
    oAuthPath: str = None
    attachmentLists: list = []  # (msgID, attID, fileName)
    tempDir: str = None

    def __init__(self, oAuthPath: str = "OAuth.json", credPath: str = "GToken.json", tempDir: str = "./temp"):
        envToken = os.getenv("GTOKEN", None)
        if envToken:
            logger.debug('GmailMgr.__init__: Loading existing token from environment variable GTOKEN')
            self.gCred = Credentials.from_authorized_user_info(json.loads(envToken), SCOPES)
        if not self.gCred and os.path.exists(credPath):
            logger.debug('GmailMgr.__init__: Loading existing token from {file}', file=credPath)
            self.gCred = Credentials.from_authorized_user_file(credPath, SCOPES)

        self.credPath = credPath
        self.oAuthPath = oAuthPath
        self.attachmentLists = []
        self.tempDir = tempDir

    @trace(op="fetch_token", name="Fetch OAuth Token")
    def fetch_token(self):
        # Prompt OAuth
        if not self.gCred:
            logger.info('GmailMgr.fetch_token: Prompting User Interactive OAuth using client secret: {file}', file=self.oAuthPath)
            oauth = InstalledAppFlow.from_client_secrets_file(self.oAuthPath, SCOPES)
            self.gCred = oauth.run_local_server(prompt="consent", access_type='offline')
            self.__write_token()

        if self.gCred.expired and self.gCred.refresh_token:
            self.gCred.refresh(Request())
            self.__write_token()

        return self.gCred

    @trace(op="download_attachments", name="Download Email Attachments")
    def download_attachments(self):
        if not self.gCred:
            logger.warn('GmailMgr.download_attachments: Missing user credential, use fetch_token() first')
            return None

        if not os.path.isdir(self.tempDir):
            os.mkdir(self.tempDir)

        tz = ZoneInfo("America/New_York")
        dNow = datetime.now(tz)
        searchParam = f"from:orders@doordash.com has:attachment after:{math.ceil((datetime(dNow.year, dNow.month, dNow.day, 0, 0, 0, tzinfo=tz)).timestamp())}"
        gmailTool = build('gmail', 'v1', credentials=self.gCred)
        self.attachmentLists = []

        logger.info("GmailMgr.download_attachments: Searching emails with query: {param}", param=searchParam)
        searchMsgs = gmailTool.users().messages().list(userId='me', q=searchParam).execute().get('messages', [])
        if len(searchMsgs) == 0:
            logger.info("GmailMgr.download_attachments: No eligible messages are available to be processed")
            return

        # Get attachment ID from all eligible messages
        logger.info("GmailMgr.download_attachments: Processing {count} messages", count=len(searchMsgs))
        msg_batch = gmailTool.new_batch_http_request()
        for msg in searchMsgs:
            msg_batch.add(
                gmailTool.users().messages().get(userId='me', id=msg['id']),
                callback=self.message_callback
            )
            logger.debug("GmailMgr.download_attachments: Batched Message {id}", id=msg['id'])
        msg_batch.execute()

        # Batch attachment downloads
        logger.info("GmailMgr.download_attachments: Processing {count} attachments", count=len(self.attachmentLists))
        att_batch = gmailTool.new_batch_http_request()
        for att_data in self.attachmentLists:
            att_batch.add(
                gmailTool.users().messages().attachments().get(userId='me', messageId=att_data[0], id=att_data[1]),
                callback=self.attachment_callback,
                request_id=f"{att_data[0]}::{att_data[2]}"  # msgID::FileName
            )
        att_batch.execute()

        # Clean up
        gmailTool.close()

    @trace(op="message_callback", name="Batch Message Handle Callback")
    def message_callback(self, reqID, res, ex):
        if (ex):
            capture_exception(ex)
            return

        for part in res['payload'].get('parts', []):
            if part['filename'] and 'attachmentId' in part['body']:
                filePath = os.path.join(self.tempDir, part['filename'])
                if not os.path.exists(filePath):
                    self.attachmentLists.append((res['id'], part['body']['attachmentId'], part['filename']))
                else:
                    logger.warning('GmailMgr.download_attachments: attachment already existed for {file}', file=filePath)

    @trace(op="attachment_callback", name="Batch Attachment Handle Callback")
    def attachment_callback(self, reqID, res, ex):
        if (ex):
            capture_exception(ex)
            return

        msg_id, filename = reqID.split("::", 1)
        filePath = os.path.join(self.tempDir, filename)

        if not os.path.exists(filePath):
            with open(filePath, 'wb') as f:
                f.write(base64.urlsafe_b64decode(res['data']))
            logger.debug('GmailMgr.download_attachments: Saved {msgid} attachment to {file}', msgid=msg_id, file=filePath)
        else:
            logger.warning('GmailMgr.download_attachments: attachment already existed for {file}', file=filePath)

    def __write_token(self):
        with open(self.credPath, "w") as writer:
            writer.write(self.gCred.to_json())
            logger.info('GmailMgr.__write_token: Saving new token to {file}', file=self.credPath)
