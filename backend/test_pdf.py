import pdfplumber
with pdfplumber.open('/app/factura_test.pdf') as pdf:
    for i, page in enumerate(pdf.pages):
        print(f"=== PAGINA {i+1} ===")
        print(page.extract_text())
        print()
