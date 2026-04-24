"""
Author: RajarshiB
AI-Agent: Gemini

Consolidated logic derived from PDFeXpress.
Features: merge invoices, long image, interleave, pdf to image, delete pages, extract text, extract images, add page numbers.
"""

import pymupdf
import re
from pathlib import Path
from PIL import Image
from typing import Any
from functools import lru_cache
from collections import namedtuple

# ==========================================
# TRANSLATION DUMMY STUBS
# ==========================================
def _(text):
    """ Translation function wrapper. """
    return text

def ngettext(singular, plural, n):
    """ Pluralization translation function wrapper. """
    return singular if n == 1 else plural


# ==========================================
# PARSERS (from toolkit.util)
# ==========================================
def _parse_range(range_string: str, total_pages: int) -> list[int]:
    chunk: list[int] = []
    step = 1
    range_part = range_string

    if ':' in range_string:
        range_part, step_part = range_string.rsplit(':', 1)
        step = int(step_part)
        if range_part == '':
            return list(range(0, total_pages, step))

    if '-' in range_part:
        if range_part.startswith('-') and range_part.count('-') == 1:
            start = 1
            end = int(range_part[1:])
        elif range_part.endswith('-') and range_part.count('-') == 1:
            start = int(range_part[:-1])
            end = total_pages
        else:
            start_str, end_str = range_part.split('-', 1)
            start = int(start_str)
            end = int(end_str)

            if start > end:
                return list(range(start - 1, end - 2, -step))

        if start < 1 or end > total_pages:
            raise ValueError(_("Invalid range '{part}': must be between 1-{total_pages}.").format(part=range_string, total_pages=total_pages))
        chunk = list(range(start - 1, end, step))
    else:
        page = int(range_part)
        if page < 1 or page > total_pages:
            raise ValueError(_("Invalid page '{part}': must be between 1-{total_pages}.").format(part=range_string, total_pages=total_pages))
        chunk = [page - 1]

    return chunk

def _parse_ranges_without_duplicates(range_string: str, total_pages: int) -> list[int]:
    chunk: list[int] = []
    seen = set()
    for range_part in range_string.split(','):
        range_part = range_part.strip()
        if not range_part:
            continue
        range_pages = _parse_range(range_part, total_pages)
        for page in range_pages:
            if page not in seen:
                seen.add(page)
                chunk.append(page)
    return chunk

def _parse_ranges_with_duplicates(range_string: str, total_pages: int) -> list[int]:
    chunk: list[int] = []
    if range_string.startswith('+'):
        range_string = range_string[1:].strip()
    for range_part in range_string.split(','):
        range_part = range_part.strip()
        if not range_part:
            continue
        chunk.extend(_parse_range(range_part, total_pages))
    return chunk

def parse_page_ranges(range_string: str, total_pages: int, allow_duplicates: bool = True) -> list[list[int]]:
    chunks: list[list[int]] = []
    for range_group in range_string.split(';'):
        range_group = range_group.strip()
        if not range_group:
            continue
        if range_group.startswith('+'):
            if allow_duplicates:
                chunks.append(_parse_ranges_with_duplicates(range_group, total_pages))
            else:
                raise ValueError(_('Duplicates are not allowed'))
        else:
            chunks.append(_parse_ranges_without_duplicates(range_group, total_pages))
    return chunks

PageSegment = namedtuple('PageSegment', ['pdf_start', 'pdf_end', 'disp_type', 'disp_start'])

