from mailgun.client import Client
import os
from datetime import datetime
from zoneinfo import ZoneInfo

email = os.getenv("CRON_EMAIL", None)
MGKey = os.getenv("MAILGUN_KEY", None)
mailDNS = os.getenv("MAILGUN_DNS", None)
client = Client(auth=("api", MGKey)) if MGKey and mailDNS else None
email = email.strip().split(",")
date = datetime.now(ZoneInfo("America/New_York")).strftime("%m/%d/%Y")

req = client.messages.create(data={
    "from": f"DoorDash Parser <DDParser@{mailDNS}>",
    "to": email,
    "subject": f"{date} Doordash Financial Report",
    "text": f"Today's Doordash Report\nTotal Orders: ${100}\nSubtotal: ${12}\nTax: ${12}\nTotal: ${24}"
}, domain=mailDNS)
print(f"BotManager.sendMailReport: Mailgun API Response -> {req.text}")
