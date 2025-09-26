import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from sentry_sdk import logger

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


class GmailMgr:
    credPath: str = None
    gCred: Credentials = None
    oAuthPath: str = None

    def __init__(self, oAuthPath: str = "OAuth.json", credPath: str = "GToken.json"):
        if os.path.exists(credPath):
            logger.debug('GmailMgr.__init__: Loading existing token from {file}', file=credPath)
            self.gCred = Credentials.from_authorized_user_file(credPath, SCOPES)
        self.credPath = credPath
        self.oAuthPath = oAuthPath

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

    def download_attachments(self, tempDir: str = "./temp"):
        if not self.gCred:
            logger.warn('GmailMgr.download_attachments: Missing user credential, use fetch_token() first')
            return None

        if not os.path.isdir(tempDir):
            os.mkdir(tempDir)

        searchParam = f"from:orders@doordash.com has:attachment after:{(datetime.today() - timedelta(days=1)).strftime('%Y/%m/%d')}"
        gmailTool = build('gmail', 'v1', credentials=self.gCred)

        logger.info("GmailMgr.download_attachments: Searching emails with query: {param}", param=searchParam)
        searchResult = gmailTool.users().messages().list(userId='me', q=searchParam).execute()

        for msg in searchResult.get('messages', []):
            msg = gmailTool.users().messages().get(userId='me', id=msg['id']).execute()
            for part in msg['payload'].get('parts', []):
                if part['filename'] and part['filename'].endswith('.pdf') and 'attachmentId' in part['body']:
                    attachment = gmailTool.users().messages().attachments().get(
                        userId='me', messageId=msg['id'], id=part['body']['attachmentId']
                    ).execute()
                    data = attachment['data']
                    filePath = os.path.join(tempDir, part['filename'])
                    with open(filePath, 'wb') as f:
                        f.write(data.encode('utf-8'))
                    logger.info('GmailMgr.download_attachments: Saved attachment to {file}', file=filePath)

        # if os.path.isdir(tempDir):
        #     for f in os.listdir(tempDir):
        #         os.remove(os.path.join(tempDir, f))
        #     os.rmdir(tempDir)
        #     logger.debug('GmailMgr.download_attachments: Cleaned up temp dir: {dir}', dir=tempDir)

    def __write_token(self):
        with open(self.credPath, "w") as writer:
            writer.write(self.gCred.to_json())
            logger.info('GmailMgr.__write_token: Saving new token to {file}', file=self.credPath)
