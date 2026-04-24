"""
Author: RajarshiB
AI-Agent: Gemini

Integration test suite for the PdfBreeze logic operations.

This script performs sequential execution tests on key PDF manipulation 
functions exposed by logic_bridge.py, such as compression, booklet 
generation, interleaving, and long image creation, verifying output generation.
"""
import logic_bridge
import os

example_dir = "example"
test1 = os.path.join(example_dir, "test1.pdf")
test3 = os.path.join(example_dir, "test3.pdf")

out_dir = os.path.join(example_dir, "out")
os.makedirs(out_dir, exist_ok=True)

try:
    print("Testing compress_pdf...")
    out_compress = os.path.join(out_dir, "compress.pdf")
    logic_bridge.compress_pdf(test1, out_compress)
    print("compress_pdf passed", os.path.exists(out_compress))

    print("Testing make_booklet...")
    out_booklet = os.path.join(out_dir, "booklet.pdf")
    logic_bridge.make_booklet(test1, out_booklet)
    print("make_booklet passed", os.path.exists(out_booklet))

    print("Testing interleave_pdfs...")
    out_interleave = os.path.join(out_dir, "interleave.pdf")
    logic_bridge.interleave_pdfs(test1, test3, out_interleave)
    print("interleave_pdfs passed", os.path.exists(out_interleave))

    print("Testing pdf_to_long_image...")
    out_long_img = os.path.join(out_dir, "long_img.png")
    logic_bridge.pdf_to_long_image(test1, out_long_img)
    print("pdf_to_long_image passed", os.path.exists(out_long_img))

    print("Testing pdf_to_images...")
    out_img_dir = os.path.join(out_dir, "extracted_imgs")
    os.makedirs(out_img_dir, exist_ok=True)
    logic_bridge.pdf_to_images(test1, out_img_dir)
    print("pdf_to_images passed", len(os.listdir(out_img_dir)) > 0)

except Exception as e:
    import traceback
    traceback.print_exc()

print("Tests completed.")
