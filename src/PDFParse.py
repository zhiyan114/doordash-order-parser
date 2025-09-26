# if os.path.isdir(tempDir):
#     for f in os.listdir(tempDir):
#         os.remove(os.path.join(tempDir, f))
#     os.rmdir(tempDir)
#     logger.debug('GmailMgr.download_attachments: Cleaned up temp dir: {dir}', dir=tempDir)

import os
import copy
from sentry_sdk import logger


class DDPDFParser:
    # Contains order ID, subtotal, and total
    PDFData = []

    def parseDir(self, DirPath: str, delProcFile: bool = False) -> list:
        if not os.path.isdir(DirPath):
            logger.warn('DDPDFParser.parseDir: Missing directory: {dir}', dir=DirPath)
            return []

        for f in os.listdir(DirPath):
            if f.endswith(".pdf"):
                self.PDFData.append(self.parseFile(os.path.join(DirPath, f), delFile=delProcFile))

        if (delProcFile):
            os.rmdir(DirPath)
            logger.debug('DDPDFParser.parseDir: Cleaned up dir: {dir}', dir=DirPath)
        return copy.deepcopy(self.PDFData)

    def parseFile(filePath: str, delFile: bool = False) -> dict:
        print("PLACEHOLDER")
        return {"orderID": "0000000000", "subtotal": 0, "total": 0}

    def computeTotals(self) -> dict:
        data = {"subtotal": 0, "total": 0}
        for item in self.PDFData:
            data["subtotal"] += item.get("subtotal", 0)
            data["total"] += item.get("total", 0)
        return data
