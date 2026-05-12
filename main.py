"""
Author: RajarshiB
AI-Agent: Gemini

Purpose: Main entry point for PdfBreeze. Orchestrates UI components, drag-n-drop loading, state events, and execution mapped to `logic_bridge`.
"""
import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QPushButton, QStatusBar, QMessageBox,
    QGroupBox, QFileDialog, QInputDialog, QScrollArea, QFrame,
    QProgressDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import logic_bridge
from ui_elements import FileOrderWidget, get_dark_stylesheet

class WorkerThread(QThread):
    finished = pyqtSignal(bool, str, str) # success, error_type, error_msg

    def __init__(self, logic_call, *args):
        super().__init__()
        self.logic_call = logic_call
        self.args = args

    def run(self):
        try:
            self.logic_call(*self.args)
            self.finished.emit(True, "", "")
        except Exception as e:
            self.finished.emit(False, type(e).__name__, str(e))


class PdfBreezeMainWindow(QMainWindow):
    """
    Main controller encompassing application visual space mapping event clicks to PDF logic.
    """
    def __init__(self):
        """
                Initializes the PdfBreeze main window layout mapping visual inputs efficiently.
                """
        super().__init__()
        self.setWindowTitle("PdfBreeze")
        self.resize(1000, 700)
        
        self.setStyleSheet(get_dark_stylesheet())
        
        # List initialization targeting draggable paths
        self.file_list = FileOrderWidget()
        self.setAcceptDrops(True)
        
        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        
        left_side_widget = QWidget()
        left_layout = QVBoxLayout(left_side_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        self.btn_browse = QPushButton("Browse Files...")
        self.btn_browse.setMinimumHeight(40)
        self.btn_browse.setStyleSheet("background-color: #2980b9; color: white; border-radius: 5px; font-weight: bold; font-size: 14px;")
        
        left_layout.addWidget(self.btn_browse)
        left_layout.addWidget(self.file_list)
        
        main_layout.addWidget(left_side_widget, stretch=2)
        
        sidebar_widget = QWidget()
        sidebar = QVBoxLayout(sidebar_widget)
        
        # Category Modules corresponding to prompt mandates
        
        # 1. Layout Phase Menu
        grp_layout = QGroupBox("Layout Phase")
        layout_layout = QVBoxLayout(grp_layout)
        self.btn_reorder = self._add_action(layout_layout, "Reorder", "Visually drag and drop PDF pages to rearrange their structural sequence directly.")
        self.btn_merge = self._add_action(layout_layout, "Merge PDFs", "Combines multiple disparate PDFs sequentially into one singular continuous document.")
        self.btn_split = self._add_action(layout_layout, "Split PDF", "Isolates and physically extracts every page into its own individual PDF native stream.")
        self.btn_interleave = self._add_action(layout_layout, "Interleave", "Takes exactly two PDFs (like front and back scans) and merges them physically by alternating pages 1-by-1.")
        self.btn_booklet = self._add_action(layout_layout, "2-up Booklet", "Geometrically arranges flat documents into a folded layout suitable for physical double-sided booklet printing.")

        # 2. Visual Phase Menu
        grp_visual = QGroupBox("Visual Phase")
        layout_visual = QVBoxLayout(grp_visual)
        self.btn_img2pdf = self._add_action(layout_visual, "Images to PDF", "Compiles a sequential stream of local Images into standard A4 PDF documents securely scaled.")
        self.btn_pdf2img = self._add_action(layout_visual, "PDF to Images", "Rasterizes every PDF page returning high-quality independent JPEG/PNG frames perfectly isolated.")
        self.btn_long_img = self._add_action(layout_visual, "PDF to Long Image", "Stitches entire sequential PDF layouts vertically mapping a single continuous panoramic image natively.")
        self.btn_rotate = self._add_action(layout_visual, "Rotate", "Performs lossless geometric clockwise rotation permanently cementing the native angle directly.")
        self.btn_crop = self._add_action(layout_visual, "Crop", "Shrinks bounding view boxes physically isolating visible geometries based upon explicit margin vectors.")

        # 3. Content Phase Menu
        grp_content = QGroupBox("Content Phase")
        layout_content = QVBoxLayout(grp_content)
        self.btn_extract_text = self._add_action(layout_content, "Extract Text", "Transcribes internally registered readable text structures directly out spanning directories.")
        self.btn_extract_img = self._add_action(layout_content, "Extract Images", "Rips out native embedded graphical objects (vectors/images) discarding geometric text mappings.")
        self.btn_extract_annot = self._add_action(layout_content, "Extract Annotated Pages", "Explicitly extracts only the pages in the document specifically flagged with user marks or highlights.")
        self.btn_delete_pages = self._add_action(layout_content, "Delete Pages", "Permits selecting specific page constraints bypassing them natively truncating the sequence selectively.")
        self.btn_page_num = self._add_action(layout_content, "Page Numbers", "Injects permanent numerical sequence signatures targeting explicit layout placements natively.")

        # 4. System Phase Menu
        grp_system = QGroupBox("System Phase")
        layout_system = QVBoxLayout(grp_system)
        self.btn_compress = self._add_action(layout_system, "Compress PDF", "Tiered compression engine: 'Basic' sweeps unused internal PDF mappings safely. 'Intermediate' scales images down internally by 25%. 'Best Possible' physically crushes imagery down by 50% applying aggressive JPEG re-encoding bounds ensuring drastic disk improvements.")
        self.btn_passwords = self._add_action(layout_system, "Passwords (Security)", "Secures local metadata mathematically enforcing explicit AES password boundaries securely.")
        self.btn_metadata = self._add_action(layout_system, "Metadata", "Injects or sanitizes inherent dictionary bindings associating invisible system tags explicitly.")
        self.btn_invoices = self._add_action(layout_system, "Merge Invoices", "Specifically organizes localized A5 receipts packing them intelligently onto A4 physical constraints securely side-by-side.")
        self.btn_sign = self._add_action(layout_system, "Cryptographic Sign", "Cryptographically seals the identity constraint mapping a secure PFX native certificate verifying explicit tampering routines.")
        self.btn_watermark = self._add_action(layout_system, "Watermark PDF", "Applies visibly mapped overlays ensuring ownership constraints are visibly stamped mathematically rendering opacity limits natively.")

        sidebar.addWidget(grp_layout)
        sidebar.addWidget(grp_visual)
        sidebar.addWidget(grp_content)
        sidebar.addWidget(grp_system)
        sidebar.addStretch()
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(sidebar_widget)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        main_layout.addWidget(scroll_area, stretch=1)
        self.setCentralWidget(central_widget)
        
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready. Drop files anywhere.")
        
        # Map signals to logic execution
        self._map_signals()
        self._setup_ui()

    def _add_action(self, layout, title, help_text):

        """

                Internal standard _add_action properly executing structural logic gracefully.

                """
        row = QWidget()
        h_layout = QHBoxLayout(row)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(5)
        
        btn = QPushButton(title)
        info = QPushButton("i")
        info.setFixedSize(24, 24)
        info.setStyleSheet("border-radius: 12px; font-weight: bold; font-family: serif; background-color: #2980b9; color: white;")
        info.setToolTip("Click to learn more")
        info.clicked.connect(lambda _, t=title, ht=help_text: QMessageBox.information(self, f"{t} Feature Documentation", ht))
        
        h_layout.addWidget(btn, stretch=1)
        h_layout.addWidget(info)
        layout.addWidget(row)
        return btn

    def _setup_ui(self):
        """ Injects explicit attributes pointing to original developers/repos per specifications """
        menu = self.menuBar()
        help_menu = menu.addMenu("Help")
        about_action = help_menu.addAction("About PdfBreeze")
        about_action.triggered.connect(self.show_about)

    def _map_signals(self):

        """

                Internal standard _map_signals properly executing structural logic gracefully.

                """
        self.btn_merge.clicked.connect(self.action_merge)
        self.btn_split.clicked.connect(self.action_split)
        self.btn_interleave.clicked.connect(self.action_interleave)
        self.btn_booklet.clicked.connect(self.action_booklet)
        self.btn_img2pdf.clicked.connect(self.action_img_to_pdf)
        self.btn_pdf2img.clicked.connect(self.action_pdf_to_img)
        self.btn_long_img.clicked.connect(self.action_long_img)
        self.btn_passwords.clicked.connect(self.action_security)
        self.btn_compress.clicked.connect(self.action_compress)
        self.btn_metadata.clicked.connect(self.action_metadata)

        # Connect the remaining hooks to dynamic controller logics generating visual popups and standard dialogs
        self.btn_reorder.clicked.connect(self.action_reorder)
        self.btn_rotate.clicked.connect(self.action_rotate)
        self.btn_crop.clicked.connect(self.action_crop)
        self.btn_extract_text.clicked.connect(self.action_extract_text)
        self.btn_extract_img.clicked.connect(self.action_extract_img)
        self.btn_extract_annot.clicked.connect(self.action_extract_annot)
        self.btn_delete_pages.clicked.connect(self.action_delete_pages)
        self.btn_page_num.clicked.connect(self.action_page_num)
        self.btn_invoices.clicked.connect(self.action_invoices)
        self.btn_sign.clicked.connect(self.action_sign)
        self.btn_watermark.clicked.connect(self.action_watermark)
        
        # Connect Browse button
        self.btn_browse.clicked.connect(self.action_browse)

    def action_browse(self):
        """ Allow users to select multiple items bypassing drag/drop limitation if needed """
        files, _ = QFileDialog.getOpenFileNames(self, "Select Files", "", "Supported Files (*.pdf *.png *.jpg *.jpeg)")
        if files:
            for filepath in files:
                filename = os.path.basename(filepath)
                self.file_list.add_custom_item(filename, filepath)
            self.status_bar.showMessage(f"Sequence contains {self.file_list.count()} loaded operations.")

    def _get_single_active_file(self):

        """

                Internal standard _get_single_active_file properly executing structural logic gracefully.

                """
        paths = self._get_ordered_paths()
        if not self._ensure_files_present(paths): return None
        if len(paths) > 1:
            QMessageBox.warning(self, "Invalid Selection", "Operation is restricted to evaluating a single file context. Remove others from Queue.")
            return None
        return paths[0]

    def action_reorder(self):

        """

                Handles reorder workflow passing bounds mapping logic directly.

                """
        file_path = self._get_single_active_file()
        if not file_path: return
        from ui_elements import PDFPageViewerDialog
        dlg = PDFPageViewerDialog(file_path, self, is_reorder=True)
        if dlg.exec():
            seq = dlg.get_result()
            save_path, _ = QFileDialog.getSaveFileName(self, "Save Reordered PDF", "", "PDF Files (*.pdf)")
            if save_path:
                self._execute_with_safety(logic_bridge.visual_reorder, file_path, save_path, seq)

    def action_delete_pages(self):

        """

                Handles delete_pages workflow passing bounds mapping logic directly.

                """
        file_path = self._get_single_active_file()
        if not file_path: return
        from ui_elements import PDFPageViewerDialog
        dlg = PDFPageViewerDialog(file_path, self, is_reorder=False)
        if dlg.exec():
            indices = dlg.get_result()
            if not indices: return
            save_dir = QFileDialog.getExistingDirectory(self, "Select Save Directory")
            if save_dir:
                self._execute_with_safety(logic_bridge.delete_pages, file_path, save_dir, indices)

    def action_rotate(self):

        """

                Handles rotate workflow passing bounds mapping logic directly.

                """
        file_path = self._get_single_active_file()
        if not file_path: return
        from ui_elements import RotateDialog
        dlg = RotateDialog(self)
        if dlg.exec():
            save_path, _ = QFileDialog.getSaveFileName(self, "Save Rotated PDF", "", "PDF Files (*.pdf)")
            if save_path:
                self._execute_with_safety(logic_bridge.pypdf_transform, file_path, save_path, 'rotate', dlg.get_angle())

    def action_crop(self):

        """

                Handles crop workflow passing bounds mapping logic directly.

                """
        file_path = self._get_single_active_file()
        if not file_path: return
        from ui_elements import CropDialog
        dlg = CropDialog(self)
        if dlg.exec():
            margins = dlg.get_margins()
            save_path, _ = QFileDialog.getSaveFileName(self, "Save Cropped PDF", "", "PDF Files (*.pdf)")
            if save_path:
                self._execute_with_safety(logic_bridge.pypdf_transform, file_path, save_path, 'crop', *margins)

    def action_page_num(self):

        """

                Handles page_num workflow passing bounds mapping logic directly.

                """
        file_path = self._get_single_active_file()
        if not file_path: return
        from ui_elements import PageNumberDialog
        dlg = PageNumberDialog(self)
        if dlg.exec():
            start, h, v = dlg.get_settings()
            save_path, _ = QFileDialog.getSaveFileName(self, "Save Paginated PDF", "", "PDF Files (*.pdf)")
            if save_path:
                self._execute_with_safety(logic_bridge.append_page_numbers, file_path, save_path, start, h, v)

    def action_extract_text(self):

        """

                Handles extract_text workflow passing bounds mapping logic directly.

                """
        file_path = self._get_single_active_file()
        if not file_path: return
        save_dir = QFileDialog.getExistingDirectory(self, "Select Save Directory")
        if save_dir:
            self._execute_with_safety(logic_bridge.extract_data_or_images, file_path, save_dir, "text")

    def action_extract_img(self):

        """

                Handles extract_img workflow passing bounds mapping logic directly.

                """
        file_path = self._get_single_active_file()
        if not file_path: return
        save_dir = QFileDialog.getExistingDirectory(self, "Select Save Directory")
        if save_dir:
            self._execute_with_safety(logic_bridge.extract_data_or_images, file_path, save_dir, "images")

    def action_extract_annot(self):

        """

                Handles extract_annot workflow passing bounds mapping logic directly.

                """
        file_path = self._get_single_active_file()
        if not file_path: return
        save_path, _ = QFileDialog.getSaveFileName(self, "Save Annotated Pages PDF", "", "PDF Files (*.pdf)")
        if save_path:
            self._execute_with_safety(logic_bridge.extract_annotated, file_path, save_path)

    def action_invoices(self):

        """

                Handles invoices workflow passing bounds mapping logic directly.

                """
        files = self._get_ordered_paths()
        if not files: return
        save_path, _ = QFileDialog.getSaveFileName(self, "Save Merged Invoices PDF", "", "PDF Files (*.pdf)")
        if save_path:
            self._execute_with_safety(logic_bridge.merge_invoices, files, save_path)
            
    def action_sign(self):
            
        """
            
                Handles sign workflow passing bounds mapping logic directly.
            
                """
        file_path = self._get_single_active_file()
        if not file_path: return
        pfx_path, _ = QFileDialog.getOpenFileName(self, "Select PKCS12 Certificate", "", "Certificates (*.pfx *.p12)")
        if not pfx_path: return
        pwd, ok = QInputDialog.getText(self, "Certificate Password", "Enter password for certificate:", QLineEdit.EchoMode.Password)
        if not ok or not pwd: return
        
        save_path, _ = QFileDialog.getSaveFileName(self, "Save Signed PDF", "", "PDF Files (*.pdf)")
        if save_path:
            self._execute_with_safety(logic_bridge.digital_sign_pdf, file_path, save_path, pfx_path, pwd)
            
    def action_watermark(self):
            
        """
            
                Handles watermark workflow passing bounds mapping logic directly.
            
                """
        file_path = self._get_single_active_file()
        if not file_path: return
        from ui_elements import WatermarkDialog
        dlg = WatermarkDialog(file_path, self)
        if dlg.exec():
            data = dlg.get_watermark_data()
            if not data: return
            save_path, _ = QFileDialog.getSaveFileName(self, "Save Watermarked PDF", "", "PDF Files (*.pdf)")
            if save_path:
                self._execute_with_safety(logic_bridge.add_watermark, file_path, save_path, data, success_msg="Watermark structurally applied.")
                
    def dragEnterEvent(self, event):
        """ Signals dropping acceptance if files encompass active URI protocols """
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        """ Rips standard Windows/mac folder drops directly converting item streams """
        for url in event.mimeData().urls():
            filepath = url.toLocalFile()
            ext = os.path.splitext(filepath)[1].lower()
            if ext in ['.pdf', '.png', '.jpg', '.jpeg']:
                filename = os.path.basename(filepath)
                self.file_list.add_custom_item(filename, filepath)
        
        self.status_bar.showMessage(f"Sequence contains {self.file_list.count()} loaded operations.")

    def _get_ordered_paths(self):
        """ Fetches top-down hierarchy arrays targeting sequential items mapped in QListWidget """
        paths = []
        for index in range(self.file_list.count()):
            item = self.file_list.item(index)
            paths.append(item.data(Qt.ItemDataRole.UserRole))
        return paths

    # ===============================================
    # Validaton Constraints Engine (Edge Cases Phase 2)
    # ===============================================

    def _ensure_files_present(self, paths):

        """

                Internal validation explicitly executing validation securely natively.

                """
        if not paths:
            QMessageBox.warning(self, "No files", "Please add files to the queue.")
            return False
        return True

    def _block_mixed_format(self, paths):
        """ 1. Mixed Format Blocking """
        has_pdfs = any(p.lower().endswith('.pdf') for p in paths)
        has_imgs = any(p.lower().endswith(('.png', '.jpg', '.jpeg')) for p in paths)
        if has_pdfs and has_imgs:
            QMessageBox.critical(self, "Mixed Format Error", "Cannot mix Images and PDFs in this operation.\nPlease run 'Split PDF to Images' resolving formats prior to unifying them all.")
            return False
        return True

    def _block_interleave_restriction(self, paths):
        """ 2. Interleave Restriction """
        if len(paths) != 2:
            QMessageBox.critical(self, "Interleave Constraint", "Interleave requires exactly TWO documents.")
            return False
        if not all(p.lower().endswith('.pdf') for p in paths):
            QMessageBox.critical(self, "Interleave Constraint", "Interleave inherently requires exactly TWO distinct PDFs.")
            return False
        return True

    def _get_single_file_target(self, paths):
        """ 3. Single File Focus Constraints """
        if len(paths) > 1:
            QMessageBox.warning(self, "Single File Limitation", "This action logically enforces singular mutations. Only the *first* file located at index zero will be processed.")
        return paths[0] if paths else None

    def _ensure_image_exclusivity(self, paths):
        """ 4. Image Exclusivity """
        if any(p.lower().endswith('.pdf') for p in paths):
            QMessageBox.critical(self, "Image Exclusivity", "This action strictly relies on images. PDF extensions pollute the list queue.")
            return False
        return True

    def _ensure_pdf_exclusivity(self, paths):
        """ 5. PDF Exclusivity """
        if any(not p.lower().endswith('.pdf') for p in paths):
            QMessageBox.critical(self, "PDF Exclusivity", "Cannot operate with image structures. Queue must be exclusively PDFs without conversion tracking.")
            return False
        return True

    def _execute_with_safety(self, logic_call, *args, success_msg="Saved successfully"):
        """ 6. File Accessibility Error Locking & Async Execution """
        self.progress_dialog = QProgressDialog("Processing PDF...", None, 0, 0, self)
        self.progress_dialog.setWindowTitle("Please Wait")
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setCancelButton(None)
        self.progress_dialog.show()

        self.worker = WorkerThread(logic_call, *args)
        
        def on_finished(success, error_type, error_msg):
            self.progress_dialog.close()
            if success:
                if success_msg:
                    QMessageBox.information(self, "Success", success_msg)
            else:
                if error_type == "FileNotFoundError":
                    QMessageBox.critical(self, "File Accessibility Trap", f"File disappeared post-dropping! {error_msg}")
                elif "PdfReadError" in error_type:
                    QMessageBox.critical(self, "Accessibility Limit", f"Failed reading PDF structure gracefully: {error_msg}")
                else:
                    QMessageBox.critical(self, "Logic Execution Error", f"Failed to execute pipeline: {error_msg}")

        self.worker.finished.connect(on_finished)
        self.worker.start()
        return True

    # ===============================================
    # Orchestrator Actions (Logic Mappings)
    # ===============================================

    def action_merge(self):

        """

                Handles merge workflow passing bounds mapping logic directly.

                """
        paths = self._get_ordered_paths()
        if not self._ensure_files_present(paths): return
        if not self._block_mixed_format(paths): return
        if not self._ensure_pdf_exclusivity(paths): return
            
        save_path, _ = QFileDialog.getSaveFileName(self, "Save Merged Result", "", "PDF Files (*.pdf)")
        if save_path:
            self._execute_with_safety(logic_bridge.pypdf_merge, paths, save_path, success_msg=f"Merged successfully into {save_path}")

    def action_split(self):

        """

                Handles split workflow passing bounds mapping logic directly.

                """
        paths = self._get_ordered_paths()
        if not self._ensure_files_present(paths): return
        if not self._ensure_pdf_exclusivity(paths): return
        target_file = self._get_single_file_target(paths)
        
        save_dir = QFileDialog.getExistingDirectory(self, "Select Split Output Directory")
        if save_dir:
            self._execute_with_safety(logic_bridge.pypdf_split, target_file, save_dir, success_msg=f"PDF pages dumped into {save_dir}")

    def action_interleave(self):

        """

                Handles interleave workflow passing bounds mapping logic directly.

                """
        paths = self._get_ordered_paths()
        if not self._ensure_files_present(paths): return
        if not self._block_interleave_restriction(paths): return
        
        save_path, _ = QFileDialog.getSaveFileName(self, "Save Interleaved Result", "", "PDF Files (*.pdf)")
        if save_path:
            self._execute_with_safety(logic_bridge.interleave_pdfs, paths[0], paths[1], save_path, success_msg=f"Interleaved structure saved to {save_path}")

    def action_booklet(self):

        """

                Handles booklet workflow passing bounds mapping logic directly.

                """
        paths = self._get_ordered_paths()
        if not self._ensure_files_present(paths): return
        target_file = self._get_single_file_target(paths)
        
        save_path, _ = QFileDialog.getSaveFileName(self, "Save Booklet Layout", "", "PDF Files (*.pdf)")
        if save_path:
            self._execute_with_safety(logic_bridge.make_booklet, target_file, save_path, success_msg="Booklet formatted completely.")

    def action_img_to_pdf(self):

        """

                Handles img_to_pdf workflow passing bounds mapping logic directly.

                """
        paths = self._get_ordered_paths()
        if not self._ensure_files_present(paths): return
        if not self._block_mixed_format(paths): return
        if not self._ensure_image_exclusivity(paths): return
        
        save_path, _ = QFileDialog.getSaveFileName(self, "Save Output", "", "PDF Files (*.pdf)")
        if save_path:
            self._execute_with_safety(logic_bridge.images_to_pdf, paths, save_path, success_msg="Converted images effectively to A4 layout.")

    def action_pdf_to_img(self):

        """

                Handles pdf_to_img workflow passing bounds mapping logic directly.

                """
        paths = self._get_ordered_paths()
        if not self._ensure_files_present(paths): return
        target_file = self._get_single_file_target(paths)
        if not target_file.lower().endswith('.pdf'):
            QMessageBox.warning(self, "Invalid Selection", "Must select a PDF.")
            return

        save_dir = QFileDialog.getExistingDirectory(self, "Select Extract Directory")
        if save_dir:
            self._execute_with_safety(logic_bridge.pdf_to_images, target_file, save_dir, success_msg="Images rasterized reliably.")

    def action_long_img(self):

        """

                Handles long_img workflow passing bounds mapping logic directly.

                """
        paths = self._get_ordered_paths()
        if not self._ensure_files_present(paths): return
        target_file = self._get_single_file_target(paths)

        save_path, _ = QFileDialog.getSaveFileName(self, "Save Long Image", "", "Image Files (*.png)")
        if save_path:
            self._execute_with_safety(logic_bridge.pdf_to_long_image, target_file, save_path, success_msg="Horizontal bounds wrapped structurally into endless vertical sheet.")

    def action_security(self):

        """

                Handles security workflow passing bounds mapping logic directly.

                """
        paths = self._get_ordered_paths()
        if not self._ensure_files_present(paths): return
        target_file = self._get_single_file_target(paths)
        
        pwd, ok = QInputDialog.getText(self, "PDF Security Password", "Enter AES Password mapping:")
        if ok and pwd:
            save_path, _ = QFileDialog.getSaveFileName(self, "Save Encrypted PDF", "", "PDF Files (*.pdf)")
            if save_path:
                self._execute_with_safety(logic_bridge.pypdf_encrypt, target_file, save_path, pwd, success_msg="AES boundaries successfully integrated locally.")

    def action_compress(self):

        """

                Handles compress workflow passing bounds mapping logic directly.

                """
        paths = self._get_ordered_paths()
        if not self._ensure_files_present(paths): return
        target_file = self._get_single_file_target(paths)
        
        levels = ["Basic", "Intermediate", "Best Possible"]
        level, ok = QInputDialog.getItem(self, "Compression Level", "Select compression tier:", levels, 0, False)
        if not ok or not level: return

        save_path, _ = QFileDialog.getSaveFileName(self, "Save Compressed PDF", "", "PDF Files (*.pdf)")
        if save_path:
            self._execute_with_safety(logic_bridge.compress_pdf, target_file, save_path, level, success_msg=f"Compression ({level}) completed securely.")

    def action_metadata(self):

        """

                Handles metadata workflow passing bounds mapping logic directly.

                """
        paths = self._get_ordered_paths()
        if not self._ensure_files_present(paths): return
        target_file = self._get_single_file_target(paths)
        
        meta, ok = QInputDialog.getText(self, "Custom Metadata", "Format as 'Key=Value' pairings:")
        if ok and meta:
            save_path, _ = QFileDialog.getSaveFileName(self, "Save Out PDF", "", "PDF Files (*.pdf)")
            if save_path:
                self._execute_with_safety(logic_bridge.set_metadata, target_file, save_path, {'custom_field': meta}, success_msg="Applied custom metadata bindings comprehensively.")

    def show_about(self):
        """ Renders strictly mandated attribution dialog ensuring compliance with specification constraints """
        text = (
            "PdfBreeze - Advanced Desktop Unified Integration Interface\n\n"
            "Credits and Functional Attribution:\n"
            "1. pypdf - Core PDF sequence merging operations\n"
            "2. pdfarranger - Core visualization abstractions & Drag Drop mechanics\n"
            "3. pdfly - Embedded extraction constraints\n"
            "4. PDFeXpress - Toolkit structural dependencies\n"
            "\nUI orchestrated via dynamic PyQt6 mappings."
        )
        QMessageBox.about(self, "About System", text)

if __name__ == '__main__':
    # Initialize unified framework loop
    app = QApplication(sys.argv)
    window = PdfBreezeMainWindow()
    window.show()
    sys.exit(app.exec())