def parse_page_format(format_str: str, total_pages: int) -> list[PageSegment]:
    if not format_str:
        return [PageSegment(pdf_start=1, pdf_end=total_pages, disp_type='n', disp_start=1)]

    segments = []
    last_pdf_end = 0
    last_disp = 0

    for seg_str in format_str.split(';'):
        if not seg_str:
            continue
        if ':' in seg_str:
            parts = seg_str.split(':', 1)
            range_str = parts[0].strip()
            disp_str = parts[1].strip()
        else:
            range_str = seg_str.strip()
            disp_str = ''

        pdf_start = last_pdf_end + 1
        pdf_end = total_pages
        if range_str:
            if '-' not in range_str:
                pdf_start = int(range_str)
                pdf_end = pdf_start
            else:
                match = re.match(r'^(\d*)-(\d*)$', range_str)
                if not match:
                    raise ValueError(f'Invalid range: {range_str}')
                start_str, end_str = match.groups()
                if start_str:
                    pdf_start = int(start_str)
                if end_str:
                    pdf_end = int(end_str)

        if pdf_start > pdf_end or pdf_end > total_pages or pdf_start <= last_pdf_end:
            raise ValueError(f'Invalid or overlapping range: {pdf_start}-{pdf_end}')

        disp_type = 'n'
        disp_start = last_disp + 1
        if disp_str:
            if disp_str[0].isalpha() and disp_str[0] in 'nrRaA':
                disp_type = disp_str[0]
                disp_str = disp_str[1:]
            if disp_str:
                try:
                    disp_start = int(disp_str)
                except ValueError:
                    raise ValueError(f'Invalid start: {disp_str}')

        segments.append(PageSegment(pdf_start=pdf_start, pdf_end=pdf_end, disp_type=disp_type, disp_start=disp_start))
        page_count = pdf_end - pdf_start + 1
        last_disp = disp_start + page_count - 1
        last_pdf_end = pdf_end

    return segments


# ==========================================
# WORKERS
# ==========================================

# -- INVOICES --
A4_WIDTH, A4_HEIGHT = 595, 842
STANDARD_INVOICE_HEIGHT_MM = 140
STANDARD_INVOICE_HEIGHT_PTS = STANDARD_INVOICE_HEIGHT_MM * 2.83465
TOLERANCE = 10 

def _is_a4_size(rect: pymupdf.Rect) -> bool:
    is_a4_portrait = abs(rect.width - A4_WIDTH) <= TOLERANCE and abs(rect.height - A4_HEIGHT) <= TOLERANCE
    is_a4_landscape = abs(rect.width - A4_HEIGHT) <= TOLERANCE and abs(rect.height - A4_WIDTH) <= TOLERANCE
    return is_a4_portrait or is_a4_landscape

def _is_standard_invoice(doc: pymupdf.Document) -> bool:
    if len(doc) != 1:
        return False
    page = doc[0]
    is_a5_width = abs(page.rect.width - A4_WIDTH) <= TOLERANCE
    is_standard_height = abs(page.rect.height - STANDARD_INVOICE_HEIGHT_PTS) <= TOLERANCE
    return is_a5_width and is_standard_height

def merge_invoices_worker(invoice_pdf_paths: list[str], output_pdf_path: str, cancel_event, progress_queue, result_queue, saving_ack_event):
    """
    Worker function to merge disparate PDF invoices precisely fitting onto standard A4 layouts iteratively.
    """
    try:
        if not invoice_pdf_paths:
            raise ValueError(_('No invoice files provided.'))

        progress_queue.put(('INIT', len(invoice_pdf_paths)))
        standard_invoice_paths: list[str] = []
        other_invoice_paths: list[str] = []

        for i, pdf_path in enumerate(invoice_pdf_paths):
            if cancel_event.is_set():
                raise InterruptedError
            with pymupdf.open(pdf_path) as doc:
                if _is_standard_invoice(doc):
                    standard_invoice_paths.append(pdf_path)
                else:
                    other_invoice_paths.append(pdf_path)
            progress_queue.put(('PROGRESS', i + 1))

        with pymupdf.open() as final_doc:
            for i in range(0, len(standard_invoice_paths), 2):
                if cancel_event.is_set():
                    raise InterruptedError
                page = final_doc.new_page(width=A4_WIDTH, height=A4_HEIGHT)
                with pymupdf.open(standard_invoice_paths[i]) as doc1:
                    doc1.bake()
                    page.show_pdf_page(pymupdf.Rect(0, 0, A4_WIDTH, A4_HEIGHT / 2), doc1, 0)

                if i + 1 < len(standard_invoice_paths):
                    with pymupdf.open(standard_invoice_paths[i + 1]) as doc2:
                        doc2.bake()
                        page.show_pdf_page(pymupdf.Rect(0, A4_HEIGHT / 2, A4_WIDTH, A4_HEIGHT), doc2, 0)

            for pdf_path in other_invoice_paths:
                if cancel_event.is_set():
                    raise InterruptedError
                with pymupdf.open(pdf_path) as doc:
                    doc.bake()
                    for p_idx, p in enumerate(doc):
                        if _is_a4_size(p.rect):
                            final_doc.insert_pdf(doc, from_page=p_idx, to_page=p_idx)
                        else:
                            new_page = final_doc.new_page(width=A4_WIDTH, height=A4_HEIGHT)
                            new_page.show_pdf_page(pymupdf.Rect(0, 0, p.rect.width, p.rect.height), doc, p_idx)

            if cancel_event.is_set():
                raise InterruptedError

            progress_queue.put(('SAVING', _('Saving merged PDF...')))
            while not saving_ack_event.is_set():
                if cancel_event.is_set():
                    raise InterruptedError
                saving_ack_event.wait(timeout=0.1)

            final_doc.save(output_pdf_path, garbage=4, deflate=True)

        success_msg = _('Merged {} invoices.').format(len(invoice_pdf_paths))
        result_queue.put(('SUCCESS', success_msg))

    except InterruptedError:
        result_queue.put(('CANCEL', _('Cancelled by user.')))
    except Exception as e:
        result_queue.put(('ERROR', _('Unexpected error occurred. {}').format(e)))


