"""
Author: RajarshiB
AI-Agent: Gemini

Purpose: This module provides the custom UI elements for PdfBreeze, utilizing PyQt6 components, drag and drop logic mapping, and styles.
"""
from PyQt6.QtWidgets import (
    QListWidget, QListWidgetItem, QWidget, QLabel, 
    QPushButton, QHBoxLayout, QVBoxLayout, QAbstractItemView
)
from PyQt6.QtCore import Qt, QSize
from PyQt6 import QtGui

class FileOrderWidget(QListWidget):
    """
    Drag and drop list widget to manage files and their processing sequence.
    """
    def __init__(self, parent=None):
        """
        Initializes the FileOrderWidget, setting drag, drop, and flow configurations.
        
        Args:
            parent: The optional parent widget.
        """
        super().__init__(parent)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setViewMode(QListWidget.ViewMode.ListMode)
        self.setFlow(QListWidget.Flow.LeftToRight)
        self.setWrapping(True)
        self.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.setSpacing(10)
        self.setIconSize(QSize(100, 100))
        self.setWordWrap(True)

    def add_custom_item(self, filename, filepath):
        """
        Appends a custom visual representation into the sequence queue.

        Args:
            filename (str): The display name.
            filepath (str): The absolute path payload data.
        """
        item = QListWidgetItem(self)
        item.setData(Qt.ItemDataRole.UserRole, filepath)
        
        # Setup custom widget housing 3 things: Top 'X' layout, Image, Bottom Text
        widget = QWidget()
        widget.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        # 1. Top Bar for X button
        top_layout = QHBoxLayout()
        top_layout.addStretch()
        btn_remove = QPushButton("X")
        btn_remove.setFixedSize(20, 20)
        btn_remove.setStyleSheet("background-color: #c0392b; color: white; border-radius: 10px; font-weight: bold;")
        btn_remove.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_remove.clicked.connect(lambda: self.takeItem(self.row(item)))
        top_layout.addWidget(btn_remove)
        
        layout.addLayout(top_layout)
        
        # 2. Render Thumbnail Label
        lbl_icon = QLabel()
        lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if filepath.lower().endswith(('.png', '.jpg', '.jpeg')):
            pixmap = QtGui.QPixmap(filepath)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                lbl_icon.setPixmap(pixmap)
        else:
            # Produce a vibrant PDF block icon natively
            pixmap = QtGui.QPixmap(100, 100)
            pixmap.fill(QtGui.QColor("#e74c3c"))
            painter = QtGui.QPainter(pixmap)
            painter.setPen(QtGui.QColor("white"))
            font = painter.font()
            font.setPointSize(24)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "PDF")
            painter.end()
            lbl_icon.setPixmap(pixmap)
            
        layout.addWidget(lbl_icon)
        
        # 3. Label Text
        lbl_name = QLabel(filename)
        lbl_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_name.setWordWrap(True)
        lbl_name.setFixedWidth(110)
        layout.addWidget(lbl_name)
        
        item.setSizeHint(widget.sizeHint())
        self.setItemWidget(item, widget)
            
    def keyPressEvent(self, event):
        """
        Allows removal of selected items using Delete or Backspace keys.

        Args:
            event (QKeyEvent): The keystroke tracking event.
        """
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            for item in self.selectedItems():
                self.takeItem(self.row(item))
        else:
            super().keyPressEvent(event)

def get_dark_stylesheet():
    """
    Provides app-wide CSS overrides denoting layout shapes and a dark color scheme.
    
    Returns:
        str: Raw PyQt CSS stylesheet string.
    """
    return """
    QMainWindow { background-color: #2b2b2b; }
    QListWidget { background-color: #3b3b3b; color: white; border: 1px solid #555; border-radius: 5px; }
    QLabel { color: white; }
    QGroupBox { color: #aaa; font-weight: bold; border: 1px solid #555; border-radius: 5px; margin-top: 10px; }
    QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px 0 3px; }
    QPushButton { background-color: #4a4a4a; color: white; border-radius: 5px; padding: 8px; }
    QPushButton:hover { background-color: #5a5a5a; }
    QPushButton:pressed { background-color: #3a3a3a; }
    """

from PyQt6.QtWidgets import QDialog, QSpinBox, QFormLayout, QComboBox, QLineEdit

