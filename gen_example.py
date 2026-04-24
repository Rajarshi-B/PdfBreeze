"""
Author: RajarshiB
AI-Agent: Gemini

Generates example PDF files for testing validation.

This script creates an 'example' directory and constructs two test 
PDF documents ('test1.pdf' and 'test3.pdf') containing sample text 
and colored images. It is primarily used to produce mock data for 
testing PDF manipulations operations within the application.
"""
import os, io, pymupdf
from PIL import Image

os.makedirs('example', exist_ok=True)

# Helper for colored image buffers
def make_img_bytes(color, size=(400, 400), fmt='JPEG'):
    img = Image.new('RGB', size, color=color)
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()

sizes = [
    (pymupdf.Rect(50, 100, 300, 350), 'salmon', 'JPEG'),
    (pymupdf.Rect(150, 400, 450, 700), 'lightgreen', 'PNG')
]

doc1 = pymupdf.open()
for i in range(3):
    page = doc1.new_page(width=595, height=842)
    page.insert_text(pymupdf.Point(50, 50), f'Test Document 1 - Page {i+1} Payload', fontsize=20)
    page.insert_text(pymupdf.Point(50, 80), 'Additional detailed text explicitly rendering across bounds.', fontsize=12)
    rect, color, fmt = sizes[i % len(sizes)]
    page.insert_image(rect, stream=make_img_bytes(color, (int(rect.width), int(rect.height)), fmt))
doc1.save(os.path.join('example', 'test1.pdf'))
doc1.close()

doc3 = pymupdf.open()
for i in range(5):
    page = doc3.new_page(width=595, height=842)
    page.insert_text(pymupdf.Point(50, 50), f'Test Document 3 - Page {i+1} Payload', fontsize=20)
    page.insert_text(pymupdf.Point(50, 75), 'Multipage structural sequences mapped internally.', fontsize=14)
    rect, color, fmt = sizes[(i + 1) % len(sizes)]
    page.insert_image(rect, stream=make_img_bytes('lightblue', (int(rect.width), int(rect.height)), 'PNG'))
    if i % 2 == 0:
        page.insert_text(pymupdf.Point(200, 200), 'EVEN PAGE ANNOTATED EXTRACT POINT', fontsize=18)
        
doc3.save(os.path.join('example', 'test3.pdf'))
doc3.close()

print('Example multi-page PDFs uniquely constructed.')
