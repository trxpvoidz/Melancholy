"""
Melancholy Skin Pack Manager
Copyright (c) 2026 TrxpVoidz (Ecliptix)
All rights reserved.

This software is proprietary and confidential.
Unauthorized copying, distribution, or modification is prohibited.
"""

import sys, os, json, zipfile, shutil, tempfile, ctypes, time, shlex
from pathlib import Path
from io import BytesIO
from hashlib import sha256
from base64 import b64encode
import threading
import subprocess
import psutil

import requests
from PIL import Image
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, QScrollArea,
    QMessageBox, QProgressBar, QTextEdit, QTabWidget,
    QFileDialog, QListWidget, QListWidgetItem, QComboBox, QSplashScreen,
    QSizePolicy, QGroupBox, QCheckBox, QSlider, QSpinBox, QSplitter,
    QTreeWidget, QTreeWidgetItem, QHeaderView, QLineEdit, QPlainTextEdit
)
from PySide6.QtGui import QPixmap, QIcon, QDesktopServices, QPainter, QColor, QBrush, QLinearGradient, QPalette, QFont, QTextCursor
from PySide6.QtCore import Qt, QThread, Signal, QUrl, QPropertyAnimation, QEasingCurve, QTimer, QPoint, QByteArray
from PySide6.QtMultimedia import QSoundEffect
from PySide6.QtGui import QPixmap, QIcon, QDesktopServices, QPainter, QColor, QBrush, QLinearGradient, QPalette, QFont, QTextCursor
from PySide6.QtCore import Qt, QThread, Signal, QUrl, QPropertyAnimation, QEasingCurve, QTimer, QPoint, QByteArray

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

# Try to import Windows API modules
try:
    import win32api
    import win32process
    import win32con
    import win32file
    import win32event
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    print("Warning: pywin32 not installed. Some features may be simulated.")

# ---------------- RESOURCE PATH ----------------
def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# ---------------- PATHS ----------------
SKIN_PACK_DIR = Path(os.getenv("APPDATA")) / "Minecraft Bedrock" / "premium_cache" / "skin_packs"
SKIN_PACK_DIR.mkdir(parents=True, exist_ok=True)
LEGACY_VAULT_DIR = SKIN_PACK_DIR.parent / "legacy_vault"
LEGACY_VAULT_DIR.mkdir(parents=True, exist_ok=True)
STATE_FILE = SKIN_PACK_DIR / ".skinpack_manager_state.json"
LEGACY_STATE_FILE = LEGACY_VAULT_DIR / ".legacy_vault_state.json"
MARKETPLACE_URL = "https://raw.githubusercontent.com/trxpvoidz/Skin-Pack-Store-Importer/main/store.json"
SOUND_FILE = SKIN_PACK_DIR.parent / "startup_sound.wav"

# ---------------- STATE ----------------
def load_state():
    state = {"known": []}
    if STATE_FILE.exists():
        try:
            state = json.loads(STATE_FILE.read_text())
        except:
            state = {"known": []}
    if not isinstance(state.get("known"), list):
        state["known"] = list(state.get("known").values())
    return state

def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))

def load_legacy_state():
    state = {"injected_packs": [], "custom_packs": []}
    if LEGACY_STATE_FILE.exists():
        try:
            state = json.loads(LEGACY_STATE_FILE.read_text())
        except:
            pass
    return state

def save_legacy_state(state):
    LEGACY_STATE_FILE.write_text(json.dumps(state, indent=2))

# ---------------- MANIFEST ----------------
def find_manifest(folder):
    for r, _, f in os.walk(folder):
        if "manifest.json" in f:
            return Path(r) / "manifest.json"
    return None

def read_manifest(path):
    data = json.loads(path.read_text())
    return data["header"]["uuid"], data["header"].get("version", [0,0,0])

def vtuple(v): return tuple(v or [0,0,0])

# ---------------- SKIN PACK MERGER UTILITIES ----------------
def remove_quotes(s: str) -> str:
    return s.replace('"', '').strip()

def load_json(json_path: Path) -> dict:
    with json_path.open("r", encoding="utf-8") as f:
        return json.load(f)

def merge_geometry_json(files: list[Path], output_path: Path) -> None:
    geo_dicts = []
    for f in files:
        if f.exists():
            try:
                geo_dicts.append(load_json(f))
            except Exception:
                print(f"  [!] Skipping invalid geometry.json: {f}")

    if not geo_dicts:
        return

    # Choose the largest file as base
    base = max(geo_dicts, key=lambda d: len(json.dumps(d)))
    merged = base.copy()

    for other in geo_dicts:
        if other is base:
            continue
        for key, value in other.items():
            if key not in merged:
                merged[key] = value
            elif isinstance(merged[key], list) and isinstance(value, list):
                existing_names = {g.get("name") for g in merged[key] if isinstance(g, dict) and "name" in g}
                for geom in value:
                    if isinstance(geom, dict) and geom.get("name") not in existing_names:
                        merged[key].append(geom)

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)

def process_single_pack(sp_dir: Path, output_dir: Path, tex_start: int, cape_start: int) -> tuple[list, int, int]:
    json_path = sp_dir / "skins.json"
    if not json_path.exists():
        print(f"  [!] skins.json not found in {sp_dir} – skipping.")
        return [], tex_start, cape_start

    data = load_json(json_path)
    new_skins = []
    cape_map: dict[str, str] = {}

    for skin in data["skins"]:
        # --- texture ---
        old_tex_path = sp_dir / skin["texture"]
        new_tex_name = f"s{tex_start}.png"
        if old_tex_path.exists():
            shutil.copy(old_tex_path, output_dir / new_tex_name)
        skin["texture"] = new_tex_name

        # --- cape ---
        if "cape" in skin:
            orig_cape_name = skin["cape"]
            if orig_cape_name in cape_map:
                skin["cape"] = cape_map[orig_cape_name]
            else:
                new_cape_name = f"c{cape_start}.png"
                old_cape_path = sp_dir / orig_cape_name
                if old_cape_path.exists():
                    shutil.copy(old_cape_path, output_dir / new_cape_name)
                cape_map[orig_cape_name] = new_cape_name
                skin["cape"] = new_cape_name
                cape_start += 1

        # --- localization name ---
        skin["localization_name"] = f"s{tex_start}"

        new_skins.append(skin)
        tex_start += 1

    return new_skins, tex_start, cape_start

def merge_multiple_skinpacks(pack_dirs: list[Path], output_dir: Path, log_callback=None) -> None:
    """Merge multiple skin packs into one"""
    def log(msg):
        if log_callback:
            log_callback(msg)
        else:
            print(msg)
    
    log(f"\n>>> Merging {len(pack_dirs)} packs into: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    tex_counter = 1
    cape_counter = 1
    all_skins = []
    geometry_files = []
    manifest_copied = False

    for i, pack_dir in enumerate(pack_dirs):
        log(f"  → {pack_dir}")
        skins, tex_counter, cape_counter = process_single_pack(pack_dir, output_dir, tex_counter, cape_counter)
        all_skins.extend(skins)

        geo = pack_dir / "geometry.json"
        if geo.exists():
            geometry_files.append(geo)

        if not manifest_copied:
            manifest = pack_dir / "manifest.json"
            if manifest.exists():
                shutil.copy(manifest, output_dir / "manifest.json")
                manifest_copied = True
                log(f"  ✔ Copied manifest.json from: {pack_dir.name}")

    # Save merged skins.json
    merged_json = {
        "serialize_name": "merged_pack",
        "localization_name": "merged_pack",
        "skins": all_skins
    }
    with (output_dir / "skins.json").open("w", encoding="utf-8") as f:
        json.dump(merged_json, f, indent=2, ensure_ascii=False)

    # Merge geometry.json
    if geometry_files:
        merge_geometry_json(geometry_files, output_dir / "geometry.json")
        log("  ✔ geometry.json merged")

    log("\n  ✔ Merge completed!")

# ---------------- BACKGROUND WIDGET ----------------
class BackgroundWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.background_image = None
        self.load_background()
        
    def load_background(self):
     """Try to load background.png from various locations"""
     possible_paths = [
        Path(resource_path("background.png")),
        Path(os.getcwd()) / "background.png",
        Path(os.getcwd()) / "assets" / "background.png",
    ]
    
     for path in possible_paths:
        if path.exists():
            self.background_image = QPixmap(str(path))
            break
                
    def paintEvent(self, event):
        painter = QPainter(self)
        
        # Draw background image if available
        if self.background_image and not self.background_image.isNull():
            # Scale image to fit window while keeping aspect ratio
            scaled_bg = self.background_image.scaled(
                self.size(), 
                Qt.KeepAspectRatioByExpanding, 
                Qt.SmoothTransformation
            )
            
            # Center the image
            x = (self.width() - scaled_bg.width()) // 2
            y = (self.height() - scaled_bg.height()) // 2
            painter.drawPixmap(x, y, scaled_bg)
        else:
            # Fallback gradient if no background image
            gradient = QLinearGradient(0, 0, self.width(), self.height())
            gradient.setColorAt(0, QColor(20, 20, 20, 220))
            gradient.setColorAt(1, QColor(40, 40, 40, 220))
            painter.fillRect(self.rect(), gradient)
        
        # Draw a semi-transparent overlay to make text readable
        painter.fillRect(self.rect(), QColor(0, 0, 0, 100))
        
        super().paintEvent(event)

# ---------------- MERGER WORKER ----------------
class MergerWorker(QThread):
    log = Signal(str)
    progress = Signal(int)
    finished = Signal(bool, str)
    
    def __init__(self, pack_dirs, output_dir):
        super().__init__()
        self.pack_dirs = pack_dirs
        self.output_dir = output_dir
        
    def run(self):
        try:
            def log_callback(msg):
                self.log.emit(msg)
            
            # Simulate progress
            self.progress.emit(10)
            merge_multiple_skinpacks(self.pack_dirs, self.output_dir, log_callback)
            self.progress.emit(100)
            self.finished.emit(True, "Merge completed successfully!")
            
        except Exception as e:
            self.finished.emit(False, str(e))

# ---------------- STORE WORKER ----------------
class StoreLoader(QThread):
    finished = Signal(list)
    error = Signal(str)
    def run(self):
        try:
            r = requests.get(MARKETPLACE_URL, timeout=15)
            packs = r.json()["packs"]
            self.finished.emit(packs)
        except Exception as e:
            self.error.emit(str(e))

# ---------------- DOWNLOAD WORKER ----------------
class DownloadWorker(QThread):
    progress = Signal(int)
    log = Signal(str)
    finished = Signal(Path)
    error = Signal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            self.log.emit("Starting download…")
            tmp_dir = Path(tempfile.gettempdir()) / "mcbe_skin_downloads"
            tmp_dir.mkdir(exist_ok=True)
            zip_path = tmp_dir / "pack.zip"

            r = requests.get(self.url, stream=True, timeout=30)
            r.raise_for_status()
            total = int(r.headers.get("Content-Length",0))
            done = 0
            with open(zip_path,"wb") as f:
                for chunk in r.iter_content(8192):
                    if not chunk: continue
                    f.write(chunk)
                    done += len(chunk)
                    if total: self.progress.emit(int(done/total*100))
            self.progress.emit(100)
            self.log.emit("Download complete")
            self.finished.emit(zip_path)
        except Exception as e:
            self.error.emit(str(e))

# ---------------- THUMBNAIL LOADER ----------------
class ThumbnailLoader(QThread):
    finished = Signal(QPixmap)
    error = Signal()
    def __init__(self, url):
        super().__init__()
        self.url = url
    def run(self):
        try:
            r = requests.get(self.url, timeout=10)
            img = Image.open(BytesIO(r.content))
            img.thumbnail((200, 200))
            buf = BytesIO()
            img.save(buf, "PNG")
            pix = QPixmap()
            pix.loadFromData(buf.getvalue())
            self.finished.emit(pix)
        except:
            self.error.emit()

# ---------------- ANIMATED WIDGET ----------------
class AnimatedWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._opacity = 1.0
        self.scale = 1.0
        
    def fade_in(self):
        self.anim = QPropertyAnimation(self, b"opacity")
        self.anim.setDuration(500)
        self.anim.setStartValue(0)
        self.anim.setEndValue(1)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)
        self.anim.start()
        
    def get_opacity(self):
        return self._opacity
        
    def set_opacity(self, value):
        self._opacity = value
        self.update()
        
    opacity = property(get_opacity, set_opacity)

