# Why PdfBreeze?
For personal use, pdf merging, splitting and other operations I have been using smallpdf.com, ilovepdf.com etc. I didn't like the idea of uploading my pdfs to the internet. So I thought of building a desktop GUI application that can do all these operations locally. This is particularly easy when others have already written code for most of these operations, and when I have access to AI agents to help me do most/all of the coding by just guiding and inspecting on a high level. In making this, I made specification files detailing which python libraries to use, which features to build on top(not from scratch) of, and other instructions to be as precise as possible for the AI agents to understand and implement. Initially I thought of the way of operation will be to just clone the repos and the the logic_brdidge will fetch and adapt functions already built. But making it standalone and using standard python pdf packages directly was a better idea was very close so on _dependency.py files are kept. Cloning enitre repositotires will be bloat.

PdfBreeze is built with PyQt6 that provides a unified graphical interface for various PDF manipulation tasks. It combines features originally found in command-line tools such as `PDFeXpress`, `pdfly`, and `pdfarranger` into a single, easy-to-use application. 

The program runs fully locally and securely without relying on external repository cloning. It utilizes direct integration scripts dependent entirely on standard Python PDF packages (`pypdf`, `PyMuPDF`, and `Pillow`).

It esentially solved my problem, if it solves others' problems, I would be happy.


## Screenshots

*Place screenshot of Main App Front here*
`![Main App Front](images/main_app_screenshot.png)`

*Place screenshot of Reordering Pages here*
`![Reordering Pages](images/reorder_screenshot.png)`

*Place screenshot of Deleting Pages here*
`![Deleting Pages](images/delete_screenshot.png)`

*Place screenshot of Watermark Editor here*
`![Watermark Editor](images/watermark_screenshot.png)`

## Project Structure

* `main.py`: The main graphical user interface and central application controller.
* `ui_elements.py`: Custom Qt widgets containing styling, drag-and-drop lists, and graphical dialogue tools.
* `logic_bridge.py`: An adapter that directs the UI's inputs toward the corresponding PDF function.
* `PDFeXpress_dependency.py`: Contains functions adapted directly from the PDFeXpress repository.
* `pdfly_dependency.py`: Contains functions adapted from the pdfly repository.
* `pdfarranger_dependency.py`: Structure stub for pdfarranger logic.
* `test_logic.py`: A runtime testing script verifying core PDF features.
* `example/`: Containing sample layout PDFs designated for tests.
* `requirements.txt`: Python package requirements.

## Features Overview

Below is the breakdown of internal operations and their origins:

### 1. Adapted from PDFeXpress
* **Merge Invoices**: Arranges smaller A5 size pages and tightly packs them side-by-side onto standard A4 pages.
* **PDF to Long Image**: Connects pages vertically to create a singular long continuous image document.
* **Interleave PDFs**: Combines two PDFs by alternating one page from each side (1A, 1B, 2A, 2B), commonly used for merging duplex scans.
* **Delete Pages**: Deletes specific pages either via visual selection or by explicitly defining sequence numbers.
* **PDF to Images**: Extracts and converts each page into standalone images (PNG/JPEG).
* **Extract Text & Extract Images**: Bulk strips the internal text or graphic assets out of documents natively.

### 2. Adapted from pdfly 
* **2-up Booklet**: Reorganizes individual PDF pages into a layout ready to be folded into a readable physical booklet.
* **Extract Annotated Pages**: Automatically detects and extracts only the pages that contain user annotations or flags.
* **Compress PDF**: Custom three-tiered compression script ranging from "Basic" structure cleanups, to "Intermediate" and "Best Possible" compression which directly unmaps embedded images, dramatically reduces their size via PIL, and inserts them back.

### 3. Built Extensively via Core pypdf / PyMuPDF 
* **Visual Reorder**: Graphically shift and sequence individual PDF thumbnails by dragging and dropping them natively.
* **Rotate & Crop**: Visually adjusts viewing structures, cropping boundaries natively in points.
* **Watermark PDF**: A modern interface for positioning, adding, and customizing transparent PNGs or Text strings atop an entire PDF sequence. Easily change their angle, opacity and scale using simple sliders.

## Installation and Execution

To safely run this application via Anaconda/Miniconda:

1. Create and activate a clean conda environment:
```bash
conda create -n pdfbreeze_env python=3.10 -y
conda activate pdfbreeze_env
```

2. Install the necessary dependencies via pip:
```bash
pip install -r requirements.txt
```

3. Launch the central user interface:
```bash
python main.py
```
