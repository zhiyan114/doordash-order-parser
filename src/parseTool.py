# NOT USE IN PRODUCTION, USE FOR DEVELOPMENT ONLY!!!

import pymupdf

if __name__ == "__main__":
    doc = pymupdf.open("test.pdf")
    for page in doc:
        print("PAGE CONTENT:", page.get_text())
    print("PAGE COUNT:", doc.page_count)