# ---------------- STORE CARD ----------------
class StoreCard(AnimatedWidget):
    def __init__(self, pack, state, install_cb, uninstall_cb):
        super().__init__()
        self.pack = pack
        self.install_cb = install_cb
        self.uninstall_cb = uninstall_cb
        self.setFixedWidth(220)
        self.setMinimumHeight(300)
        
        # Transparent black background
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(20, 20, 20, 200))
        self.setPalette(palette)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(8)
        
        self.thumb = QLabel("Loading…")
        self.thumb.setFixedSize(200,200)
        self.thumb.setAlignment(Qt.AlignCenter)
        self.thumb.setStyleSheet("background-color: rgba(0,0,0,100); border-radius: 10px; color: white;")
        layout.addWidget(self.thumb)
        
        self.name_label = QLabel(pack.get("name", "Unnamed Pack"))
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setWordWrap(True)
        self.name_label.setStyleSheet("color: white; font-weight: bold; font-size: 13px;")
        layout.addWidget(self.name_label)
        
        self.badge = QLabel("")
        self.badge.setAlignment(Qt.AlignCenter)
        self.badge.setStyleSheet("color: #00ff00; font-size: 11px;")
        layout.addWidget(self.badge)
        
        btns = QHBoxLayout()
        dl = QPushButton("Download")
        dl.setStyleSheet("""
            QPushButton {
                background-color: rgba(255,255,255,50);
                border: 1px solid rgba(255,255,255,100);
                border-radius: 5px;
                color: white;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: rgba(255,255,255,100);
                border: 1px solid white;
            }
        """)
        dl.clicked.connect(lambda: install_cb(pack))
        btns.addWidget(dl)
        
        if any(info.get("store_name") == pack.get("name") for info in state.get("known", [])):
            rm = QPushButton("Uninstall")
            rm.setStyleSheet("""
                QPushButton {
                    background-color: rgba(255,0,0,50);
                    border: 1px solid rgba(255,0,0,100);
                    border-radius: 5px;
                    color: white;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: rgba(255,0,0,100);
                }
            """)
            rm.clicked.connect(lambda: uninstall_cb(pack))
            btns.addWidget(rm)
            
        layout.addLayout(btns)
        
        self.update_badge(state)
        self.load_thumb(pack.get("thumbnail"))
        self.fade_in()

    def update_badge(self, state):
        if any(info.get("store_name") == self.pack.get("name") for info in state.get("known", [])):
            self.badge.setText("✔ Installed")
            self.badge.setStyleSheet("color: #00ff00; font-size: 11px;")
        else:
            self.badge.setText("")
            self.badge.setStyleSheet("")

    def load_thumb(self, url):
        if not url:
            return
        self.thumb_loader = ThumbnailLoader(url)
        self.thumb_loader.finished.connect(self.thumb.setPixmap)
        self.thumb_loader.error.connect(lambda: self.thumb.setText("No image"))
        self.thumb_loader.start()

# ---------------- DRAG & DROP WIDGET ----------------
class DragDropWidget(AnimatedWidget):
    def __init__(self, text, file_types=None, folder_mode=False, callback=None, parent=None, multi_folder=False):
        super().__init__(parent)
        self.callback = callback
        self.file_types = file_types or []
        self.folder_mode = folder_mode
        self.multi_folder = multi_folder
        self.setAcceptDrops(True)
        self.setMinimumHeight(120)
        self.text = text
        self.is_hovered = False
        
        # Set size policy correctly
        policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setSizePolicy(policy)
        
        # Transparent background
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(30, 30, 30, 180))
        self.setPalette(palette)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setOpacity(self._opacity)
        
        # Fill background
        painter.fillRect(self.rect(), QColor(30, 30, 30, 180))
        
        # Draw border
        if self.is_hovered:
            painter.setPen(QColor(255, 255, 255, 200))
        else:
            painter.setPen(QColor(255, 255, 255, 100))
            
        painter.drawRoundedRect(self.rect().adjusted(2, 2, -2, -2), 10, 10)
        
        # Draw text
        painter.setPen(QColor(255, 255, 255, 200 if self.is_hovered else 150))
        font = painter.font()
        font.setPointSize(12)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignCenter, self.text)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            self.is_hovered = True
            self.update()
            event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self.is_hovered = False
        self.update()

    def dropEvent(self, event):
        self.is_hovered = False
        self.update()
        urls = event.mimeData().urls()
        if not urls:
            return
            
        if self.multi_folder and self.folder_mode:
            # Handle multiple folders
            paths = []
            for url in urls:
                path = url.toLocalFile()
                if os.path.isdir(path):
                    paths.append(path)
            if paths and self.callback:
                self.callback(paths)
        else:
            # Single file/folder mode
            path = urls[0].toLocalFile()
            if self.folder_mode and os.path.isdir(path):
                if self.callback:
                    self.callback(path)
            elif not self.folder_mode and os.path.isfile(path):
                if self.file_types and any(path.lower().endswith(ext) for ext in self.file_types):
                    if self.callback:
                        self.callback(path)
                elif not self.file_types:
                    if self.callback:
                        self.callback(path)

    def mousePressEvent(self, event):
        self.anim = QPropertyAnimation(self, b"opacity")
        self.anim.setDuration(200)
        self.anim.setKeyValueAt(0, self._opacity)
        self.anim.setKeyValueAt(0.5, 0.5)
        self.anim.setKeyValueAt(1, self._opacity)
        self.anim.start()
        
        if self.folder_mode and self.multi_folder:
            # Multiple folder selection
            paths = QFileDialog.getExistingDirectory(self, "Select First Folder")
            if paths:
                # For multiple folders, you'd need a different approach
                # This is simplified
                if self.callback:
                    self.callback([paths])
        elif self.folder_mode:
            path = QFileDialog.getExistingDirectory(self, "Select Folder")
            if path and self.callback:
                self.callback(path)
        else:
            path, _ = QFileDialog.getOpenFileName(
                self,
                "Select File",
                "",
                "ZIP Files (*.zip)"
            )
            if path and self.callback:
                self.callback(path)

# ---------------- LOADING SCREEN ----------------
class LoadingScreen(QSplashScreen):
    def __init__(self):
        pixmap = QPixmap(600, 400)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        
       # Try to load background for loading screen
        bg_paths = [
        Path(resource_path("background.png")),
         Path(os.getcwd()) / "background.png",
     Path(os.getcwd()) / "assets" / "background.png"
]
        
        bg_loaded = False
        for path in bg_paths:
            if path.exists():
                bg = QPixmap(str(path))
                if not bg.isNull():
                    scaled_bg = bg.scaled(600, 400, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                    painter.drawPixmap(0, 0, scaled_bg)
                    bg_loaded = True
                break
        
        if not bg_loaded:
            gradient = QLinearGradient(0, 0, 600, 400)
            gradient.setColorAt(0, QColor(0, 0, 0, 240))
            gradient.setColorAt(1, QColor(50, 50, 50, 240))
            painter.fillRect(pixmap.rect(), gradient)
        
        painter.fillRect(pixmap.rect(), QColor(0, 0, 0, 100))
        
        painter.setPen(QColor(255, 255, 255, 200))
        font = painter.font()
        font.setPointSize(24)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "Melancholy\n\nLoading...")
        
        painter.setPen(QColor(255, 255, 255, 100))
        font.setPointSize(12)
        painter.setFont(font)
        painter.drawText(pixmap.rect().adjusted(0, 100, 0, 0), Qt.AlignCenter, "Skin Pack Manager")
        
        painter.end()
        
        super().__init__(pixmap)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        
    def show_message(self, message):
        self.showMessage(message, Qt.AlignBottom | Qt.AlignCenter, QColor(255, 255, 255, 200))