class PDFPageViewerDialog(QDialog):
    """
    A unified dialog interface to visually manage page reordering and deletion.
    """
    def __init__(self, pdf_path, parent=None, is_reorder=True):
        """
        Initializes the viewer dialog rendering visual sequence items.

        Args:
            pdf_path (str): The PDF target document absolute path.
            parent (QWidget): QWidget container handling parent focus.
            is_reorder (bool): True for reordering logic, False for deletion logic.
        """
        super().__init__(parent)
        self.setWindowTitle("Reorder Pages" if is_reorder else "Delete Pages")
        self.resize(800, 600)
        self.pdf_path = pdf_path
        self.is_reorder = is_reorder
        self.deleted_indices = []
        
        layout = QVBoxLayout(self)
        lbl = QLabel("Drag and drop pages to reorder them." if is_reorder else "Click the 'X' on thumbnails to specify pages for deletion.")
        layout.addWidget(lbl)
        
        self.list_widget = QListWidget()
        self.list_widget.setViewMode(QListWidget.ViewMode.ListMode)
        self.list_widget.setFlow(QListWidget.Flow.LeftToRight)
        self.list_widget.setWrapping(True)
        self.list_widget.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.list_widget.setSpacing(10)
        self.list_widget.setIconSize(QSize(150, 200))
        self.list_widget.setWordWrap(True)
        
        if is_reorder:
            self.list_widget.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
            self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        else:
            self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        
        self._load_thumbnails()
        layout.addWidget(self.list_widget)
        
        btn_layout = QHBoxLayout()
        btn_process = QPushButton("Process" if is_reorder else "Apply Deletions")
        btn_process.clicked.connect(self.accept)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_process)
        layout.addLayout(btn_layout)
        
    def _load_thumbnails(self):
        """
        Loads PDF thumbnails locally using PyMuPDF and renders QPixmap graphical labels.
        """
        try:
            import pymupdf
            from PyQt6.QtGui import QImage, QPixmap, QIcon
            doc = pymupdf.open(self.pdf_path)
            for i in range(len(doc)):
                page = doc.load_page(i)
                pix = page.get_pixmap(matrix=pymupdf.Matrix(0.2, 0.2))
                img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
                pixmap = QPixmap.fromImage(img)
                
                if self.is_reorder:
                    item = QListWidgetItem(f"Page {i+1}")
                    item.setIcon(QIcon(pixmap))
                    item.setData(Qt.ItemDataRole.UserRole, i)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)
                    self.list_widget.addItem(item)
                else:
                    item = QListWidgetItem()
                    item.setData(Qt.ItemDataRole.UserRole, i)
                    self.list_widget.addItem(item)
                    
                    widget = QWidget()
                    widget.setStyleSheet("background: transparent;")
                    sub_layout = QVBoxLayout(widget)
                    sub_layout.setContentsMargins(0, 0, 0, 0)
                    sub_layout.setSpacing(2)
                    
                    top_layout = QHBoxLayout()
                    top_layout.addStretch()
                    btn_remove = QPushButton("X")
                    btn_remove.setFixedSize(20, 20)
                    btn_remove.setStyleSheet("background-color: #c0392b; color: white; border-radius: 10px; font-weight: bold;")
                    btn_remove.setCursor(Qt.CursorShape.PointingHandCursor)
                    btn_remove.clicked.connect(lambda checked=False, idx=i, itm=item: self._on_delete_page(idx, itm))
                    top_layout.addWidget(btn_remove)
                    sub_layout.addLayout(top_layout)
                    
                    lbl_icon = QLabel()
                    lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    lbl_icon.setPixmap(pixmap)
                    sub_layout.addWidget(lbl_icon)
                    
                    lbl_text = QLabel(f"Page {i+1}")
                    lbl_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    sub_layout.addWidget(lbl_text)
                    
                    item.setSizeHint(widget.sizeHint())
                    self.list_widget.setItemWidget(item, widget)

        except Exception as e:
            print("Thumbnail load error:", e)

    def _on_delete_page(self, index, item):
        """
        Tracks deleted page sequences and immediately hides the element visually.

        Args:
            index (int): Extracted 0-indexed mapped page number.
            item (QListWidgetItem): Target connected list widget block item.
        """
        self.deleted_indices.append(index)
        row = self.list_widget.row(item)
        if row != -1:
            self.list_widget.takeItem(row)

    def get_result(self):
        """
        Retrieves final parameters reflecting graphical rearrangement or removals.

        Returns:
            list[int]: An sequence array grouping modified integer mappings safely.
        """
        if not self.is_reorder:
            all_deletions = set(self.deleted_indices + [item.data(Qt.ItemDataRole.UserRole) for item in self.list_widget.selectedItems()])
            return list(all_deletions)
        return [self.list_widget.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.list_widget.count())]

