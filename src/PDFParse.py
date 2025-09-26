import os
import copy
import pymupdf
from sentry_sdk import logger


class DDPDFParser:
    # Contains order ID, subtotal, tax, and total
    PDFData = []

    def parseDir(self, DirPath: str = "./temp", delProcFile: bool = False) -> list:
        if not os.path.isdir(DirPath):
            logger.warn('DDPDFParser.parseDir: Missing directory: {dir}', dir=DirPath)
            return []

        for f in os.listdir(DirPath):
            if f.endswith(".pdf"):
                self.PDFData.append(self.parseFile(os.path.join(DirPath, f)))

        if delProcFile and os.path.isdir(DirPath):
            for f in os.listdir(DirPath):
                os.remove(os.path.join(DirPath, f))
            os.rmdir(DirPath)
            logger.debug('DDPDFParser.parseDir: Cleaned up temp dir: {dir}', dir=DirPath)

        return copy.deepcopy(self.PDFData)

    def parseFile(self, filePath: str) -> dict:
        doc = pymupdf.open(filePath)
        data = {"orderID": "0000000000", "subtotal": 0.0, "tax": 0.0, "total": 0.0}

        # Parse Order Number (format: "Order Number: deadbeef")
        headerText = doc[0].get_text().split("\n")
        orderIDIndex = next((i for i, w in enumerate(headerText) if "Order Number:" in w), -1)
        data["orderID"] = headerText[orderIDIndex].split(":")[1].strip()

        if (doc.page_count == 1):
            # Parse everything in that one page
            data["subtotal"] = self.__computeSubtotal(headerText)
            data["tax"] = self.__computeTax(headerText)
            data["total"] = self.__computeTotal(headerText)
            logger.info("DDPDFParser.parseFile: Parsed {orderID} with {pageNum} pages. Subtotal: ${sub} | Tax: ${tax} | Total: ${tot}",
                        orderID=data["orderID"],
                        pageNum=1,
                        sub=data["subtotal"],
                        tax=data["tax"],
                        tot=data["total"])
            return data

        # Parse multi-page (2+)
        PricePageA = doc[-2].get_text().split("\n")
        PricePageB = doc[-1].get_text().split("\n")

        tempSub = self.__computeSubtotal(PricePageA)
        tempTax = self.__computeTax(PricePageA)
        tempTot = self.__computeTotal(PricePageA)
        data["subtotal"] = tempSub if tempSub != -1 else self.__computeSubtotal(PricePageB)
        data["tax"] = tempTax if tempTax != -1 else self.__computeTax(PricePageB)
        data["total"] = tempTot if tempTot != -1 else self.__computeTotal(PricePageB)

        logger.info("DDPDFParser.parseFile: Parsed {orderID} with {pageNum} pages. Subtotal: ${sub} | Tax: ${tax} | Total: ${tot}",
                    orderID=data["orderID"],
                    pageNum=doc.page_count,
                    sub=data["subtotal"],
                    tax=data["tax"],
                    tot=data["total"])
        return data

    def computeTotals(self) -> dict:
        data = {"subtotal": 0.0, "tax": 0.0, "total": 0.0}
        for item in self.PDFData:
            data["subtotal"] += item.get("subtotal", 0)
            data["tax"] += item.get("tax", 0)
            data["total"] += item.get("total", 0)

        # Basic validation (Check if the potential pdf format is updated)
        if (data["subtotal"] < 0.0):
            raise Exception("DDPDFParser.computeTotals: Subtotal isn't computed correctly (broken parsing algorithm?)")
        if (data["tax"] < 0.0):
            raise Exception("DDPDFParser.computeTotals: Tax isn't computed correctly (broken parsing algorithm?)")
        if (data["total"] < 0.0):
            raise Exception("DDPDFParser.computeTotals: Total isn't computed correctly (broken parsing algorithm?)")

        return data

    # We're just doing guess work with this one lmao
    def __computeSubtotal(self, text: list):
        try:
            subIndex = text.index("Subtotal:") + 1
            return float(text[subIndex][1:])
        except ValueError:
            return -1

    def __computeTax(self, text: list):
        try:
            taxIndex = text.index("+ Tax (6.500%):") + 1
            return float(text[taxIndex][1:])
        except ValueError:
            return -1

    def __computeTotal(self, text: list):
        try:
            totIndex = text.index("Total:") + 1
            return float(text[totIndex][1:])
        except ValueError:
            return -1
