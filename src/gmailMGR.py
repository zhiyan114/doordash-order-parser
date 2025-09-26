from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


class GmailMgr:
    credPath: Credentials = None
    rawToken: str = None
    oAuthPath: str = None

    def __init__(self, oAuthPath: str = "OAuth.json", credPath: str = "GToken.json"):
        self.credJSON = credPath
        self.oAuthPath = oAuthPath

    def fetch_token(self):
        if self.rawToken is not None:
            return self.rawToken
        creds = Credentials.from_authorized_user_file(self.credPath, SCOPES)
        if not creds:
            oauth = InstalledAppFlow.from_client_secrets_file(self.oAuthPath, SCOPES)
            creds = oauth.run_local_server()
            with open(self.credPath, "w") as writer:
                writer.write(creds.to_json())

        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
        self.rawToken = creds.token
        return self.rawToken