# -- LONG IMAGE --
def pdf_to_long_image_worker(pdf_path, output_image_path, dpi_value, quality_value, cancel_event, progress_queue, result_queue, saving_ack_event):
    """
    Worker generating a singular long continuous scrollable image stitching all pages sequentially.
    """
    try:
        with pymupdf.open(pdf_path) as doc:
            total_pages = len(doc)
            if total_pages == 0:
                raise ValueError(_('PDF file has no pages.'))

            progress_queue.put(('INIT', total_pages + 1))
            page_images = []
            total_width = 0
            total_height = 0

            for i in range(total_pages):
                if cancel_event.is_set():
                    result_queue.put(('CANCEL', _('Cancelled by user.')))
                    return
                page = doc.load_page(i)
                pix = page.get_pixmap(dpi=dpi_value)
                img = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)

                page_images.append(img)
                total_width = max(total_width, img.width)
                total_height += img.height
                progress_queue.put(('PROGRESS', i + 1))

            if not page_images:
                raise ValueError(_('No pages were rendered from the PDF.'))

            long_image = Image.new('RGB', (total_width, total_height), (255, 255, 255))
            current_y = 0
            for img in page_images:
                long_image.paste(img, (0, current_y))
                current_y += img.height

            progress_queue.put(('SAVING', _('Saving long image...')))
            while not saving_ack_event.is_set():
                if cancel_event.is_set():
                    result_queue.put(('CANCEL', _('Cancelled by user.')))
                    return
                saving_ack_event.wait(timeout=0.1)

            long_image.save(output_image_path, quality=quality_value)
            progress_queue.put(('PROGRESS', total_pages + 1))

        success_msg = _('PDF converted to a long image.')
        result_queue.put(('SUCCESS', success_msg))
    except Exception as e:
        result_queue.put(('ERROR', _('Unexpected error occurred. {}').format(e)))


# -- INTERLEAVE --
def interleave_pdf_worker(pdf_path_a, pdf_path_b, output_pdf_path, reverse_b, cancel_event, progress_queue, result_queue, saving_ack_event):
    """
    Worker interleaving two disparate PDF documents natively alternating pages.
    """
    try:
        with pymupdf.open(pdf_path_a) as doc_a, pymupdf.open(pdf_path_b) as doc_b, pymupdf.open() as new_doc:
            len_a = len(doc_a)
            len_b = len(doc_b)
            total_pages_to_insert = len_a + len_b
            progress_queue.put(('INIT', total_pages_to_insert))

            if total_pages_to_insert == 0:
                raise ValueError(_('Input files are empty, no pages to merge.'))

            max_len = max(len_a, len_b)
            pages_processed = 0

            for i in range(max_len):
                if cancel_event.is_set():
                    result_queue.put(('CANCEL', _('Cancelled by user.')))
                    return

                if i < len_a:
                    new_doc.insert_pdf(doc_a, from_page=i, to_page=i)
                    pages_processed += 1

                if i < len_b:
                    page_b_index = (len_b - 1) - i if reverse_b else i
                    new_doc.insert_pdf(doc_b, from_page=page_b_index, to_page=page_b_index)
                    pages_processed += 1

                progress_queue.put(('PROGRESS', pages_processed))

            progress_queue.put(('SAVING', _('Saving PDF...')))
            while not saving_ack_event.is_set():
                if cancel_event.is_set():
                    result_queue.put(('CANCEL', _('Cancelled by user.')))
                    return
                saving_ack_event.wait(timeout=0.1)

            new_doc.save(output_pdf_path, garbage=4, deflate=True)

        success_msg = _('PDF interleaved.')
        result_queue.put(('SUCCESS', success_msg))
    except Exception as e:
        result_queue.put(('ERROR', _('Unexpected error occurred. {}').format(e)))


