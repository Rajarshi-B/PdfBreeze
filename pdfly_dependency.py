"""
Author: RajarshiB
AI-Agent: Gemini

Consolidated logic derived from pdfly.
Features: compress_pdf, make_booklet, extract_annotated_pages
"""
import shutil
from io import BytesIO
from pathlib import Path
from collections.abc import Generator

from pypdf import PdfReader, PdfWriter, PageObject
from pypdf.generic import FloatObject, RectangleObject
from pypdf.annotations import AnnotationDictionary


# ==========================================
# COMPRESS LOGIC (from pdfly.compress)
# ==========================================
import pymupdf
import pymupdf
import pymupdf
import io
import shutil
from PIL import Image

def compress_pdf_main(pdf: Path, output: Path, level: str = "Basic") -> None:
    """
    Compresses a PDF file using PyMuPDF tier-based image down-sampling.

    Args:
        pdf (Path): Path to the input PDF file.
        output (Path): Path where the compressed PDF will be saved.
        level (str): Compression level ("Basic", "Intermediate", or customized lower levels). Default is "Basic".
    """
    doc = pymupdf.open(str(pdf))
    orig_size = pdf.stat().st_size
    
    if level == "Basic":
        doc.save(str(output), garbage=3, deflate=True)
        doc.close()
        
        # PyMuPDF restructuring can occasionally increase metadata/xref tables if the file was highly custom.
        # Validating output prevents negative compression ratios.
        if output.stat().st_size >= orig_size:
            shutil.copy2(pdf, output)
        return
        
    img_quality = 65 if level == "Intermediate" else 30
    zoom = 0.75 if level == "Intermediate" else 0.5

    seen_xrefs = set()

    for page in doc:
        image_list = page.get_images()
        for img in image_list:
            xref = img[0]
            if xref in seen_xrefs:
                continue

            try:
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                
                pil_img = Image.open(io.BytesIO(image_bytes))
                
                # Strip alphas and re-flatten to RGB
                if pil_img.mode in ("RGBA", "P", "LA"):
                    bg = Image.new("RGB", pil_img.size, (255, 255, 255))
                    if pil_img.mode in ("RGBA", "LA"):
                        bg.paste(pil_img, mask=pil_img.split()[-1]) 
                    else:
                        bg.paste(pil_img)
                    pil_img = bg
                elif pil_img.mode != "RGB":
                    pil_img = pil_img.convert("RGB")
                    
                target_width = int(pil_img.width * zoom)
                target_height = int(pil_img.height * zoom)
                
                if target_width > 50 and target_height > 50:
                    pil_img = pil_img.resize((target_width, target_height), Image.Resampling.LANCZOS)
                
                img_buffer = io.BytesIO()
                pil_img.save(img_buffer, format="JPEG", quality=img_quality, optimize=True)
                new_image_bytes = img_buffer.getvalue()
                
                # Safely overwrite PDF using PyMuPDF's abstraction ensuring no bounding-box/xref corruption
                page.replace_image(xref, stream=new_image_bytes)
                seen_xrefs.add(xref)

            except Exception:
                continue

    doc.save(str(output), garbage=4, deflate=True)

