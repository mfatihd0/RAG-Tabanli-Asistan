from pypdf import PdfReader

def pdf_oku(dosya_yolu):
    text = ""
    with open(dosya_yolu, "rb") as f:
        reader = PdfReader(f)
        for page in reader.pages:
            text += page.extract_text()
    
    return text

if __name__ == "__main__":
    yazi = pdf_oku("data/raw/pdf/2547_DISIPLIN.pdf")
    print(yazi)