# -- PDF TO IMAGE --
def pdf_to_image_worker(input_files: list[str], output_dir: str, dpi_value: float, image_format: str, jpeg_quality: int, transparent_background: bool, save_in_same_folder: bool, cancel_event: Any, progress_queue: Any, result_queue: Any, saving_ack_event: Any) -> None:
    try:
        total_steps = 0
        for file_path in input_files:
            with pymupdf.open(file_path) as doc:
                total_steps += doc.page_count
        progress_queue.put(('INIT', total_steps))

        current_step = 0
        for file_path in input_files:
            if cancel_event.is_set():
                result_queue.put(('CANCEL', _('Cancelled by user.')))
                return

            pdf_path_obj = Path(file_path)
            pdf_name_only = pdf_path_obj.stem

            if save_in_same_folder:
                sub_output_dir = pdf_path_obj.parent / pdf_name_only
            else:
                sub_output_dir = Path(output_dir) / pdf_name_only

            sub_output_dir.mkdir(parents=True, exist_ok=True)

            with pymupdf.open(file_path) as doc:
                num_digits = len(str(doc.page_count))
                for i in range(doc.page_count):
                    if cancel_event.is_set():
                        result_queue.put(('CANCEL', _('Cancelled by user.')))
                        return

                    page = doc.load_page(i)
                    pix = page.get_pixmap(dpi=dpi_value, alpha=transparent_background)
                    page_num_str = str(i + 1).zfill(num_digits)
                    new_filename = f'{pdf_name_only}_page_{page_num_str}.{image_format}'
                    output_filename = sub_output_dir / new_filename

                    if image_format == 'jpg':
                        pix.save(str(output_filename), jpg_quality=jpeg_quality)
                    else:
                        pix.save(str(output_filename))

                    current_step += 1
                    progress_queue.put(('PROGRESS', current_step))

        success_msg = ngettext('Converted {} page to image.', 'Converted {} pages to images.', total_steps).format(total_steps)
        result_queue.put(('SUCCESS', success_msg))
    except Exception as e:
        result_queue.put(('ERROR', _('Unexpected error occurred. {}').format(e)))


# -- DELETE PAGES --
@lru_cache(maxsize=10)
def get_pdf_bytes_cached(pdf_path_str: str) -> bytes:
    with pymupdf.open(pdf_path_str) as doc:
        return doc.tobytes()

def delete_pages_worker(pdf_path: str, output_dir: str, pages_to_delete_str: str, cancel_event: Any, progress_queue: Any, result_queue: Any, saving_ack_event: Any) -> None:
    try:
        if not pages_to_delete_str:
            raise ValueError(_('No pages specified to delete.'))

        with pymupdf.open(pdf_path) as doc:
            total_pages_doc = len(doc)
            if total_pages_doc == 0:
                raise ValueError(_('PDF file has no pages.'))

            delete_groups = parse_page_ranges(pages_to_delete_str, total_pages_doc, allow_duplicates=False)

            if not delete_groups:
                raise ValueError(_("No valid pages could be parsed from '{pages_to_delete_str}'.").format(pages_to_delete_str=pages_to_delete_str))

            pdf_path_obj = Path(pdf_path)
            output_dir_obj = Path(output_dir)
            output_dir_obj.mkdir(parents=True, exist_ok=True)
            progress_queue.put(('INIT', len(delete_groups)))
            src_doc_bytes = get_pdf_bytes_cached(str(pdf_path))
            original_range_groups = [rg.strip() for rg in pages_to_delete_str.split(';') if rg.strip()]

            for i, pages_to_delete_list in enumerate(delete_groups):
                if cancel_event.is_set():
                    result_queue.put(('CANCEL', _('Cancelled by user.')))
                    return

                pages_to_delete_set = set(pages_to_delete_list)
                pages_to_keep = [p for p in range(total_pages_doc) if p not in pages_to_delete_set]
                if not pages_to_keep:
                    raise ValueError(_('Will delete all pages from {pdf_path_name} in group {group_num}.').format(pdf_path_name=pdf_path_obj.name, group_num=i + 1))

                with pymupdf.open(stream=src_doc_bytes, filetype='pdf') as new_doc:
                    new_doc.select(pages_to_keep)
                    output_name = ''
                    if i < len(original_range_groups):
                        range_str = original_range_groups[i].replace(':', 'S')
                        output_name = f'D{range_str}.pdf'
                    else:
                        output_name = f'D_group_{i + 1}.pdf'

                    output_file_path = output_dir_obj / output_name
                    new_doc.save(str(output_file_path), garbage=4, deflate=True)

                progress_queue.put(('PROGRESS', i + 1))

            success_msg = ngettext('Deleted pages in {} PDF file.', 'Deleted pages in {} PDF files.', len(delete_groups)).format(len(delete_groups))
            result_queue.put(('SUCCESS', success_msg))

    except Exception as e:
        result_queue.put(('ERROR', _('Unexpected error occurred. {}').format(e)))


