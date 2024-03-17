import fitz  # PyMuPDF library for PDF parsing

def pdf_reader(file_name):
    text = ""
    pageNum = 1

    # Open the PDF file
    with fitz.open(file_name) as pdf:
        for page_num in range(len(pdf)):
            page = pdf.load_page(page_num)
            text += f"\nPN: {page_num}\n"
            text += page.get_text() + "\n"
            print(text)

    return text

pdf_reader("code/test.pdf")