# ==========================================
# BOOKLET LOGIC (from pdfly.booklet)
# ==========================================
def page_iter(num_pages: int) -> Generator[tuple[int, int], None, None]:
    """
    Generates pairs of page indices for booklet printing.

    Generates page index pairs representing the left and right pages for 
    each sheet to assemble a standard foldable booklet.

    Args:
        num_pages (int): The total number of pages in the document. Must be divisible by 4.

    Yields:
        Generator[tuple[int, int], None, None]: Tuples representing the (lhs, rhs) page indices.

    Raises:
        ValueError: If num_pages is not divisible by 4.
    """
    if num_pages % 4 != 0:
        raise ValueError("Number of pages must be divisible by 4")

    for sheet in range(num_pages // 4):
        last_page = num_pages - sheet * 2 - 1
        first_page = sheet * 2
        second_page = sheet * 2 + 1
        second_to_last_page = num_pages - sheet * 2 - 2

        yield last_page, first_page
        yield second_page, second_to_last_page

def requires_rotate(a: RectangleObject, b: RectangleObject) -> bool:
    """
    Determines if rotation is required between two bounding boxes.

    Args:
        a (RectangleObject): The primary page rectangle object.
        b (RectangleObject): The secondary page rectangle object.

    Returns:
        bool: True if the rectangles have different orientations (e.g. one portrait, one landscape).
    """
    a_portrait = a.height > a.width
    b_portrait = b.height > b.width
    return a_portrait != b_portrait

def fetch_first_page(filename: Path) -> PageObject:
    """
    Retrieves the first page of a given PDF file.

    Args:
        filename (Path): The path to the PDF file.

    Returns:
        PageObject: The extracted first page object from pypdf.
    """
    return PdfReader(filename).pages[0]

def make_booklet_main(
    filename: Path,
    output: Path,
    inside_cover_file: Path | None = None,
    centerfold_file: Path | None = None,
) -> None:
    """
    Creates a 2-up standard booklet from a provided PDF file.

    Arranges pages into a format suitable for printing and folding into 
    a booklet, dynamically scaling and merging translated pages.

    Args:
        filename (Path): The input PDF file.
        output (Path): The output booklet PDF path.
        inside_cover_file (Path | None): Optional PDF for the inside cover.
        centerfold_file (Path | None): Optional PDF for the centerfold.

    Raises:
        RuntimeError: If an error occurs during processing.
    """
    try:
        reader = PdfReader(filename)
        pages = list(reader.pages)
        writer = PdfWriter()

        blank_page = PageObject.create_blank_page(
            width=pages[0].mediabox.width, height=pages[0].mediabox.height
        )
        if len(pages) % 2 == 1:
            if inside_cover_file:
                ic_reader_page = fetch_first_page(inside_cover_file)
                pages.insert(-1, ic_reader_page)
            else:
                pages.insert(-1, blank_page)
        if len(pages) % 4 == 2:
            pages.insert(len(pages) // 2, blank_page)
            pages.insert(len(pages) // 2, blank_page)
            requires_centerfold = True
        else:
            requires_centerfold = False

        for lhs, rhs in page_iter(len(pages)):
            pages[lhs].merge_translated_page(
                page2=pages[rhs],
                tx=pages[lhs].mediabox.width,
                ty=0,
                expand=True,
                over=True,
            )
            pages[lhs].cropbox[2] = FloatObject(2 * pages[lhs].cropbox[2])
            writer.add_page(pages[lhs])

        if requires_centerfold and centerfold_file:
            centerfold_page = fetch_first_page(centerfold_file)
            last_page = writer.pages[-1]
            if centerfold_page.rotation != 0:
                centerfold_page.transfer_rotation_to_content()
            if requires_rotate(centerfold_page.mediabox, last_page.mediabox):
                centerfold_page = centerfold_page.rotate(270)
            if centerfold_page.rotation != 0:
                centerfold_page.transfer_rotation_to_content()
            last_page.merge_page(centerfold_page)

        with open(output, "wb") as output_fh:
            writer.write(output_fh)

    except Exception as error:
        raise RuntimeError(f"Error while processing {filename}") from error


# ==========================================
# EXTRACT ANNOTATED PAGES LOGIC (from pdfly.extract_annotated_pages)
# ==========================================
def is_manipulable(annot: AnnotationDictionary) -> bool:
    """
    Checks if a PDF annotation is manipulable (not a basic link).

    Args:
        annot (AnnotationDictionary): The dictionary representation of a PDF annotation.

    Returns:
        bool: True if the annotation is manipulable (Subtype is not /Link).
    """
    return annot.get("/Subtype") != "/Link"

def extract_annotated_main(input_pdf: Path, output_pdf: Path | None) -> None:
    """
    Extracts pages containing annotations from a PDF file.

    Iterates through the original document and copies over only the pages 
    that feature manipulable annotations (like highlights or text).

    Args:
        input_pdf (Path): Input PDF file.
        output_pdf (Path | None): Output PDF file path. If None, saves with a suffix.
    """
    if not output_pdf:
        output_pdf = input_pdf.with_name(input_pdf.stem + "_annotated.pdf")
    input_reader = PdfReader(input_pdf)
    output = PdfWriter()
    for page in input_reader.pages:
        if "/Annots" not in page:
            continue
        page_annots = page["/Annots"]
        if not any(is_manipulable(annot) for annot in page_annots):
            continue
        output.add_page(page)
    output.write(output_pdf)
