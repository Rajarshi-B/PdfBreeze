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

img = Image.new('RGB', (400, 400), color='salmon')
img_buf = io.BytesIO()
img.save(img_buf, format='JPEG')
img_bytes = img_buf.getvalue()

doc1 = pymupdf.open()
page1 = doc1.new_page(width=595, height=842)
page1.insert_text(pymupdf.Point(50, 50), 'Test Document 1 Payload', fontsize=20)
page1.insert_image(pymupdf.Rect(100, 100, 500, 500), stream=img_bytes)
doc1.save(os.path.join('example', 'test1.pdf'))
doc1.close()

img2 = Image.new('RGB', (400, 400), color='lightblue')
img2_buf = io.BytesIO()
img2.save(img2_buf, format='PNG')
img2_bytes = img2_buf.getvalue()

doc3 = pymupdf.open()
page3 = doc3.new_page(width=595, height=842)
page3.insert_text(pymupdf.Point(50, 50), 'Test Document 3 Payload', fontsize=20)
page3.insert_image(pymupdf.Rect(100, 100, 500, 500), stream=img2_bytes)
doc3.save(os.path.join('example', 'test3.pdf'))
doc3.close()
print('Example PDFs uniquely constructed.')