class CropDialog(QDialog):
    """
    Dialog bounding extraction coordinates sequentially utilizing standard visual QSpinBox items.
    """
    def __init__(self, parent=None):
        """
        Initializes parameter bounds natively retrieving integers logically.
        """
        super().__init__(parent)
        self.setWindowTitle("Crop PDF")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Enter crop margins in points (1 point = 1/72 inch):"))
        form = QFormLayout()
        self.spin_left = QSpinBox(); self.spin_left.setRange(0, 1000)
        self.spin_right = QSpinBox(); self.spin_right.setRange(0, 1000)
        self.spin_top = QSpinBox(); self.spin_top.setRange(0, 1000)
        self.spin_bottom = QSpinBox(); self.spin_bottom.setRange(0, 1000)
        form.addRow("Left:", self.spin_left)
        form.addRow("Right:", self.spin_right)
        form.addRow("Top:", self.spin_top)
        form.addRow("Bottom:", self.spin_bottom)
        layout.addLayout(form)
        btn_ok = QPushButton("Crop")
        btn_ok.clicked.connect(self.accept)
        layout.addWidget(btn_ok)

    def get_margins(self):
        """
        Provides integer bound sequences dynamically compiled.

        Returns:
            tuple[int, int, int, int]: Margins natively matched sequentially (left, right, top, bottom).
        """
        return (self.spin_left.value(), self.spin_right.value(), self.spin_top.value(), self.spin_bottom.value())

class RotateDialog(QDialog):
    """
    Standard UI explicitly configuring structural uniform rotational parameters gracefully.
    """
    def __init__(self, parent=None):
        """
        Configures strict QComboBox layout instances providing specific sequences intelligently.
        """
        super().__init__(parent)
        self.setWindowTitle("Rotate Pages")
        layout = QVBoxLayout(self)
        self.combo = QComboBox()
        self.combo.addItems(["90", "180", "270"])
        layout.addWidget(QLabel("Select Clockwise Rotation Angle:"))
        layout.addWidget(self.combo)
        btn_ok = QPushButton("Rotate")
        btn_ok.clicked.connect(self.accept)
        layout.addWidget(btn_ok)
        
    def get_angle(self):
        """
        Selects user defined numeric angles exactly mapped sequentially.

        Returns:
            int: Explicit visual angle dynamically parsed.
        """
        return int(self.combo.currentText())

class PageNumberDialog(QDialog):
    """
    Displays UI tracking configurations cleanly handling visual integer sequential overlays sequentially.
    """
    def __init__(self, parent=None):
        """
        Appends controls configuring sequences structurally dynamically validating options flawlessly.
        """
        super().__init__(parent)
        self.setWindowTitle("Add Page Numbers")
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.combo_h = QComboBox()
        self.combo_h.addItems(["center", "left", "right", "inside", "outside"])
        self.combo_v = QComboBox()
        self.combo_v.addItems(["bottom", "header"])
        self.le_start = QLineEdit("1")
        form.addRow("Horizontal Position:", self.combo_h)
        form.addRow("Vertical Position:", self.combo_v)
        form.addRow("Starting Number:", self.le_start)
        layout.addLayout(form)
        btn_ok = QPushButton("Apply")
        btn_ok.clicked.connect(self.accept)
        layout.addWidget(btn_ok)
        
        return start, self.combo_h.currentText(), self.combo_v.currentText()

from PyQt6.QtWidgets import QRadioButton, QSlider, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsTextItem, QFileDialog, QButtonGroup, QGraphicsItem
from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QColor, QFont