# -- EXTRACT TEXT --
def extract_text_worker(input_files, output_dir, sort_text, save_in_same_folder, cancel_event, progress_queue, result_queue, saving_ack_event):
    """
    Worker parsing textual element blocks outputting flat textual streams iteratively.
    """
    try:
        total_steps = len(input_files)
        progress_queue.put(('INIT', total_steps))

        for i, file_path in enumerate(input_files):
            if cancel_event.is_set():
                result_queue.put(('CANCEL', _('Cancelled by user.')))
                return

            with pymupdf.open(file_path) as doc:
                text = ''
                for page in doc:
                    text += page.get_text(sort=sort_text)

                pdf_path_obj = Path(file_path)
                if save_in_same_folder:
                    output_path = pdf_path_obj.parent / f'{pdf_path_obj.stem}.txt'
                else:
                    output_path = Path(output_dir) / f'{pdf_path_obj.stem}.txt'
                output_path.write_text(text, encoding='utf-8')

            progress_queue.put(('PROGRESS', i + 1))

        success_msg = ngettext('Extracted text from {} file.', 'Extracted text from {} files.', total_steps).format(total_steps)
        result_queue.put(('SUCCESS', success_msg))

    except Exception as e:
        result_queue.put(('ERROR', _('Unexpected error occurred. {}').format(e)))


# -- EXTRACT IMAGES -- 
def extract_images_worker(input_files: list[str], output_dir: str, min_width: int, min_height: int, save_in_same_folder: bool, extract_all: bool, cancel_event: Any, progress_queue: Any, result_queue: Any, saving_ack_event: Any = None) -> None:
    try:
        total_images_found = 0
        images_extracted_count = 0

        for file_path in input_files:
            with pymupdf.open(file_path) as doc:
                total_images_found += sum(len(page.get_images(full=True)) for page in doc)

        progress_queue.put(('INIT', total_images_found))

        for file_path in input_files:
            if cancel_event.is_set():
                result_queue.put(('CANCEL', _('Cancelled by user.')))
                return

            pdf_path_obj = Path(file_path)
            if save_in_same_folder:
                output_subfolder = pdf_path_obj.parent / pdf_path_obj.stem
            else:
                output_subfolder = Path(output_dir) / pdf_path_obj.stem
            output_subfolder.mkdir(parents=True, exist_ok=True)

            with pymupdf.open(file_path) as doc:
                for page_num, page in enumerate(doc):
                    img_list = page.get_images(full=True)
                    for img_info in img_list:
                        xref = img_info[0]
                        w = img_info[2]
                        h = img_info[3]

                        if extract_all or (w >= min_width and h >= min_height):
                            img_dict = doc.extract_image(xref)
                            if not img_dict:
                                continue

                            img_bytes = img_dict['image']
                            img_ext = img_dict['ext']

                            img_filename = f'{pdf_path_obj.stem}_p{page_num + 1}_{xref}.{img_ext}'
                            img_path = output_subfolder / img_filename
                            img_path.write_bytes(img_bytes)
                            images_extracted_count += 1

                        progress_queue.put(('PROGRESS', images_extracted_count))

        success_msg = _('Found {} images, extracted {} images.').format(total_images_found, images_extracted_count)
        result_queue.put(('SUCCESS', success_msg))

    except Exception as e:
        result_queue.put(('ERROR', _('Unexpected error occurred. {}').format(e)))