# ---------------- MERGER TAB WITH ENCRYPTION ----------------
class MergerTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.pack_dirs = []
        self.merger_worker = None
        self.merged_pack_path = None
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("SkinPack Merger - Combine & Encrypt Multiple Skin Packs")
        title.setStyleSheet("color: white; font-size: 18px; font-weight: bold; padding: 10px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Description
        desc = QLabel(
            "Drag and drop multiple SkinPack folders to merge them into one combined pack.\n"
            "Textures will be renamed automatically and geometry files will be merged.\n"
            "After merging, you can encrypt the pack with a selected manifest."
        )
        desc.setStyleSheet("color: rgba(255,255,255,150); font-size: 12px; padding: 5px;")
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Drag & drop area for multiple folders
        self.drop_area = DragDropWidget(
            "📁 Drag SkinPack Folders Here\n(or click to select folders)",
            folder_mode=True,
            multi_folder=True,
            callback=self.add_folders
        )
        self.drop_area.setMinimumHeight(150)
        layout.addWidget(self.drop_area)
        
        # Selected packs list
        list_label = QLabel("Selected Packs:")
        list_label.setStyleSheet("color: white; font-size: 14px; font-weight: bold; padding: 5px;")
        layout.addWidget(list_label)
        
        self.pack_list = QListWidget()
        self.pack_list.setStyleSheet("""
            QListWidget {
                background-color: rgba(0,0,0,150);
                border: 1px solid rgba(255,255,255,50);
                border-radius: 5px;
                color: white;
                min-height: 100px;
            }
        """)
        layout.addWidget(self.pack_list)
        
        # Manifest selection
        manifest_layout = QHBoxLayout()
        manifest_label = QLabel("Select Manifest for Encryption:")
        manifest_label.setStyleSheet("color: white; font-size: 13px;")
        manifest_layout.addWidget(manifest_label)
        
        self.manifest_dropdown = QComboBox()
        self.manifest_dropdown.addItems(MANIFEST_OPTIONS.keys())
        self.manifest_dropdown.setStyleSheet("""
            QComboBox {
                background-color: rgba(0,0,0,150);
                border: 1px solid rgba(255,255,255,50);
                border-radius: 5px;
                color: white;
                padding: 5px;
                min-width: 200px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: rgba(30,30,30,230);
                color: white;
                selection-background-color: rgba(255,255,255,100);
            }
        """)
        manifest_layout.addWidget(self.manifest_dropdown)
        manifest_layout.addStretch()
        layout.addLayout(manifest_layout)
        
        # Checkbox for encryption
        self.encrypt_checkbox = QCheckBox("🔐 Encrypt merged pack before importing")
        self.encrypt_checkbox.setStyleSheet("color: white; font-size: 13px; padding: 5px;")
        self.encrypt_checkbox.setChecked(True)
        layout.addWidget(self.encrypt_checkbox)
        
        # Control buttons
        btn_layout = QHBoxLayout()
        
        self.clear_btn = QPushButton("🗑️ Clear List")
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255,0,0,50);
                border: 1px solid rgba(255,0,0,100);
                border-radius: 5px;
                color: white;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: rgba(255,0,0,100);
            }
        """)
        self.clear_btn.clicked.connect(self.clear_list)
        btn_layout.addWidget(self.clear_btn)
        
        self.merge_btn = QPushButton("🔄 Merge Packs")
        self.merge_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(0,150,255,80);
                border: 1px solid rgba(0,150,255,150);
                border-radius: 5px;
                color: white;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(0,150,255,150);
            }
        """)
        self.merge_btn.clicked.connect(self.start_merge)
        btn_layout.addWidget(self.merge_btn)
        
        self.import_merged_btn = QPushButton("📦 Import Merged Pack")
        self.import_merged_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(0,255,0,50);
                border: 1px solid rgba(0,255,0,100);
                border-radius: 5px;
                color: white;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(0,255,0,100);
            }
        """)
        self.import_merged_btn.clicked.connect(self.import_merged_pack)
        self.import_merged_btn.setEnabled(False)
        btn_layout.addWidget(self.import_merged_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Log output
        log_label = QLabel("Merge Log:")
        log_label.setStyleSheet("color: white; font-size: 12px; padding: 5px;")
        layout.addWidget(log_label)
        
        self.log_output = QPlainTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(150)
        self.log_output.setStyleSheet("""
            QPlainTextEdit {
                background-color: rgba(0,0,0,150);
                border: 1px solid rgba(255,255,255,50);
                border-radius: 5px;
                color: #00ff00;
                font-family: monospace;
            }
        """)
        layout.addWidget(self.log_output)
        
    def add_folders(self, paths):
        """Add folders to the list"""
        for path_str in paths:
            path = Path(path_str)
            if path.is_dir() and self.is_valid_skinpack(path):
                if str(path) not in [self.pack_list.item(i).text() for i in range(self.pack_list.count())]:
                    self.pack_list.addItem(str(path))
                    self.pack_dirs.append(path)
            else:
                QMessageBox.warning(self, "Invalid Pack", f"{path} is not a valid skin pack (missing skins.json)")
        
        self.update_merge_button()
        
    def is_valid_skinpack(self, path):
        """Check if folder is a valid skin pack"""
        return (path / "skins.json").exists()
        
    def clear_list(self):
        """Clear the pack list"""
        self.pack_list.clear()
        self.pack_dirs.clear()
        self.log_output.clear()
        self.import_merged_btn.setEnabled(False)
        self.update_merge_button()
        
    def update_merge_button(self):
        """Update merge button state based on number of packs"""
        if len(self.pack_dirs) >= 2:
            self.merge_btn.setEnabled(True)
        else:
            self.merge_btn.setEnabled(False)
            
    def start_merge(self):
        """Start the merge process"""
        if len(self.pack_dirs) < 2:
            QMessageBox.warning(self, "Not Enough Packs", "Please select at least 2 skin packs to merge.")
            return
            
        # Create output directory
        output_dir = Path(tempfile.gettempdir()) / "merged_skinpack"
        if output_dir.exists():
            shutil.rmtree(output_dir)
            
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.log_output.clear()
        self.merge_btn.setEnabled(False)
        self.clear_btn.setEnabled(False)
        
        # Start worker thread
        self.merger_worker = MergerWorker(self.pack_dirs, output_dir)
        self.merger_worker.log.connect(self.log_output.appendPlainText)
        self.merger_worker.progress.connect(self.progress_bar.setValue)
        self.merger_worker.finished.connect(self.on_merge_finished)
        self.merger_worker.start()
        
    def on_merge_finished(self, success, message):
        """Handle merge completion"""
        self.progress_bar.setVisible(False)
        self.merge_btn.setEnabled(True)
        self.clear_btn.setEnabled(True)
        
        if success:
            self.log_output.appendPlainText("\n✅ Merge completed successfully!")
            self.import_merged_btn.setEnabled(True)
            self.merged_pack_path = Path(tempfile.gettempdir()) / "merged_skinpack"
        else:
            QMessageBox.critical(self, "Merge Failed", f"Failed to merge packs: {message}")
            
    def encrypt_merged_pack(self, pack_path, manifest_choice):
     """Encrypt the merged pack using EXACT same method as porter tab"""
     try:
        self.log_output.appendPlainText(f"\n🔐 Encrypting pack with manifest: {manifest_choice}...")
        
        # Create a temporary copy exactly like porter does
        temp_copy = copy_pack_first(str(pack_path))
        self.log_output.appendPlainText("  ✓ Pack copied to temporary location")
        
        # Setup manifest exactly like porter does
        setup_porter(temp_copy, manifest_choice)
        self.log_output.appendPlainText(f"  ✓ Manifest set: {manifest_choice}")
        
        # Make sure global variables are accessible
        global key, encryptedVariable, inputPathSkinpack
        
        # Run porter encryption exactly like porter does
        # Change to the temp directory to ensure paths work correctly
        original_dir = os.getcwd()
        os.chdir(temp_copy)
        
        try:
            # Call tool_porter with the temp directory
            tool_porter(temp_copy)
        finally:
            # Change back to original directory
            os.chdir(original_dir)
            
        self.log_output.appendPlainText("  ✓ Encryption completed")
        
        # Replace original with encrypted version
        shutil.rmtree(pack_path)
        shutil.move(temp_copy, pack_path)
        
        self.log_output.appendPlainText("  ✓ Encrypted pack ready")
        return True
        
     except Exception as e:
        self.log_output.appendPlainText(f"  ✗ Encryption failed: {str(e)}")
        import traceback
        self.log_output.appendPlainText(f"  Traceback: {traceback.format_exc()}")
        
        # Clean up temp directory if it exists
        try:
            if 'temp_copy' in locals() and os.path.exists(temp_copy):
                shutil.rmtree(temp_copy, ignore_errors=True)
        except:
            pass
        return False
     

    def encrypt_merged_pack_direct(self, pack_path, manifest_choice):
     """Direct encryption method if the porter functions fail"""
     try:
        self.log_output.appendPlainText(f"\n🔐 Directly encrypting pack with manifest: {manifest_choice}...")
        
        # Import necessary modules locally to ensure they're available
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        import json
        from hashlib import sha256
        from base64 import b64encode
        import os
        import shutil
        
        # Create a temporary copy
        temp_copy = copy_pack_first(str(pack_path))
        self.log_output.appendPlainText("  ✓ Pack copied to temporary location")
        
        # Write the manifest
        manifest_json = MANIFEST_OPTIONS[manifest_choice]
        manifest_path = os.path.join(temp_copy, "manifest.json")
        with open(manifest_path, 'w', encoding='utf-8') as f:
            f.write(manifest_json)
        self.log_output.appendPlainText(f"  ✓ Manifest written: {manifest_choice}")
        
        # Define encryption constants (same as in porter)
        FIXED_KEY = 's5s5ejuDru4uchuF2drUFuthaspAbepE'
        fileSkip = {'manifest.json', 'pack_icon.png'}
        fileSkipForce = {'contents.json', 'signatures.json'}
        fileSkipFull = fileSkip | fileSkipForce
        
        # Process all files
        fileJSONContents = {"version": 1, "content": []}
        
        for root, dirs, files in os.walk(temp_copy):
            if os.path.basename(root).lower() == 'texts':
                continue
            for file in files:
                pathFile = os.path.join(root, file)
                doEncrypt = True
                doNotAdd = False
                
                # Check if file should be skipped
                for skip_file in fileSkipFull:
                    if pathFile.endswith(skip_file):
                        doEncrypt = False
                        if skip_file in fileSkipForce:
                            doNotAdd = True
                        break
                
                relativePath = os.path.relpath(pathFile, temp_copy).replace("\\", "/")
                
                if doEncrypt and not doNotAdd:
                    # Encrypt the file
                    key = FIXED_KEY
                    cipher = Cipher(
                        algorithms.AES(key.encode('utf-8')),
                        modes.CFB8(key[:16].encode('utf-8'))
                    )
                    encryptor = cipher.encryptor()
                    
                    with open(pathFile, 'rb') as f:
                        data = f.read()
                    
                    encrypted_data = encryptor.update(data) + encryptor.finalize()
                    
                    with open(pathFile, 'wb') as f:
                        f.write(encrypted_data)
                    
                    fileJSONContents["content"].append({
                        'key': key,
                        'path': relativePath
                    })
                elif not doNotAdd:
                    fileJSONContents["content"].append({'path': relativePath})
        
        # Create signatures.json
        manifest_path = os.path.join(temp_copy, "manifest.json")
        with open(manifest_path, 'rb') as f:
            manifest_data = f.read()
            hashVal = b64encode(sha256(manifest_data).digest()).decode()
        
        signatures = [{"hash": hashVal, "path": "manifest.json"}]
        
        # Encrypt signatures
        key = FIXED_KEY
        cipher = Cipher(
            algorithms.AES(key.encode('utf-8')),
            modes.CFB8(key[:16].encode('utf-8'))
        )
        encryptor = cipher.encryptor()
        
        encrypted_sigs = encryptor.update(
            json.dumps(signatures, separators=(',', ':')).encode('utf-8')
        ) + encryptor.finalize()
        
        sig_path = os.path.join(temp_copy, 'signatures.json')
        with open(sig_path, 'wb') as f:
            f.write(encrypted_sigs)
        
        # Add signatures to contents
        fileJSONContents["content"].append({
            'key': key,
            'path': 'signatures.json'
        })
        
        # Create final contents.json
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest_data = json.load(f)
            jsonUUID = manifest_data['header']['uuid']
        
        # Encrypt contents
        cipher = Cipher(
            algorithms.AES(key.encode('utf-8')),
            modes.CFB8(key[:16].encode('utf-8'))
        )
        encryptor = cipher.encryptor()
        
        encrypted_contents = encryptor.update(
            json.dumps(fileJSONContents, separators=(',', ':')).encode('utf-8')
        ) + encryptor.finalize()
        
        # Create header
        headerByte = b'\xfc\xb9\xcf\x9b\x00\x00\x00\x00\x00\x00\x00\x00\x24'
        empty = bytes(256)
        headerFinal = empty[:4] + headerByte + jsonUUID.encode('utf-8') + empty[53:] + encrypted_contents
        
        contents_path = os.path.join(temp_copy, 'contents.json')
        with open(contents_path, 'wb') as f:
            f.write(headerFinal)
        
        self.log_output.appendPlainText("  ✓ Direct encryption completed")
        
        # Replace original with encrypted version
        shutil.rmtree(pack_path)
        shutil.move(temp_copy, pack_path)
        
        return True
        
     except Exception as e:
        self.log_output.appendPlainText(f"  ✗ Direct encryption failed: {str(e)}")
        import traceback
        self.log_output.appendPlainText(f"  Traceback: {traceback.format_exc()}")
        
        # Clean up
        try:
            if 'temp_copy' in locals() and os.path.exists(temp_copy):
                shutil.rmtree(temp_copy, ignore_errors=True)
        except:
            pass
        return False

        
    def import_merged_pack(self):
     """Import the merged pack into Minecraft with encryption - ONLY if successful"""
     if not hasattr(self, 'merged_pack_path') or not self.merged_pack_path.exists():
        QMessageBox.warning(self, "No Merged Pack", "Please merge packs first.")
        return
        
     # Check if manifest exists and is valid
     manifest_path = self.merged_pack_path / "manifest.json"
     if not manifest_path.exists():
        QMessageBox.critical(self, "Invalid Pack", "Merged pack has no manifest.json - cannot import.")
        return
        
     try:
        # Verify manifest is valid JSON
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest_data = json.load(f)
        
        # Verify manifest has required fields
        if "header" not in manifest_data or "uuid" not in manifest_data["header"]:
            QMessageBox.critical(self, "Invalid Manifest", "Manifest.json is missing required fields (header.uuid).")
            return
            
        uuid = manifest_data["header"]["uuid"]
        
     except json.JSONDecodeError:
        QMessageBox.Critical(self, "Invalid Manifest", "Manifest.json is not valid JSON.")
        return
     except Exception as e:
        QMessageBox.critical(self, "Invalid Manifest", f"Error reading manifest: {str(e)}")
        return
    
     # Handle encryption if requested
     encrypt_success = False
     if self.encrypt_checkbox.isChecked():
        manifest_choice = self.manifest_dropdown.currentText()
        
        reply = QMessageBox.question(
            self,
            "Encrypt Pack",
            f"Encrypt merged pack with manifest: {manifest_choice}?\n\n"
            "This will replace the current manifest with the selected one.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.log_output.appendPlainText("\n🔐 Starting encryption process...")
            
            # Try the standard encryption first
            encrypt_success = self.encrypt_merged_pack(self.merged_pack_path, manifest_choice)
            
            # If standard encryption fails, try direct encryption
            if not encrypt_success:
                self.log_output.appendPlainText("\n⚠️ Standard encryption failed, trying direct method...")
                encrypt_success = self.encrypt_merged_pack_direct(self.merged_pack_path, manifest_choice)
            
            if not encrypt_success:
                QMessageBox.critical(
                    self, 
                    "Encryption Failed", 
                    "Failed to encrypt the merged pack.\n\n"
                    "The pack will NOT be imported.\n"
                    "Please check the log for details."
                )
                return
                
            self.log_output.appendPlainText("✅ Encryption completed successfully!")
        else:
            self.log_output.appendPlainText("\n⏭️ Skipping encryption")
     else:
        self.log_output.appendPlainText("\n⏭️ Encryption not requested")
    
     # Now proceed with import
     try:
        dest_folder = SKIN_PACK_DIR / uuid
        
        # Check if pack with this UUID already exists
        if dest_folder.exists():
            reply = QMessageBox.question(
                self,
                "Pack Already Exists",
                f"A pack with UUID {uuid} already exists.\n\n"
                f"Existing: {dest_folder}\n"
                f"New: {self.merged_pack_path}\n\n"
                "Replace it?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply != QMessageBox.StandardButton.Yes:
                self.log_output.appendPlainText("⏭️ Import cancelled - pack already exists")
                return
                
            # Remove existing pack
            shutil.rmtree(dest_folder, ignore_errors=True)
            self.log_output.appendPlainText(f"  ✓ Removed existing pack")
        
        # Copy merged pack to Minecraft directory
        shutil.copytree(self.merged_pack_path, dest_folder)
        self.log_output.appendPlainText(f"  ✓ Copied to: {dest_folder}")
        
        # Update installed packs state
        if hasattr(self.parent, 'scan_local'):
            self.parent.scan_local()
            if hasattr(self.parent, 'refresh_installed'):
                self.parent.refresh_installed()
        
        self.log_output.appendPlainText(f"\n✅ Merged pack imported to Minecraft!")
        self.log_output.appendPlainText(f"   UUID: {uuid}")
        self.log_output.appendPlainText(f"   Location: {dest_folder}")
        self.log_output.appendPlainText(f"\n✨ Restart Minecraft to see it in the dressing room!")
        
        QMessageBox.information(
            self, 
            "Import Successful", 
            f"Merged pack imported to Minecraft!\n\n"
            f"UUID: {uuid}\n"
            f"Encrypted: {'Yes' if encrypt_success else 'No'}\n\n"
            f"Restart Minecraft to see it in the dressing room."
        )
        
     except Exception as e:
        self.log_output.appendPlainText(f"\n❌ Import failed: {e}")
        import traceback
        self.log_output.appendPlainText(f"Traceback: {traceback.format_exc()}")
        QMessageBox.critical(self, "Import Failed", f"Failed to import merged pack: {e}")

# ---------------- MAIN APP ----------------
class App(QMainWindow):
    def __init__(self, splash):
        super().__init__()
        self.splash = splash
        self.downloading = False
        self.porter_running = False
        self.porter_folder = None
        self.legacy_packs = []
        self.injection_worker = None
        self.sound = None
        self.sound_enabled = True  # Sound enabled by default
        self.setWindowTitle("Melancholy")
        self.setWindowIcon(QIcon(resource_path("icon.ico")))
        self.resize(1300, 900)
        
        # Set transparent background
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)
        
        # Create background widget
        self.background = BackgroundWidget(self)
        self.background.lower()
        self.background.setGeometry(self.rect())
        
        # Initialize sound
        self.init_sound()
        
        # Play startup sound if enabled
        if self.sound_enabled:
            QTimer.singleShot(100, self.play_startup_sound)
        
        self.state = load_state()
        if "known" not in self.state or not isinstance(self.state["known"], list):
            self.state["known"] = []
            
        self.legacy_state = load_legacy_state()
        
        self.splash.show_message("Scanning local packs...")
        self.scan_local()

        central = QWidget()
        self.setCentralWidget(central)
        
        central.setAttribute(Qt.WA_StyledBackground)
        central.setStyleSheet("QWidget { background-color: transparent; }")
        
        main_layout = QVBoxLayout(central)

        # Top bar
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        
        # Sound toggle button (replaces Set Sound button)
        self.sound_toggle_btn = QPushButton("🔊 Sound On")
        self.sound_toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(0,150,0,100);
                border: 1px solid rgba(0,255,0,150);
                border-radius: 5px;
                color: white;
                padding: 5px 15px;
                margin-right: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(0,150,0,150);
            }
        """)
        self.sound_toggle_btn.clicked.connect(self.toggle_sound)
        top_bar.addWidget(self.sound_toggle_btn)
        
        credits_btn = QPushButton("Credits")
        credits_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(0,0,0,100);
                border: 1px solid rgba(255,255,255,100);
                border-radius: 5px;
                color: white;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: rgba(0,0,0,150);
                border: 1px solid white;
            }
        """)
        credits_btn.clicked.connect(self.show_credits)
        top_bar.addWidget(credits_btn)
        main_layout.addLayout(top_bar)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget { background-color: transparent; }
            QTabWidget::pane { 
                background-color: rgba(20, 20, 20, 180);
                border: 1px solid rgba(255, 255, 255, 50);
                border-radius: 10px;
            }
        """)
        main_layout.addWidget(self.tabs)
        
        self.splash.show_message("Building interface...")
        
        self.store_tab = QWidget()
        self.installed_tab = QWidget()
        self.porter_tab = QWidget()
        self.merger_tab = MergerTab(self)  # Pass self as parent
        
        for tab in [self.store_tab, self.installed_tab, self.porter_tab]:
            tab.setAttribute(Qt.WA_StyledBackground)
            tab.setStyleSheet("background-color: transparent;")
            
        self.tabs.addTab(self.store_tab, "Store")
        self.tabs.addTab(self.installed_tab, "Installed")
        self.tabs.addTab(self.porter_tab, "Porter")
        self.tabs.addTab(self.merger_tab, "Pack Merger")

        self.splash.show_message("Building store...")
        self.build_store()
        
        self.splash.show_message("Building installed tab...")
        self.build_installed()
        
        self.splash.show_message("Building porter...")
        self.build_porter()
        
        self.splash.show_message("Loading store...")
        self.load_store()
        
        self.tabs.currentChanged.connect(lambda _: self.refresh_installed())

        # Fade-in animation
        self.setWindowOpacity(0)
        self.fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_anim.setDuration(1500)
        self.fade_anim.setStartValue(0)
        self.fade_anim.setEndValue(1)
        self.fade_anim.setEasingCurve(QEasingCurve.InOutCubic)
        self.fade_anim.start()
        
        QTimer.singleShot(2000, self.splash.close)
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.background.setGeometry(self.rect())
        
    def init_sound(self):
        """Initialize sound system - looks for startup_sound.wav in multiple locations"""
        try:
            self.sound = QSoundEffect()
            self.sound.setLoopCount(1)
            self.sound.setVolume(0.8)
            
            # Look for startup sound in multiple locations
            sound_locations = [
                Path(os.getcwd()) / "startup_sound.wav",  # Current directory
                Path(os.getcwd()) / "startup_sound.mp3",  # Current directory mp3
                Path(os.getcwd()) / "assets" / "startup_sound.wav",  # Assets folder
                SOUND_FILE,  # AppData location
                Path(os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__)) / "startup_sound.wav"  # Script directory
            ]
            
            sound_found = False
            for sound_path in sound_locations:
                if sound_path.exists():
                    self.sound.setSource(QUrl.fromLocalFile(str(sound_path)))
                    print(f"Found startup sound: {sound_path}")
                    sound_found = True
                    break
            
            if sound_found:
                self.sound_available = True
                print("✅ Startup sound loaded successfully")
            else:
                self.sound_available = False
                print("ℹ️ No startup sound found - using fallback beeps")
                
        except Exception as e:
            print(f"Sound system not available: {e}")
            self.sound_available = False
            self.sound = None
    
    def toggle_sound(self):
        """Toggle startup sound on/off"""
        self.sound_enabled = not self.sound_enabled
        
        if self.sound_enabled:
            self.sound_toggle_btn.setText("🔊 Sound On")
            self.sound_toggle_btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(0,150,0,100);
                    border: 1px solid rgba(0,255,0,150);
                    border-radius: 5px;
                    color: white;
                    padding: 5px 15px;
                    margin-right: 10px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: rgba(0,150,0,150);
                }
            """)
            # Test the sound to confirm it's working
            self.play_startup_sound()
        else:
            self.sound_toggle_btn.setText("🔇 Sound Off")
            self.sound_toggle_btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(100,100,100,100);
                    border: 1px solid rgba(255,255,255,100);
                    border-radius: 5px;
                    color: white;
                    padding: 5px 15px;
                    margin-right: 10px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: rgba(150,150,150,150);
                }
            """)
        
    def play_startup_sound(self):
        """Play startup sound only if enabled"""
        if not self.sound_enabled:
            return
            
        try:
            if self.sound_available and self.sound and self.sound.source().isValid():
                self.sound.play()
                print("Playing startup sound")
            else:
                # Only use beeps as absolute last resort
                try:
                    import winsound
                    winsound.Beep(800, 200)
                    winsound.Beep(1000, 200)
                    winsound.Beep(1200, 400)
                except:
                    pass  # Silently fail if no sound available
        except:
            pass

    def set_porter_folder_from_drop(self, path):
        self.porter_folder = path
        if hasattr(self, 'porter_status'):
            self.porter_status.append(f"📂 Selected folder via drag-drop: {path}")

    # -------------- Local scan --------------
    def scan_local(self):
        self.state["known"] = []
        for folder in SKIN_PACK_DIR.iterdir():
            if not folder.is_dir(): continue
            manifest = find_manifest(folder)
            if not manifest: continue
            try:
                uuid, version = read_manifest(manifest)
            except: continue
            self.state["known"].append({
                "uuid": uuid,
                "version": version,
                "path": str(folder),
                "store_name": folder.name,
                "source": "local"
            })
        save_state(self.state)

    # -------------- Credits --------------
    def show_credits(self):
        discord_url = "https://discord.gg/3x3M289anm"
        msg = QMessageBox(self)
        msg.setWindowTitle("Credits")
        msg.setText(
            "Melancholy Skin Pack Manager\n\n"
            "Created by: TrxpVoidz (Founder of Ecliptix)\n"
            "Special Thanks to a6wwp for the SkinPack Merger script!\n\n"
            "Join the official Discord server below!"
        )
        msg.setStyleSheet("""
            QMessageBox {
                background-color: rgba(20, 20, 20, 230);
                color: white;
            }
            QMessageBox QLabel {
                color: white;
            }
            QPushButton {
                background-color: rgba(255,255,255,50);
                border: 1px solid rgba(255,255,255,100);
                border-radius: 5px;
                color: white;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: rgba(255,255,255,100);
            }
        """)
        discord_btn = msg.addButton("Open Discord", QMessageBox.ActionRole)
        msg.addButton(QMessageBox.Close)
        msg.exec()
        if msg.clickedButton() == discord_btn:
            QDesktopServices.openUrl(QUrl(discord_url))

    # ---------------- STORE ----------------
    def build_store(self):
        root = QVBoxLayout(self.store_tab)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { background-color: transparent; border: none; }")
        root.addWidget(self.scroll)

        self.grid_host = QWidget()
        self.grid_host.setStyleSheet("background-color: transparent;")
        self.grid = QGridLayout(self.grid_host)
        self.grid.setSpacing(16)
        self.scroll.setWidget(self.grid_host)

        self.progress = QProgressBar()
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setFixedHeight(140)
        root.addWidget(self.progress)
        root.addWidget(self.log)

    def load_store(self):
        self.store_loader = StoreLoader()
        self.store_loader.finished.connect(self.populate_store)
        self.store_loader.error.connect(lambda e: QMessageBox.critical(self, "Store error", e))
        self.store_loader.start()

    def populate_store(self, packs):
        while self.grid.count():
            w = self.grid.takeAt(0).widget()
            if w:
                w.deleteLater()

        row = col = 0
        for pack in packs:
            card = StoreCard(pack, self.state, self.start_download, self.uninstall_pack)
            self.grid.addWidget(card, row, col)
            col += 1
            if col == 4:
                col = 0
                row += 1

    def start_download(self, pack):
        if self.downloading:
            QMessageBox.warning(self, "Download Running", "A download is already in progress.")
            return

        self.downloading = True
        self.progress.setValue(0)
        self.log.clear()

        self.worker = DownloadWorker(pack["zip_url"])
        self.worker.progress.connect(self.progress.setValue)
        self.worker.log.connect(self.log.append)
        self.worker.finished.connect(lambda tmp: self.finish_download(tmp, pack))
        self.worker.error.connect(self.download_error)
        self.worker.start()

    def finish_download(self, tmp, pack):
        self.downloading = False
        self.install_pack(tmp, pack)

    def download_error(self, err):
        self.downloading = False
        QMessageBox.critical(self, "Download Error", err)

    # ---------------- INSTALL PACK ----------------
    def install_pack(self, tmp_zip: Path, pack):
        self.log.append("Preparing installation…")

        try:
            temp_extract = SKIN_PACK_DIR / "__temp_install__"
            if temp_extract.exists():
                shutil.rmtree(temp_extract)
            temp_extract.mkdir()

            with zipfile.ZipFile(tmp_zip, "r") as z:
                z.extractall(temp_extract)

            manifest_path = find_manifest(temp_extract)
            if not manifest_path:
                raise Exception("manifest.json not found in pack")

            new_uuid, version = read_manifest(manifest_path)

            existing = next(
                (info for info in self.state.get("known", [])
                 if info.get("uuid") == new_uuid),
                None
            )

            dest_folder = SKIN_PACK_DIR / new_uuid

            if existing:
                msg = QMessageBox(self)
                msg.setWindowTitle("Existing Pack Found")
                msg.setText(
                    "A pack with the same UUID already exists.\n\n"
                    f"Installed: {existing.get('store_name')}\n"
                    f"UUID: {new_uuid}\n\n"
                    "Choose what to do:"
                )
                msg.setStyleSheet("""
                    QMessageBox {
                        background-color: rgba(20, 20, 20, 230);
                        color: white;
                    }
                    QMessageBox QLabel {
                        color: white;
                    }
                    QPushButton {
                        background-color: rgba(255,255,255,50);
                        border: 1px solid rgba(255,255,255,100);
                        border-radius: 5px;
                        color: white;
                        padding: 5px 15px;
                    }
                    QPushButton:hover {
                        background-color: rgba(255,255,255,100);
                    }
                """)
                replace_btn = msg.addButton("Replace", QMessageBox.AcceptRole)
                cancel_btn = msg.addButton("Cancel", QMessageBox.RejectRole)
                msg.exec()

                if msg.clickedButton() == cancel_btn:
                    self.log.append("Install cancelled.")
                    shutil.rmtree(temp_extract, ignore_errors=True)
                    return

                old_path = Path(existing["path"])
                if old_path.exists():
                    shutil.rmtree(old_path, ignore_errors=True)

                self.state["known"].remove(existing)

            if dest_folder.exists():
                shutil.rmtree(dest_folder, ignore_errors=True)

            shutil.move(temp_extract, dest_folder)

            self.state["known"].append({
                "uuid": new_uuid,
                "version": version,
                "path": str(dest_folder),
                "store_name": pack.get("name", new_uuid),
                "source": "store"
            })

            save_state(self.state)

            self.log.append("✔ Installation complete.")
            self.refresh_installed()
            self.load_store()

            # Success animation
            self.fade_anim = QPropertyAnimation(self, b"windowOpacity")
            self.fade_anim.setDuration(300)
            self.fade_anim.setKeyValueAt(0, 1)
            self.fade_anim.setKeyValueAt(0.5, 0.8)
            self.fade_anim.setKeyValueAt(1, 1)
            self.fade_anim.start()

        except Exception as e:
            QMessageBox.critical(self, "Install failed", str(e))
            self.log.append(f"Error: {e}")

    # ---------------- INSTALLED TAB ----------------
    def build_installed(self):
        layout = QVBoxLayout(self.installed_tab)
        layout.setSpacing(12)

        btn_row = QHBoxLayout()

        refresh = QPushButton("Refresh")
        refresh.setStyleSheet("""
            QPushButton {
                background-color: rgba(255,255,255,50);
                border: 1px solid rgba(255,255,255,100);
                border-radius: 5px;
                color: white;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: rgba(255,255,255,100);
            }
        """)
        refresh.clicked.connect(self.refresh_installed)
        btn_row.addWidget(refresh)

        wipe = QPushButton("Safe Wipe")
        wipe.setStyleSheet("""
            QPushButton {
                background-color: rgba(255,0,0,50);
                border: 1px solid rgba(255,0,0,100);
                border-radius: 5px;
                color: white;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: rgba(255,0,0,100);
            }
        """)
        wipe.clicked.connect(self.safe_wipe)
        btn_row.addWidget(wipe)

        delete_btn = QPushButton("Delete Selected")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255,0,0,50);
                border: 1px solid rgba(255,0,0,100);
                border-radius: 5px;
                color: white;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: rgba(255,0,0,100);
            }
        """)
        delete_btn.clicked.connect(self.delete_selected)
        btn_row.addWidget(delete_btn)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.import_drop = DragDropWidget(
            "Click or Drag & Drop ZIP Here to Import",
            file_types=[".zip"],
            folder_mode=False,
            callback=self.handle_import_drop
        )
        layout.addWidget(self.import_drop)

        self.installed_list = QListWidget()
        self.installed_list.setSelectionMode(QListWidget.SingleSelection)
        self.installed_list.itemClicked.connect(self.show_installed_preview)
        layout.addWidget(self.installed_list)

        self.installed_preview = QLabel("Select a pack")
        self.installed_preview.setFixedSize(256, 256)
        self.installed_preview.setAlignment(Qt.AlignCenter)
        self.installed_preview.setStyleSheet("""
            QLabel {
                background-color: rgba(0,0,0,100);
                border: 1px solid rgba(255,255,255,50);
                border-radius: 10px;
                color: white;
            }
        """)
        layout.addWidget(self.installed_preview, alignment=Qt.AlignCenter)

        self.refresh_installed()

    def handle_import_drop(self, path):
        try:
            self.install_pack(Path(path), {"name": Path(path).stem})
            self.refresh_installed()
        except Exception as e:
            QMessageBox.critical(self, "Import Error", str(e))

    def refresh_installed(self):
        self.scan_local()
        self.installed_list.clear()

        for info in self.state.get("known", []):
            item = QListWidgetItem(info.get("store_name", "Unnamed Pack"))
            item.setData(Qt.UserRole, info)
            self.installed_list.addItem(item)

    def show_installed_preview(self, item):
        info = item.data(Qt.UserRole)
        folder = Path(info.get("path", ""))

        thumb = folder / "thumbnail.png"
        if thumb.exists():
            pix = QPixmap(str(thumb))
            self.installed_preview.setPixmap(
                pix.scaled(256, 256, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        else:
            self.installed_preview.setText("No thumbnail found")

    def delete_selected(self):
        item = self.installed_list.currentItem()
        if not item:
            return

        info = item.data(Qt.UserRole)

        reply = QMessageBox.question(
            self,
            "Delete Pack",
            f"Delete {info.get('store_name', 'pack')}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        shutil.rmtree(info.get("path", ""), ignore_errors=True)

        self.state["known"].remove(info)
        save_state(self.state)

        self.refresh_installed()
        self.load_store()

    def safe_wipe(self):
        reply = QMessageBox.question(
            self,
            "Safe Wipe",
            "Remove ALL installed skin packs?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        for info in list(self.state.get("known", [])):
            shutil.rmtree(info.get("path", ""), ignore_errors=True)

        self.state["known"] = []
        save_state(self.state)

        self.refresh_installed()
        self.load_store()

    # ---------------- PORTER TAB ----------------
    def build_porter(self):
        layout = QVBoxLayout(self.porter_tab)

        title = QLabel("Porter – Copy → Encrypt → Import")
        title.setStyleSheet("color: white; font-size: 16px; font-weight: bold; padding: 10px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.porter_folder_btn = QPushButton("Select Folder")
        self.porter_folder_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255,255,255,50);
                border: 1px solid rgba(255,255,255,100);
                border-radius: 5px;
                color: white;
                padding: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(255,255,255,100);
            }
        """)
        self.porter_folder_btn.clicked.connect(self.select_porter_folder)
        layout.addWidget(self.porter_folder_btn)

        self.manifest_dropdown = QComboBox()
        self.manifest_dropdown.addItems(MANIFEST_OPTIONS.keys())
        layout.addWidget(self.manifest_dropdown)

        self.porter_drop = DragDropWidget(
            "Drag & Drop Skin Pack Folder Here",
            folder_mode=True,
            callback=self.set_porter_folder_from_drop
        )
        layout.addWidget(self.porter_drop)

        self.porter_progress = QProgressBar()
        self.porter_progress.setValue(0)
        layout.addWidget(self.porter_progress)

        self.porter_run_btn = QPushButton("Run Porter")
        self.porter_run_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(0,255,0,50);
                border: 1px solid rgba(0,255,0,100);
                border-radius: 5px;
                color: white;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(0,255,0,100);
            }
        """)
        self.porter_run_btn.clicked.connect(self.run_porter)
        layout.addWidget(self.porter_run_btn)

        self.porter_status = QTextEdit()
        self.porter_status.setReadOnly(True)
        layout.addWidget(self.porter_status)

    def select_porter_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Skin Pack Folder")
        if folder:
            self.porter_folder = folder
            self.porter_status.append(f"Selected folder: {folder}")

    def run_porter(self):
        if self.porter_running:
            QMessageBox.warning(self, "Porter Running", "Porter is already processing.")
            return

        if not hasattr(self, "porter_folder") or not self.porter_folder:
            QMessageBox.warning(self, "Porter", "Select a folder first")
            return

        self.porter_running = True
        self.porter_progress.setValue(0)

        try:
            folder = self.porter_folder
            choice = self.manifest_dropdown.currentText()

            self.porter_status.append("📁 Copying pack...")
            temp_copy = copy_pack_first(folder)
            self.porter_progress.setValue(25)

            self.porter_status.append("🧾 Setting manifest...")
            setup_porter(temp_copy, choice)
            self.porter_progress.setValue(50)

            self.porter_status.append("🔐 Encrypting...")
            tool_porter(temp_copy)
            self.porter_progress.setValue(75)

            self.porter_status.append("🔎 Checking for existing packs...")
            self.remove_existing_manifest_pack(temp_copy)

            self.porter_status.append("📦 Importing...")
            import_to_minecraft_porter(temp_copy)

            self.porter_progress.setValue(100)

            self.porter_status.append("✅ Done")
            
            self.fade_anim = QPropertyAnimation(self, b"windowOpacity")
            self.fade_anim.setDuration(300)
            self.fade_anim.setKeyValueAt(0, 1)
            self.fade_anim.setKeyValueAt(0.5, 0.8)
            self.fade_anim.setKeyValueAt(1, 1)
            self.fade_anim.start()

        except Exception as e:
            QMessageBox.critical(self, "Porter Error", str(e))
            self.porter_status.append(f"❌ {e}")

        finally:
            self.porter_running = False

    def uninstall_pack(self, pack):
        name = pack.get("name")

        existing = next(
            (info for info in self.state.get("known", [])
             if info.get("store_name") == name),
            None
        )

        if not existing:
            QMessageBox.information(self, "Uninstall", "Pack not found.")
            return

        reply = QMessageBox.question(
            self,
            "Uninstall Pack",
            f"Uninstall {name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        path = existing.get("path")
        if path and os.path.exists(path):
            shutil.rmtree(path, ignore_errors=True)

        self.state["known"].remove(existing)
        save_state(self.state)

        self.refresh_installed()
        self.load_store()

    def remove_existing_manifest_pack(self, temp_folder):
        manifest = Path(temp_folder) / "manifest.json"
        if not manifest.exists():
            return
        try:
            uuid, _ = read_manifest(manifest)
        except:
            return
        existing = next((info for info in self.state.get("known", [])
                         if info.get("uuid") == uuid), None)
        if existing:
            shutil.rmtree(existing.get("path", ""), ignore_errors=True)
            self.state["known"].remove(existing)
            save_state(self.state)
            self.refresh_installed()

# ---------------- PORTER / ENCRYPTION FUNCTIONS ----------------
fileSkip = {'manifest.json', 'pack_icon.png'}
fileSkipForce = {'contents.json', 'signatures.json'}
fileSkipFull = fileSkip | fileSkipForce
key = None
encryptedVariable = None
inputPathSkinpack = None
FIXED_KEY = 's5s5ejuDru4uchuF2drUFuthaspAbepE'

MANIFEST_OPTIONS = {
    "1st Birthday": '{"header":{"version":[1,0,5],"description":"pack.description","name":"pack.name","uuid":"202539ce-e6c5-40b5-a4a1-4296277d18f6"},"modules":[{"version":[1,0,5],"type":"skin_pack","uuid":"ef6f8811-933b-4673-b285-c02cf583e56d"}],"format_version":1}',
    "1st Animal Friends": '{"format_version":1,"header":{"name":"1st Animal Friends","uuid":"9a9fa850-0b5e-11ee-9a0f-a795af90f04f","version":[1,0,3]},"modules":[{"type":"skin_pack","uuid":"a162eb70-0b5e-11ee-86cb-9d9dd4413780","version":[1,0,3]}]}',
    "Beap Borp HD": '{"header":{"name":"BeepBorpHD","version":[1,0,4],"uuid":"18215a23-e943-4004-b799-48fdcc926799"},"modules":[{"version":[1,0,4],"type":"skin_pack","uuid":"7eb2682d-9532-4db6-aa7e-b4512e347f2e"}],"format_version":1}',
    "Blockheads": '{"header": {"name": "Blockheads","version": [1,0,0],"uuid": "8b8362a3-cd8c-4f48-9a49-b494659513b6"},"modules": [{"version": [1,0,0],"type": "skin_pack","uuid": "c47ad348-0f17-438f-ae11-6c001445a947"}],"format_version": 1}',
    "Crafty Costumes": '{"format_version":1,"header":{"name":"CraftyCostumes","uuid":"c35ad990-3dc5-4179-bfe9-6f323d94f0b2","version":[1,0,11]},"modules":[{"type":"skin_pack","uuid":"a568d136-49ec-4287-bbe1-29110643a489","version":[1,0,11]}]}',
    "Creepy Creatures": '{"header": {"name": "Creepy Creatures","version": [1,0,1],"uuid": "dd44b7d6-2c05-48a2-bfdf-f78596b59f44"},"modules": [{"version": [1,0,1],"type": "skin_pack","uuid": "f84c0b4a-7b0b-4ed3-9125-dffa2815809f"}],"format_version": 1}',
    "Cute Kitty HD": '{"header":{"name":"CuteKittyHD","version":[1,0,10],"uuid":"7124cf9d-5d0e-4865-9656-03c1f04039c3"},"modules":[{"version":[1,0,10],"type":"skin_pack","uuid":"e9c920a2-fbb1-430a-a951-f240f48c5abc"}],"format_version":1}',
    "Cyborg Skin Pack": '{"header": {"description": "Cyborg Skin Pack","name": "Cyborg Skin Pack","version": [1,0,4],"uuid": "deb3b920-be8a-4b62-b8b1-5c9c7a4272f9"},"modules": [{"version": [1,0,4],"type": "skin_pack","uuid": "94d873ba-6fe7-4374-b5a4-cb36a285fd49"}],"format_version": 1}',
    "Dress Code": '{"header": {"name": "Dress Code","version": [1,0,6],"uuid": "f47107de-385d-4e15-8a5a-cdd40a1df33d"},"modules": [{"version": [1,0,6],"type": "skin_pack","uuid": "683735a6-44f6-40e2-97b0-5039f5251353"}],"format_version": 1}',
    "Builders & Biomes": '{"format_version":1,"header":{"name":"BuildersBiomes","uuid":"05ead86c-572c-40c8-8cb0-8733a7894185","version":[1,0,4]},"modules":[{"type":"skin_pack","uuid":"9d6e6755-42dc-4ac9-8cc8-374a4ca9a9ab","version":[1,0,4]}]}',
    "Haipu": '{"format_version":1,"header":{"name":"Haipu","uuid":"f46a707a-36c7-45d0-becf-88c5e2f4257d","version":[1,0,3]},"modules":[{"type":"skin_pack","uuid":"2791e9a8-e380-4e14-8f9c-6d3c3aa3476b","version":[1,0,3]}]}',
    "Heartfelt": '{"header": {"name": "Heartfelt","version": [1, 0, 0],"uuid": "72fe6a92-121d-40a7-bb47-d08a41579d32"},"modules": [{"version": [1, 0, 0],"type": "skin_pack","uuid": "31a2afa5-b024-444a-822b-46d4bd1dd2c6"}],"format_version": 1}',
    "Lunar New Year of The Ox": '{"header":{"name":"Lunar_New_Year_of_The_Ox","version":[1,0,12],"uuid":"96e8daad-3d7a-4818-bc25-2c815fb3bbc2"},"modules":[{"version":[1,0,12],"type":"skin_pack","uuid":"bed5e4b3-b108-4448-b608-0908e7905db5"}],"format_version":1}',
    "Minecraft x Uniqlo Skins Vol 2": '{"format_version":1,"header":{"name":"pack.name","uuid":"18219eb4-d96f-4b8b-999a-6cbd1b65c58d","version":[1,0,5]},"modules":[{"type":"skin_pack","uuid":"77260103-f950-4280-9a17-89da92391898","version":[1,0,5]}],"metadata":{"authors":["Mike Gaboury"]}}',
    "Norse Mythology Bonus Skins": '{"format_version":1,"header":{"name":"pack.name","uuid":"6dd86351-0191-4a3e-85cf-2a81647b830c","version":[1,0,5]},"modules":[{"type":"skin_pack","uuid":"a29a25d5-4b28-4ddb-a57d-ce272cf5fc39","version":[1,0,5]}]}',
    "Notice Me Senpai HD": '{"header":{"name":"NoticeMeHD","version":[1,0,2],"uuid":"4bf4b0f7-dec8-4cde-b6f4-0222972d0aac"},"modules":[{"version":[1,0,2],"type":"skin_pack","uuid":"39e6f01a-da8a-4106-b66f-a643fbaee1c9"}],"format_version":1}',
    "Onesie Skeletons": '{"header":{"name":"OnesieSkeletons","version":[1,0,3],"uuid":"87e7495b-a219-4a65-837c-654ee97ad8f6"},"modules":[{"version":[1,0,3],"type":"skin_pack","uuid":"d164c220-a005-466d-ac87-d096e08337d7"}],"format_version":1}',
    "Popya": '{"format_version":1,"header":{"name":"Popya","uuid":"e3f6e616-ca3c-492c-bbbf-4d41b859b8cd","version":[1,0,5]},"modules":[{"type":"skin_pack","uuid":"52e87833-4d00-47bb-abb1-62731227a037","version":[1,0,5]}]}',
    "Rockin' Holiday": '{"format_version":1,"header":{"name":"RockinHoliday","uuid":"0887d1fd-a752-47d9-a119-b47e6a5fac67","version":[1,0,7]},"modules":[{"type":"skin_pack","uuid":"d8c125af-9c41-4e0c-998f-52961a0c2a0d","version":[1,0,7]}]}',
    "Safari Adventurers": '{"header": {"name": "Safari Adventurers Skin Pack","version": [1,0,1],"uuid": "219655ca-39b4-4ec4-b04b-281a6ac1e3e5"},"modules": [{"version": [1,0,1],"type": "skin_pack","uuid": "3ad7c0f9-13a0-4e19-861a-04f336eec2a8"}],"format_version": 1}',
    "Sailor Uniform": '{"format_version":1,"header":{"name":"Sailor Uniform","uuid":"00e87c90-b734-4021-88b3-7cca436747cc","version":[1,0,10]},"modules":[{"type":"skin_pack","uuid":"73b4293b-c91b-4d9b-9f12-d00d9455d2b9","version":[1,0,10]}]}',
    "Stay Warm HD": '{"header":{"name":"StayWarmHD","version":[1,0,3],"uuid":"85a2ede9-cce0-42e4-96af-c9fd1e913b37"},"modules":[{"version":[1,0,3],"type":"skin_pack","uuid":"b0afc709-4c72-4578-953b-146f3270bcb7"}],"format_version":1}',
    "Summer Beach Party": '{"format_version": 1,"metadata": {"authors": ["GoE-Craft","All Rights Reserved."]},"header": {"name": "SummerBeachPartySkinPack","uuid": "6fef41b8-4000-4afc-ae5d-03b08755a8e4","version": [1,0,0]},"modules": [{"type": "skin_pack","uuid": "683da9cd-a504-4001-b0bf-400991218560","version": [1,0,0]}]}',
    "Summer Gift": '{"header":{"name":"pack.SummerGift","version":[1,0,1],"uuid":"aed5c500-83e9-44f6-9213-618a9dd32e3e"},"modules":[{"version":[1,0,1],"type":"skin_pack","uuid":"c9fe656a-9cad-48a9-97db-860e1f90021b"}],"format_version":1}',
    "Superman": '{"format_version":1,"header":{"name":"pack.name","version":[1,0,6],"uuid":"50a5f49f-86b3-3b7e-3060-d40000f59dcb"},"modules":[{"version":[1,0,6],"type":"skin_pack","uuid":"0e837629-6794-2d56-76ef-174bb282f3ca"}]}',
    "Timless Toys": '{"format_version":1,"header":{"name":"Timeless Toys Skins","uuid":"727df6bb-5392-4b92-b262-54545731116a","version":[1,0,3]},"modules":[{"type":"skin_pack","uuid":"cbc1286c-aa81-427a-9360-0a9c4042da0a","version":[1,0,3]}]}',
    "Vibrant Adventurers Volume 1": '{"header":{"name":"VibrantAdventurersV1","version":[1,0,1],"uuid":"5cfc95c0-7490-4bdd-a5f9-d1164decbb1b"},"modules":[{"version":[1,0,0],"type":"skin_pack","uuid":"d2dbc6e4-956e-4c7d-83b1-70437a168f3a"}],"format_version":1}',
    "Vibrant Adventurers Volume 2": '{"header":{"name":"VibrantAdventurersV2","version":[1,0,3],"uuid":"b3b5a06a-7dc6-4ec6-a3cc-89c46f9a91e2"},"modules":[{"version":[1,0,0],"type":"skin_pack","uuid":"7e4831cb-9912-4cd3-83a0-76ffee9104d5"}],"format_version":1}',
    "Vibrant Adventurers Volume 3": '{"header":{"name":"VibrantAdventurersV3","version":[1,0,1],"uuid":"ba692d28-b4ca-40ce-9e0e-7f7960baee13"},"modules":[{"version":[1,0,0],"type":"skin_pack","uuid":"96456913-21cc-4b12-99bb-a6f937c9bec1"}],"format_version":1}',
    "Wild West Adventurers": '{"header": {"name": "Cowboys and Indians","version": [1,0,4],"uuid": "222b52e7-d292-4765-838c-66d8cbb4719d"},"modules": [{"version": [1,0,4],"type": "skin_pack","uuid": "942e9425-18c8-4246-9a90-0af9804e3d40"}],"format_version": 1}',
    "Winter Whimsy": '{"header": {"name": "WinterWhimsy","version": [1, 0, 0],"uuid": "163b24c0-5989-4457-a68f-fbbb6099c842"},"modules": [{"version": [1, 0, 0],"type": "skin_pack","uuid": "3b8b7a48-b62a-44a7-b1ff-d93098c31cc6"}],"format_version": 1}',
    "Young Fashion": '{"header": {"name": "Young Fashion","version": [1,0,1],"uuid": "7fdde03a-8dce-4b76-a969-6484d79358fd"},"modules": [{"version": [1,0,1],"type": "skin_pack","uuid": "944a69ab-c924-4155-ad7b-a4f13742fb86"}],"format_version": 1}',
    "Young Gru": '{"header":{"name":"Young Gru","version":[1,0,8],"uuid":"670f5c25-c3a2-4a87-b48c-313b8ee35578"},"modules":[{"version":[1,0,8],"type":"skin_pack","uuid":"e84a3684-808a-42e5-8a68-610c3cb8adb8"}],"format_version":1}'
}

def generateKey(pathOrByte, isPath, variableOrFile):
    global key, encryptedVariable
    key = FIXED_KEY
    cipher = Cipher(algorithms.AES(key.encode('utf-8')), modes.CFB8(key[:16].encode('utf-8')))
    encryptor = cipher.encryptor()
    if isPath:
        with open(pathOrByte, 'rb') as file:
            data = file.read()
        with open(pathOrByte, 'wb') as file:
            file.write(encryptor.update(data) + encryptor.finalize())
    elif variableOrFile is True:
        encryptedVariable = encryptor.update(pathOrByte) + encryptor.finalize()
    else:
        with open(variableOrFile, 'wb') as file:
            file.write(encryptor.update(pathOrByte) + encryptor.finalize())

def setup_porter(inputPath, manifestChoice):
    global inputPathSkinpack
    inputPathSkinpack = os.path.join(rf'{inputPath}', '')
    manifest_path = os.path.join(inputPathSkinpack, 'manifest.json')
    with open(manifest_path, 'w', encoding='utf-8') as f:
        f.write(MANIFEST_OPTIONS[manifestChoice])

def tool_porter(inputPath):
    global key, inputPathSkinpack, encryptedVariable
    fileJSONContents = {"version": 1, "content": []}
    for path, dirs, files in os.walk(inputPathSkinpack):
        if os.path.basename(path).lower() == 'texts': continue
        for file in files:
            pathFile = os.path.join(path, file)
            doEncrypt, doNotAdd = True, False
            for pathFileSkip in fileSkipFull:
                if pathFile.endswith(pathFileSkip):
                    doEncrypt = False
                    if pathFileSkip in fileSkipForce:
                        doNotAdd = True
                    break
            relativePath = pathFile.replace(inputPathSkinpack, "").replace("\\", "/")
            if doEncrypt:
                generateKey(pathFile, True, True)
                fileJSONContents["content"].append({'key': key, 'path': relativePath})
            elif not doNotAdd:
                fileJSONContents["content"].append({'path': relativePath})
    contents_path = os.path.join(inputPathSkinpack, 'contents.json')
    with open(contents_path, 'wb') as fileContents:
        manifest_path = os.path.join(inputPathSkinpack, 'manifest.json')
        with open(manifest_path, 'r') as file:
            jsonManifest = json.load(file)
            jsonUUID = jsonManifest['header']['uuid']
        with open(manifest_path, 'rb') as fileManifest:
            hashVal = b64encode(sha256(fileManifest.read()).digest()).decode()
            fileJSONSignatures = [{"hash": hashVal, "path": "manifest.json"}]
            sig_path = os.path.join(inputPathSkinpack, 'signatures.json')
            generateKey(json.dumps(fileJSONSignatures, separators=(',', ':')).encode('utf-8'), False, sig_path)
            fileJSONContents["content"].append({'key': key, 'path': 'signatures.json'})
        headerByte = b'\xfc\xb9\xcf\x9b\x00\x00\x00\x00\x00\x00\x00\x00\x24'
        empty = bytes(256)
        generateKey(json.dumps(fileJSONContents, separators=(',', ':')).encode('utf-8'), False, True)
        headerFinal = empty[:4] + headerByte + jsonUUID.encode('utf-8') + empty[53:] + encryptedVariable
        fileContents.write(headerFinal)

def import_to_minecraft_porter(temp_path):
    manifest = Path(temp_path) / "manifest.json"
    if not manifest.exists():
        raise Exception("manifest.json missing after porter")
    data = json.loads(manifest.read_text(encoding="utf-8"))
    uuid = data["header"]["uuid"]
    dest_folder = SKIN_PACK_DIR / uuid
    if dest_folder.exists():
        shutil.rmtree(dest_folder, ignore_errors=True)
    shutil.move(temp_path, dest_folder)

def copy_pack_first(folder):
    temp_root = os.path.join(tempfile.gettempdir(), "porter_temp")
    if os.path.exists(temp_root):
        shutil.rmtree(temp_root, ignore_errors=True)
    os.makedirs(temp_root, exist_ok=True)
    new_name = f"{os.path.basename(folder)}_PORTED"
    temp_dest = os.path.join(temp_root, new_name)
    shutil.copytree(folder, temp_dest)
    return temp_dest

# ---------------- RUN ----------------
if __name__ == "__main__":
    myappid = 'ecliptix.melancholy.1.0'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path("icon.ico")))
    
    # Set application-wide transparent style
    app.setStyle('Fusion')
    
    # Create and show loading screen
    splash = LoadingScreen()
    splash.show()
    app.processEvents()
    
    # Create main window (loading screen will be closed after initialization)
    win = App(splash)
    
    # Show main window after a delay
    QTimer.singleShot(2500, win.show)
    
    sys.exit(app.exec())