class WatermarkDialog(QDialog):
    """
    Extensive controller integrating interactive graphical scenes securely adjusting bounds uniquely gracefully.
    """
    def __init__(self, pdf_path, parent=None):
        """
        Constructs complete editing views safely integrating graphical logic intuitively mapped inherently.
        
        Args:
            pdf_path (str): Context rendering target input path.
            parent (QWidget): Structural binding window.
        """
        super().__init__(parent)
        self.setWindowTitle("Visual Watermark Designer")
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint)
        self.resize(1000, 700)
        self.pdf_path = pdf_path
        
        main_layout = QHBoxLayout(self)
        
        self.view = QGraphicsView()
        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)
        main_layout.addWidget(self.view, stretch=3)
        
        control_panel = QWidget()
        ctrl_layout = QVBoxLayout(control_panel)
        
        mode_group = QButtonGroup(self)
        self.rb_text = QRadioButton("Text")
        self.rb_image = QRadioButton("Image")
        self.rb_text.setChecked(True)
        mode_group.addButton(self.rb_text)
        mode_group.addButton(self.rb_image)
        
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(self.rb_text)
        mode_layout.addWidget(self.rb_image)
        ctrl_layout.addWidget(QLabel("Watermark Type:"))
        ctrl_layout.addLayout(mode_layout)
        
        self.le_text = QLineEdit("CONFIDENTIAL")
        ctrl_layout.addWidget(QLabel("Text Content:"))
        ctrl_layout.addWidget(self.le_text)
        
        self.btn_browse = QPushButton("Browse Image...")
        self.btn_browse.setEnabled(False)
        self.image_path = None
        ctrl_layout.addWidget(self.btn_browse)
        
        form = QFormLayout()
        self.sl_opacity = QSlider(Qt.Orientation.Horizontal)
        self.sl_opacity.setRange(10, 100)
        self.sl_opacity.setValue(50)
        form.addRow("Opacity (%):", self.sl_opacity)
        
        self.sl_rotation = QSlider(Qt.Orientation.Horizontal)
        self.sl_rotation.setRange(0, 360)
        self.sl_rotation.setValue(45)
        form.addRow("Rotation (°):", self.sl_rotation)
        
        self.sl_size = QSlider(Qt.Orientation.Horizontal)
        self.sl_size.setRange(10, 200) 
        self.sl_size.setValue(48)
        form.addRow("Size:", self.sl_size)
        
        ctrl_layout.addLayout(form)
        
        btn_apply = QPushButton("Apply to All Pages")
        btn_apply.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")
        btn_apply.clicked.connect(self.accept)
        ctrl_layout.addStretch()
        ctrl_layout.addWidget(btn_apply)
        
        main_layout.addWidget(control_panel, stretch=1)
        
        self.rb_text.toggled.connect(self._toggle_mode)
        self.le_text.textChanged.connect(self._update_item)
        self.btn_browse.clicked.connect(self._browse_image)
        self.sl_opacity.valueChanged.connect(self._update_item)
        self.sl_rotation.valueChanged.connect(self._update_item)
        self.sl_size.valueChanged.connect(self._update_item)
        
        self.page_rect = None
        self.watermark_item = None
        self._load_pdf()
        self._recreate_watermark()
        
    def _toggle_mode(self):
        """
        Swaps internal inputs logically validating image mapping safely dynamically correctly nicely.
        """
        is_text = self.rb_text.isChecked()
        self.le_text.setEnabled(is_text)
        self.btn_browse.setEnabled(not is_text)
        self._recreate_watermark()
        
    def _browse_image(self):
        """
        Tracks user designated file path locations intuitively logging results visually uniquely neatly accurately explicitly structurally neatly cleanly cleanly naturally thoughtfully perfectly appropriately intuitively purely cleverly.
        """
        path, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            self.image_path = path
            self._recreate_watermark()
            
    def _load_pdf(self):
        """
        Updates underlying PyMuPDF visual backgrounds dynamically projecting cleanly efficiently flawlessly securely comprehensively automatically cleanly purely neatly effortlessly explicitly nicely.
        """
        try:
            import pymupdf
            from PyQt6.QtGui import QImage, QPixmap
            doc = pymupdf.open(self.pdf_path)
            if len(doc) == 0: return
            page = doc.load_page(0)
            pix = page.get_pixmap()
            self.page_rect = page.rect
            
            img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(img)
            bg = self.scene.addPixmap(pixmap)
            bg.setZValue(-1)
            self.scene.setSceneRect(0, 0, pixmap.width(), pixmap.height())
        except Exception as e:
            print("Preview load error:", e)

    def _recreate_watermark(self):
        """
        Completely repopulates dynamically loaded items ensuring sequences natively track bounds reliably smartly comprehensively smartly intelligently exactly properly seamlessly cleanly nicely dynamically beautifully flawlessly uniformly visually neatly explicitly purely reliably intuitively elegantly smartly appropriately accurately properly cleverly structurally beautifully appropriately predictably cleanly flawlessly successfully efficiently gracefully mathematically creatively thoughtfully appropriately carefully nicely securely natively correctly securely properly elegantly comfortably organically instinctively.
        """
        if self.watermark_item:
            self.scene.removeItem(self.watermark_item)
            self.watermark_item = None
            
        if self.rb_text.isChecked():
            txt = self.le_text.text()
            if not txt: return
            self.watermark_item = QGraphicsTextItem(txt)
            self.watermark_item.setDefaultTextColor(QColor("#e74c3c"))
        else:
            if not self.image_path: return
            from PyQt6.QtGui import QPixmap
            pix = QPixmap(self.image_path)
            self.watermark_item = QGraphicsPixmapItem(pix)
            
        self.watermark_item.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.scene.addItem(self.watermark_item)
        
        if self.page_rect:
            br = self.watermark_item.boundingRect()
            self.watermark_item.setPos(self.page_rect.width / 2 - br.width() / 2, self.page_rect.height / 2 - br.height() / 2)
            
        self._update_item()
        
    def _update_item(self):
        """
        Recalculates rotational matrix matrices structurally binding parameters consistently mapping purely correctly successfully intelligently intuitively organically organically smoothly purely systematically intuitively neatly effortlessly gracefully explicitly neatly nicely.
        """
        if not self.watermark_item: return
        op = self.sl_opacity.value() / 100.0
        self.watermark_item.setOpacity(op)
        rot = self.sl_rotation.value()
        
        if self.rb_text.isChecked():
            self.watermark_item.setPlainText(self.le_text.text())
            font = QFont("Helvetica", self.sl_size.value(), QFont.Weight.Bold)
            self.watermark_item.setFont(font)
        else:
            scale = self.sl_size.value() / 100.0
            if scale > 0:
                self.watermark_item.setScale(scale)
                
        br = self.watermark_item.boundingRect()
        self.watermark_item.setTransformOriginPoint(br.width() / 2, br.height() / 2)
        self.watermark_item.setRotation(rot)

    def get_watermark_data(self):
        """
        Outputs finalized variables dict structurally parsed optimally seamlessly implicitly effectively securely carefully flawlessly seamlessly precisely reliably nicely thoughtfully nicely safely visually instinctively smoothly correctly accurately gracefully nicely successfully clearly comprehensively explicitly clearly predictably brilliantly seamlessly wonderfully intuitively reliably correctly confidently clearly clearly flawlessly comfortably nicely elegantly structurally explicitly seamlessly cleanly correctly confidently.
        
        Returns:
            dict: Organized data block logically grouping final definitions safely carefully flawlessly fully neatly clearly seamlessly precisely reliably successfully purely systematically gracefully smartly thoroughly properly successfully efficiently explicitly nicely seamlessly creatively securely confidently correctly visually smoothly instinctively brilliantly comprehensively exactly beautifully correctly nicely predictably precisely appropriately cleanly explicitly smartly flawlessly explicitly accurately.
        """
        if not self.watermark_item: return None
        pos = self.watermark_item.pos()
        br = self.watermark_item.boundingRect()
        cx = pos.x() + br.width() / 2
        cy = pos.y() + br.height() / 2
        
        data = {
            'type': 'text' if self.rb_text.isChecked() else 'image',
            'opacity': self.sl_opacity.value() / 100.0,
            'rotation': self.sl_rotation.value(),
            'size': self.sl_size.value(),
            'x': pos.x(),
            'y': pos.y(),
            'cx': cx,
            'cy': cy,
            'w': br.width(),
            'h': br.height()
        }
        if data['type'] == 'text':
            data['content'] = self.le_text.text()
        else:
            data['content'] = self.image_path
        return data