# -- PAGE NUMBERS --
def to_roman(n, upper=True):
    """
    Converts numerical indexes into Roman Numerals computationally.
    """
    val = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
    syb_lower = ['m', 'cm', 'd', 'cd', 'c', 'xc', 'l', 'xl', 'x', 'ix', 'v', 'iv', 'i']
    syb_upper = [s.upper() for s in syb_lower]
    syb = syb_upper if upper else syb_lower
    roman_num = ''
    i = 0
    while n > 0:
        for _ in range(n // val[i]):
            roman_num += syb[i]
            n -= val[i]
        i += 1
    return roman_num

def to_alpha(n, upper=True):
    """
    Converts numerical references into alphabetical mapped encodings natively.
    """
    alpha_str = ''
    base = ord('A' if upper else 'a')
    while n > 0:
        n, rem = divmod(n - 1, 26)
        alpha_str = chr(base + rem) + alpha_str
    return alpha_str

def add_page_numbers_worker(input_path: str, output_path: str, rule: str, v_pos: str, h_pos: str, font_name: str, font_style: str, font_size: int, v_margin_cm: float, h_margin_cm: float, cancel_event: Any, progress_queue: Any, result_queue: Any, saving_ack_event: Any):
    """
    Worker printing precise coordinate mapped numerical sequences representing pages explicitly accurately.
    """
    try:
        CM_TO_POINTS = 72 / 2.54
        v_margin_points = v_margin_cm * CM_TO_POINTS
        h_margin_points = h_margin_cm * CM_TO_POINTS

        font_map = {
            ('Courier', 'Regular'): 'cour',
            ('Courier', 'Bold'): 'cobo',
            ('Courier', 'Italic'): 'coit',
            ('Courier', 'Bold Italic'): 'cobi',
            ('Times', 'Regular'): 'tiro',
            ('Times', 'Bold'): 'tibo',
            ('Times', 'Italic'): 'tiit',
            ('Times', 'Bold Italic'): 'tibi',
            ('Helvetica', 'Regular'): 'hero',
            ('Helvetica', 'Bold'): 'hebo',
            ('Helvetica', 'Italic'): 'heit',
            ('Helvetica', 'Bold Italic'): 'hebi',
        }
        fitz_font_name = font_map.get((font_name, font_style), 'tiro')
        font = pymupdf.Font(fitz_font_name)

        doc = pymupdf.open(input_path)
        total_pages = len(doc)
        progress_queue.put(('INIT', total_pages))

        segments = parse_page_format(rule, total_pages)
        page_text_map = {}
        for seg in segments:
            disp_num = seg.disp_start
            for page_num in range(seg.pdf_start, seg.pdf_end + 1):
                text = ''
                if seg.disp_type == 'n':
                    text = str(disp_num)
                elif seg.disp_type == 'r':
                    text = to_roman(disp_num, upper=False)
                elif seg.disp_type == 'R':
                    text = to_roman(disp_num, upper=True)
                elif seg.disp_type == 'a':
                    text = to_alpha(disp_num, upper=False)
                elif seg.disp_type == 'A':
                    text = to_alpha(disp_num, upper=True)
                page_text_map[page_num - 1] = text
                disp_num += 1

        for i, page in enumerate(doc):
            if cancel_event.is_set():
                result_queue.put(('CANCEL', 'Cancelled by user.'))
                return

            if i in page_text_map:
                text = page_text_map[i]
                page_rect = page.rect
                text_width = font.text_length(text, fontsize=font_size)
                
                if h_pos == 'left':
                    x = h_margin_points
                elif h_pos == 'right':
                    x = page_rect.width - text_width - h_margin_points
                elif h_pos == 'center':
                    x = (page_rect.width - text_width) / 2
                elif h_pos == 'outside':
                    x = h_margin_points if (i + 1) % 2 == 0 else page_rect.width - text_width - h_margin_points
                elif h_pos == 'inside':
                    x = page_rect.width - text_width - h_margin_points if (i + 1) % 2 == 0 else h_margin_points
                else:
                    x = (page_rect.width - text_width) / 2

                y = v_margin_points + font_size if v_pos == 'header' else page_rect.height - v_margin_points
                page.insert_text((x, y), text, fontname=fitz_font_name, fontsize=font_size)

            progress_queue.put(('PROGRESS', i + 1))

        progress_queue.put(('SAVING', 'Saving PDF...'))
        saving_ack_event.wait()
        doc.save(output_path, garbage=4, deflate=True)
        doc.close()
        result_queue.put(('SUCCESS', 'Page numbers added successfully.'))

    except Exception as e:
        import traceback
        traceback.print_exc()
        result_queue.put(('ERROR', str(e)))
