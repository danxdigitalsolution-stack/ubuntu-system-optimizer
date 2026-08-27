import sys
import os
import shutil
import subprocess
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QListWidget, QStackedWidget, QPlainTextEdit,
    QLineEdit, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal, QSize
from PySide6.QtGui import QFont, QIcon, QTextCursor

class CommandRunner(QThread):
    """
    Worker thread to run shell commands without freezing the GUI.
    Uses pkexec to prompt for root password natively in Ubuntu.
    """
    output_signal = Signal(str)
    finished_signal = Signal(int)

    def __init__(self, command, requires_root=True):
        super().__init__()
        self.command = command
        self.requires_root = requires_root

    def run(self):
        cmd = self.command
        if self.requires_root:
            cmd = ["pkexec"] + cmd

        try:
            # Emit command being run for logging
            self.output_signal.emit(f"--- Running: {' '.join(cmd)} ---")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            # Read output line by line and emit to GUI
            for line in process.stdout:
                self.output_signal.emit(line.strip())

            process.wait()
            self.finished_signal.emit(process.returncode)

        except Exception as e:
            self.output_signal.emit(f"Error executing command: {str(e)}")
            self.finished_signal.emit(-1)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ubuntu System Optimizer - Enterprise")
        self.setMinimumSize(900, 600)
        
        # Main layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Initialize components
        self.create_sidebar(main_layout)
        self.create_main_content(main_layout)
        self.apply_stylesheet()

        # State tracking
        self.is_running = False

    def create_sidebar(self, parent_layout):
        sidebar_frame = QFrame()
        sidebar_frame.setObjectName("SidebarFrame")
        sidebar_frame.setFixedWidth(220)
        sidebar_layout = QVBoxLayout(sidebar_frame)
        sidebar_layout.setContentsMargins(0, 20, 0, 0)
        sidebar_layout.setSpacing(5)

        # App Title
        title_label = QLabel(" System\n Optimizer")
        title_label.setObjectName("AppTitle")
        title_label.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(title_label)
        sidebar_layout.addSpacing(20)

        # Navigation List
        self.nav_list = QListWidget()
        self.nav_list.setObjectName("NavList")
        nav_items = ["Dashboard & Cleanup", "Maintenance & Fixes", "App Uninstaller"]
        self.nav_list.addItems(nav_items)
        self.nav_list.setCurrentRow(0)
        self.nav_list.currentRowChanged.connect(self.change_page)
        
        sidebar_layout.addWidget(self.nav_list)
        parent_layout.addWidget(sidebar_frame)

    def create_main_content(self, parent_layout):
        content_frame = QFrame()
        content_frame.setObjectName("ContentFrame")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(20, 20, 20, 20)

        # Stacked Widget for pages
        self.stacked_widget = QStackedWidget()
        
        # Page 1: Cleanup
        self.stacked_widget.addWidget(self.create_cleanup_page())
        
        # Page 2: Maintenance
        self.stacked_widget.addWidget(self.create_maintenance_page())
        
        # Page 3: Uninstaller
        self.stacked_widget.addWidget(self.create_uninstaller_page())

        content_layout.addWidget(self.stacked_widget)

        # Console Log Area (Always visible at bottom)
        console_label = QLabel("Process Log")
        console_label.setObjectName("HeaderLabel")
        content_layout.addWidget(console_label)

        self.console = QPlainTextEdit()
        self.console.setObjectName("ConsoleLog")
        self.console.setReadOnly(True)
        self.console.setMaximumHeight(200)
        content_layout.addWidget(self.console)

        parent_layout.addWidget(content_frame)

    def change_page(self, index):
        self.stacked_widget.setCurrentIndex(index)

    # --- Pages Creation ---
    
    def create_cleanup_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignTop)

        lbl = QLabel("System Cleanup Tools")
        lbl.setObjectName("PageTitle")
        layout.addWidget(lbl)
        
        desc = QLabel("Safely remove unnecessary cache files and orphaned packages to free up space.")
        desc.setObjectName("DescriptionLabel")
        layout.addWidget(desc)
        layout.addSpacing(15)

        btn_clean = QPushButton("Clear Downloaded Package Cache (apt clean)")
        btn_clean.setToolTip("Removes all cached package files from /var/cache/apt/archives/")
        btn_clean.clicked.connect(lambda: self.run_system_command(["apt-get", "clean", "-y"]))
        
        btn_autoclean = QPushButton("Clear Obsolete Package Cache (apt autoclean)")
        btn_autoclean.setToolTip("Removes only package files that can no longer be downloaded")
        btn_autoclean.clicked.connect(lambda: self.run_system_command(["apt-get", "autoclean", "-y"]))
        
        btn_autoremove = QPushButton("Remove Unused Dependencies (apt autoremove)")
        btn_autoremove.setToolTip("Removes packages that were automatically installed to satisfy dependencies and are no longer needed")
        btn_autoremove.clicked.connect(lambda: self.run_system_command(["apt-get", "autoremove", "-y"]))

        layout.addWidget(btn_clean)
        layout.addWidget(btn_autoclean)
        layout.addWidget(btn_autoremove)
        return page

    def create_maintenance_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignTop)

        lbl = QLabel("System Maintenance & Fixes")
        lbl.setObjectName("PageTitle")
        layout.addWidget(lbl)
        
        desc = QLabel("Update your system, fix broken packages, and repair user interface components.")
        desc.setObjectName("DescriptionLabel")
        layout.addWidget(desc)
        layout.addSpacing(15)

        btn_update = QPushButton("Refresh Package Lists (apt update)")
        btn_update.clicked.connect(lambda: self.run_system_command(["apt-get", "update"]))
        
        btn_upgrade = QPushButton("Upgrade System Packages (apt upgrade)")
        btn_upgrade.clicked.connect(lambda: self.run_system_command(["apt-get", "upgrade", "-y"]))
        
        btn_fix_broken = QPushButton("Fix Broken Dependencies (apt --fix-broken install)")
        btn_fix_broken.clicked.connect(lambda: self.run_system_command(["apt-get", "--fix-broken", "install", "-y"]))
        
        btn_dpkg = QPushButton("Reconfigure Interrupted Installs (dpkg --configure -a)")
        btn_dpkg.clicked.connect(lambda: self.run_system_command(["dpkg", "--configure", "-a"]))
        
        btn_thumb = QPushButton("Fix Broken Thumbnails (Clear ~/.cache/thumbnails)")
        btn_thumb.clicked.connect(self.fix_thumbnails)
        btn_thumb.setObjectName("WarningButton")

        layout.addWidget(btn_update)
        layout.addWidget(btn_upgrade)
        layout.addSpacing(10)
        layout.addWidget(btn_fix_broken)
        layout.addWidget(btn_dpkg)
        layout.addSpacing(10)
        layout.addWidget(btn_thumb)
        return page

    def create_uninstaller_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignTop)

        lbl = QLabel("Application Uninstaller")
        lbl.setObjectName("PageTitle")
        layout.addWidget(lbl)

        desc = QLabel("Completely remove applications and their configuration files.")
        desc.setObjectName("DescriptionLabel")
        layout.addWidget(desc)
        layout.addSpacing(15)

        self.pkg_input = QLineEdit()
        self.pkg_input.setPlaceholderText("Enter exact package name (e.g., firefox, vlc)...")
        layout.addWidget(self.pkg_input)

        btn_uninstall = QPushButton("Uninstall and Purge Configuration")
        btn_uninstall.setObjectName("DangerButton")
        btn_uninstall.clicked.connect(self.uninstall_app)
        layout.addWidget(btn_uninstall)
        
        return page

    # --- Core Logic Functions ---

    def fix_thumbnails(self):
        if self.is_running: return
        self.console.appendPlainText("--- Fixing broken thumbnails ---")
        thumb_dir = os.path.expanduser("~/.cache/thumbnails")
        
        try:
            if os.path.exists(thumb_dir):
                shutil.rmtree(thumb_dir)
                os.makedirs(thumb_dir)
                self.console.appendPlainText("Success: Thumbnail cache cleared. They will be regenerated on demand.")
            else:
                self.console.appendPlainText("Info: Thumbnail cache directory does not exist. Nothing to clear.")
        except Exception as e:
            self.console.appendPlainText(f"Error clearing thumbnails: {str(e)}")

    def uninstall_app(self):
        pkg_name = self.pkg_input.text().strip()
        if not pkg_name:
            QMessageBox.warning(self, "Input Error", "Please enter a package name to uninstall.")
            return
        
        reply = QMessageBox.question(
            self, "Confirm Uninstall", 
            f"Are you sure you want to COMPLETELY REMOVE '{pkg_name}' and its configuration files?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.run_system_command(["apt-get", "remove", "--purge", "-y", pkg_name])

    def run_system_command(self, cmd_list, requires_root=True):
        if self.is_running:
            QMessageBox.information(self, "Busy", "A process is already running. Please wait.")
            return
            
        self.is_running = True
        self.set_ui_enabled(False)
        self.console.clear()
        
        self.worker = CommandRunner(cmd_list, requires_root=requires_root)
        self.worker.output_signal.connect(self.log_output)
        self.worker.finished_signal.connect(self.command_finished)
        self.worker.start()

    def log_output(self, text):
        self.console.appendPlainText(text)
        # Auto-scroll to bottom
        scrollbar = self.console.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def command_finished(self, returncode):
        self.is_running = False
        self.set_ui_enabled(True)
        if returncode == 0:
            self.log_output("\n--- Process completed successfully. ---")
        else:
            self.log_output(f"\n--- Process exited with code {returncode}. (If 126/127, authentication might have been canceled) ---")

    def set_ui_enabled(self, enabled):
        self.nav_list.setEnabled(enabled)
        self.stacked_widget.setEnabled(enabled)

    # --- Stylesheet ---
    def apply_stylesheet(self):
        # Black Charcoal Enterprise Style
        style = """
        QMainWindow {
            background-color: #1a1a1a;
        }
        QWidget {
            color: #d4d4d4;
            font-family: 'Segoe UI', 'Ubuntu', sans-serif;
            font-size: 10pt;
        }
        
        /* Sidebar Styling */
        QFrame#SidebarFrame {
            background-color: #212124;
            border-right: 1px solid #333336;
        }
        QLabel#AppTitle {
            font-size: 16pt;
            font-weight: bold;
            color: #ffffff;
            margin: 10px;
        }
        QListWidget#NavList {
            background-color: transparent;
            border: none;
            outline: none;
        }
        QListWidget#NavList::item {
            padding: 12px 20px;
            border-left: 4px solid transparent;
            color: #a0a0a0;
        }
        QListWidget#NavList::item:hover {
            background-color: #2d2d30;
            color: #ffffff;
        }
        QListWidget#NavList::item:selected {
            background-color: #2d2d30;
            border-left: 4px solid #007acc;
            color: #ffffff;
            font-weight: bold;
        }
        
        /* Content Styling */
        QFrame#ContentFrame {
            background-color: #1e1e1e;
        }
        QLabel#PageTitle {
            font-size: 18pt;
            font-weight: 600;
            color: #ffffff;
        }
        QLabel#DescriptionLabel {
            color: #909090;
            font-style: italic;
        }
        QLabel#HeaderLabel {
            font-size: 11pt;
            font-weight: bold;
            color: #e0e0e0;
            margin-top: 15px;
            margin-bottom: 5px;
        }
        
        /* Buttons */
        QPushButton {
            background-color: #333337;
            color: #e0e0e0;
            border: 1px solid #45454a;
            padding: 10px 15px;
            border-radius: 4px;
            text-align: left;
            font-weight: 500;
        }
        QPushButton:hover {
            background-color: #3f3f46;
            border: 1px solid #007acc;
        }
        QPushButton:pressed {
            background-color: #007acc;
            color: #ffffff;
        }
        QPushButton:disabled {
            background-color: #252526;
            color: #606060;
            border: 1px solid #333333;
        }
        
        /* Specific Button Colors */
        QPushButton#WarningButton:hover {
            border: 1px solid #d7ba7d;
        }
        QPushButton#DangerButton {
            background-color: #4a2323;
            border: 1px solid #803030;
            text-align: center;
        }
        QPushButton#DangerButton:hover {
            background-color: #6b2a2a;
            border: 1px solid #f44336;
        }
        
        /* Inputs & Logs */
        QLineEdit {
            background-color: #252526;
            border: 1px solid #3e3e42;
            padding: 10px;
            border-radius: 4px;
            color: #ffffff;
        }
        QLineEdit:focus {
            border: 1px solid #007acc;
        }
        QPlainTextEdit#ConsoleLog {
            background-color: #0d0d0d;
            border: 1px solid #333336;
            border-radius: 4px;
            padding: 10px;
            font-family: 'Consolas', 'Ubuntu Mono', monospace;
            font-size: 9pt;
            color: #4ec9b0;
        }
        
        /* Scrollbars */
        QScrollBar:vertical {
            border: none;
            background: #1e1e1e;
            width: 10px;
            margin: 0px 0px 0px 0px;
        }
        QScrollBar::handle:vertical {
            background: #424242;
            min-height: 20px;
            border-radius: 5px;
        }
        QScrollBar::handle:vertical:hover {
            background: #4f4f4f;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        """
        self.setStyleSheet(style)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Optional: set a default font
    font = QFont("Ubuntu", 10)
    app.setFont(font)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())