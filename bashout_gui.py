import sys
import os
import random
import subprocess
import json
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                            QTextEdit, QFrame, QComboBox, QSpinBox, QFileDialog,
                            QMessageBox, QMenu, QAction, QInputDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPalette, QColor, QKeyEvent, QPainter, QTextOption

# Constants
CONFIG_FILE = Path.home() / '.bashout_config.json'
DEFAULT_SAVE_DIR = Path.home() / 'Documents' / 'BashOut'
BASHOUTRC = Path.home() / '.bashoutrc'

# Helper to read ~/.bashoutrc key:value pairs
bashoutrc_defaults = {}
if BASHOUTRC.exists():
    with open(BASHOUTRC, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or ':' not in line:
                continue
            key, value = line.split(':', 1)
            bashoutrc_defaults[key.strip().upper()] = value.strip()

def check_and_install_dependencies():
    """Check for required packages and install if missing."""
    required_packages = {
        'PyQt5': 'PyQt5',
        'PyQt5.QtWidgets': 'PyQt5',
        'PyQt5.QtCore': 'PyQt5',
        'PyQt5.QtGui': 'PyQt5'
    }
    
    missing_packages = []
    
    for package, pip_name in required_packages.items():
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(pip_name)
    
    if missing_packages:
        print("Installing required packages...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--user"] + missing_packages)
            print("Dependencies installed successfully!")
        except subprocess.CalledProcessError as e:
            print("\nError: Failed to install required packages.")
            print("Please try running these commands manually:")
            print(f"pip install --user {' '.join(missing_packages)}")
            sys.exit(1)

check_and_install_dependencies()

# Theme colors
THEMES = {
    'light': {
        'window': '#ffffff',
        'text': '#000000',
        'banner': '#1a73e8',
        'input_bg': '#ffffff',
        'input_text': '#000000',
        'button_bg': '#f0f0f0',
        'button_text': '#000000'
    },
    'dark': {
        'window': '#2d2d2d',
        'text': '#ffffff',
        'banner': '#8ab4f8',
        'input_bg': '#3d3d3d',
        'input_text': '#ffffff',
        'button_bg': '#3d3d3d',
        'button_text': '#ffffff'
    }
}

class CenteredPlaceholderTextEdit(QTextEdit):
    def __init__(self, placeholder_text="", parent=None):
        super().__init__(parent)
        self.placeholder_text = placeholder_text
        self.setPlaceholderText("")

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.toPlainText() == "" and not self.hasFocus():
            painter = QPainter(self.viewport())
            painter.setPen(QColor("#808080"))  # Gray color for placeholder
            option = QTextOption()
            option.setAlignment(Qt.AlignCenter)
            rect = self.viewport().rect()
            painter.drawText(rect, Qt.AlignCenter, self.placeholder_text)

class BashOutWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Use bashoutrc values as defaults
        self.current_theme = bashoutrc_defaults.get('GUI_THEME', 'light')
        self.font_size_default = int(bashoutrc_defaults.get('GUI_FONT_SIZE', 12))
        self.save_dir = Path(bashoutrc_defaults.get('SAVE_FILE', str(DEFAULT_SAVE_DIR))).expanduser().parent
        self.current_manuscript = None
        self.load_config()
        self.init_ui()
        self.load_initial_state()
        self.apply_theme()

    def load_config(self):
        """Load or create configuration."""
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                self.save_dir = Path(config.get('save_dir', str(self.save_dir)))
                self.current_manuscript = config.get('current_manuscript')
        else:
            self.save_dir.mkdir(parents=True, exist_ok=True)
            self.show_first_run_dialog()

    def show_first_run_dialog(self):
        """Show first-run setup dialog."""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText("Welcome to BashOut!")
        msg.setInformativeText("Would you like to choose where to save your manuscripts?")
        msg.setWindowTitle("First Run Setup")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        
        if msg.exec_() == QMessageBox.Yes:
            self.choose_save_location()
        
        self.create_new_manuscript()

    def choose_save_location(self):
        """Let user choose where to save manuscripts."""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Choose Save Location",
            str(self.save_dir),
            QFileDialog.ShowDirsOnly
        )
        if dir_path:
            self.save_dir = Path(dir_path)
            self.save_dir.mkdir(parents=True, exist_ok=True)
            self.save_config()

    def create_new_manuscript(self):
        """Create a new manuscript."""
        name, ok = QInputDialog.getText(
            self,
            "New Manuscript",
            "Enter a name for your manuscript:",
            QLineEdit.Normal,
            "untitled"
        )
        if ok and name:
            self.current_manuscript = name
            self.save_config()
            self.load_initial_state()

    def save_config(self):
        """Save current configuration."""
        config = {
            'save_dir': str(self.save_dir),
            'current_manuscript': self.current_manuscript
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f)

    def init_ui(self):
        self.setWindowTitle('BashOut')
        self.setMinimumSize(600, 400)

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title (manuscript name) as clickable button
        self.title_button = QPushButton()
        self.title_button.setFont(QFont('Helvetica', 28))
        self.title_button.setFlat(True)  # Make it look like a label
        self.title_button.setCursor(Qt.PointingHandCursor)  # Show hand cursor on hover
        self.title_button.clicked.connect(self.show_manuscript_menu)
        layout.addWidget(self.title_button)

        # Banner (quote) - now as plain text
        self.banner = QLabel()
        self.banner.setFont(QFont('Helvetica', 15))
        self.banner.setWordWrap(True)
        self.banner.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.banner)

        # Controls row (Last sentence, word count, banner picker)
        controls_layout = QHBoxLayout()
        
        # Last sentence label
        last_sent_label = QLabel('Last Sentence:')
        last_sent_label.setFont(QFont('Helvetica', 13, QFont.Bold))
        controls_layout.addWidget(last_sent_label)
        
        # Word count with label
        word_count_layout = QHBoxLayout()
        word_count_label = QLabel('Words:')
        word_count_label.setFont(QFont('Helvetica', 13))
        self.word_count = QLabel('[0/0]')
        self.word_count.setFont(QFont('Helvetica', 13))
        word_count_layout.addWidget(word_count_label)
        word_count_layout.addWidget(self.word_count)
        word_count_layout.setAlignment(Qt.AlignCenter)
        controls_layout.addLayout(word_count_layout)
        
        # Banner style dropdown with label
        banner_style_layout = QHBoxLayout()
        banner_style_layout.setSpacing(2)
        banner_style_label = QLabel('Banner Style:')
        banner_style_label.setFont(QFont('Helvetica', 13))
        self.banner_style = QComboBox()
        self.banner_style.setFont(QFont('Helvetica', 13))
        self.banner_style.addItems(['Quote', 'Note', 'Prompt'])
        self.banner_style.setCurrentText('Quote')
        self.banner_style.currentTextChanged.connect(self.on_banner_style_changed)
        banner_style_layout.addWidget(banner_style_label)
        banner_style_layout.addWidget(self.banner_style)
        controls_layout.addLayout(banner_style_layout)
        
        # Set stretch factors to position elements
        controls_layout.setStretch(0, 1)
        controls_layout.setStretch(1, 1)
        controls_layout.setStretch(2, 1)
        
        layout.addLayout(controls_layout)

        # Last sentence display
        self.last_sentence = QLabel()
        self.last_sentence.setFont(QFont('Helvetica', 14))
        self.last_sentence.setWordWrap(True)
        layout.addWidget(self.last_sentence)

        # Input field
        self.input_field = CenteredPlaceholderTextEdit(
            "Type your text here. Press Enter to add to saved file.\nCmd+N: New manuscript | Cmd+R: Rename manuscript"
        )
        self.input_field.setFont(QFont('Helvetica', self.font_size_default))
        self.input_field.textChanged.connect(self.on_text_changed)
        self.input_field.installEventFilter(self)
        layout.addWidget(self.input_field)

        # Controls below input (font size and theme)
        bottom_controls = QHBoxLayout()
        
        # Font size label and spinner
        font_size_label = QLabel('Font Size:')
        font_size_label.setFont(QFont('Helvetica', 12))
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 24)
        self.font_size.setValue(self.font_size_default)
        self.font_size.setFont(QFont('Helvetica', 12))
        self.font_size.valueChanged.connect(self.update_input_font)
        
        # Theme toggle button
        self.theme_button = QPushButton('Dark Mode' if self.current_theme == 'light' else 'Light Mode')
        self.theme_button.setFont(QFont('Helvetica', 12))
        self.theme_button.clicked.connect(self.toggle_theme)
        
        bottom_controls.addWidget(font_size_label)
        bottom_controls.addWidget(self.font_size)
        bottom_controls.addStretch()
        bottom_controls.addWidget(self.theme_button)
        
        layout.addLayout(bottom_controls)

    def apply_theme(self):
        theme = THEMES[self.current_theme]
        
        # Set window background and dialog styles
        self.setStyleSheet(f"""
            QMainWindow, QDialog {{
                background-color: {theme['window']};
                color: {theme['text']};
            }}
            QLabel {{
                color: {theme['text']};
            }}
            QTextEdit {{
                background-color: {theme['input_bg']};
                color: {theme['input_text']};
                border: 1px solid {theme['text']};
            }}
            QPushButton {{
                background-color: {theme['button_bg']};
                color: {theme['button_text']};
                border: 1px solid {theme['text']};
                padding: 5px 10px;
                border-radius: 3px;
            }}
            QPushButton:hover {{
                background-color: {theme['text']};
                color: {theme['window']};
            }}
            QComboBox {{
                background-color: {theme['button_bg']};
                color: {theme['button_text']};
                border: 1px solid {theme['text']};
                padding: 2px 5px;
                border-radius: 3px;
            }}
            QSpinBox {{
                background-color: {theme['button_bg']};
                color: {theme['button_text']};
                border: 1px solid {theme['text']};
                padding: 2px 5px;
                border-radius: 3px;
            }}
            QLineEdit {{
                background-color: {theme['input_bg']};
                color: {theme['input_text']};
                border: 1px solid {theme['text']};
                padding: 2px 5px;
                border-radius: 3px;
            }}
            QMessageBox {{
                background-color: {theme['window']};
                color: {theme['text']};
            }}
            QMessageBox QLabel {{
                color: {theme['text']};
            }}
            QInputDialog {{
                background-color: {theme['window']};
                color: {theme['text']};
            }}
            QInputDialog QLabel {{
                color: {theme['text']};
            }}
            QInputDialog QLineEdit {{
                background-color: {theme['input_bg']};
                color: {theme['input_text']};
                border: 1px solid {theme['text']};
                padding: 2px 5px;
                border-radius: 3px;
            }}
        """)
        
        # Set banner color (keeping it visible in both themes)
        self.banner.setStyleSheet(f"color: {theme['banner']};")

    def toggle_theme(self):
        self.current_theme = 'dark' if self.current_theme == 'light' else 'light'
        self.theme_button.setText('Dark Mode' if self.current_theme == 'light' else 'Light Mode')
        self.apply_theme()

    def eventFilter(self, obj, event):
        if obj == self.input_field and event.type() == QKeyEvent.KeyPress:
            # Use MetaModifier (Cmd) on Mac, ControlModifier (Ctrl) on other platforms
            modifier = Qt.MetaModifier if sys.platform == 'darwin' else Qt.ControlModifier
            if event.modifiers() == modifier:
                if event.key() == Qt.Key_N:
                    self.create_new_manuscript()
                    return True
                elif event.key() == Qt.Key_R:
                    self.rename_current_manuscript()
                    return True
            elif event.key() == Qt.Key_Return and not event.modifiers():
                self.add_sentence()
                return True
        return super().eventFilter(obj, event)

    def on_text_changed(self):
        # Optional: Add any text change handling here
        pass

    def load_initial_state(self):
        """Load the initial state of the application."""
        if self.current_manuscript:
            self.title_button.setText(self.current_manuscript)
            self.SAVE_FILE = self.save_dir / f"{self.current_manuscript}.txt"
            self.SAVE_FILE.parent.mkdir(parents=True, exist_ok=True)
            self.SAVE_FILE.touch(exist_ok=True)
            
            # Initialize word counts
            self.starting_word_count = self.count_words(self.SAVE_FILE)
            self.session_word_count = 0
            self.total_word_count = self.starting_word_count
            
            # Load last sentence
            if self.SAVE_FILE.exists() and self.SAVE_FILE.stat().st_size > 0:
                with open(self.SAVE_FILE, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if lines:
                        self.last_sentence.setText(lines[-1].strip())
            
            # Update word count display
            self.update_word_count()

    def save_text(self, text):
        """Save text to the current manuscript."""
        if not self.current_manuscript:
            self.create_new_manuscript()
            if not self.current_manuscript:  # User cancelled
                return
        
        with open(self.SAVE_FILE, 'a', encoding='utf-8') as f:
            f.write(text + '\n')
        self.last_sentence.setText(text)
        self.update_word_count()

    def update_word_count(self):
        self.total_word_count = self.count_words(self.SAVE_FILE)
        self.session_word_count = self.total_word_count - self.starting_word_count
        self.word_count.setText(f"[{self.session_word_count}/{self.total_word_count}]")

    def add_sentence(self):
        new_sentence = self.input_field.toPlainText().strip()
        if new_sentence:
            self.save_text(new_sentence)
            self.input_field.clear()

    def on_banner_style_changed(self, style):
        if style == 'Quote':
            self.banner.setText(self.get_random_quote())
        elif style == 'Note':
            self.banner.setText(self.get_note())
        elif style == 'Prompt':
            self.banner.setText(self.get_style_prompt())

    def update_input_font(self, size):
        current_font = self.input_field.font()
        current_font.setPointSize(size)
        self.input_field.setFont(current_font)

    def count_words(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
                return len(text.split())
        except Exception:
            return 0

    def get_random_quote(self):
        quotes_file = RESOURCE_DIR / "quotes.txt"
        if quotes_file.exists():
            with open(quotes_file, 'r', encoding='utf-8') as f:
                quotes = [q.strip() for q in f if q.strip()]
                if quotes:
                    return random.choice(quotes)
        return "No quotes available."

    def get_note(self):
        note_file = RESOURCE_DIR / "note.txt"
        if note_file.exists():
            with open(note_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        return "No note available."

    def get_style_prompt(self):
        voicelist = ["formal", "informal", "conversational", "professional", "academic", 
                    "playful", "sarcastic", "intimate", "detached"]
        tonelist = ["light-hearted", "serious", "dark", "humorous", "whimsical", 
                    "melancholic", "uplifting", "suspenseful", "nostalgic"]
        tenselist = ["past", "present", "future"]
        povlist = ["first-person", "second-person", "third-person (limited)", 
                    "third-person (omniscient)"]
        pacelist = ["fast", "slow", "steadily", "frenetically"]
        style = (f"Create a {random.choice(tonelist)}, {random.choice(pacelist)}-paced story "
                f"with a {random.choice(voicelist)} voice in {random.choice(tenselist)}-tense "
                f"from a {random.choice(povlist)} point of view.")
        style_file = RESOURCE_DIR / "style.txt"
        with open(style_file, 'w', encoding='utf-8') as f:
            f.write(style)
        return style

    def show_manuscript_menu(self):
        """Show manuscript management menu when title is clicked."""
        menu = QMenu(self)
        
        new_action = menu.addAction("New Manuscript (Cmd+N)")
        new_action.triggered.connect(self.create_new_manuscript)
        
        rename_action = menu.addAction("Rename Manuscript (Cmd+R)")
        rename_action.triggered.connect(self.rename_current_manuscript)
        
        menu.addSeparator()
        
        change_location_action = menu.addAction("Change Save Location...")
        change_location_action.triggered.connect(self.choose_save_location)
        
        # Show menu below the title button
        menu.exec_(self.title_button.mapToGlobal(self.title_button.rect().bottomLeft()))

    def rename_current_manuscript(self):
        """Rename the current manuscript."""
        if not self.current_manuscript:
            return
            
        old_name = self.current_manuscript
        new_name, ok = QInputDialog.getText(
            self,
            "Rename Manuscript",
            "Enter new name:",
            QLineEdit.Normal,
            old_name
        )
        
        if ok and new_name and new_name != old_name:
            old_file = self.save_dir / f"{old_name}.txt"
            new_file = self.save_dir / f"{new_name}.txt"
            
            if new_file.exists():
                QMessageBox.warning(
                    self,
                    "Error",
                    f"A manuscript named '{new_name}' already exists."
                )
                return
                
            try:
                old_file.rename(new_file)
                self.current_manuscript = new_name
                self.SAVE_FILE = new_file
                self.save_config()
                self.title_button.setText(new_name)
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Failed to rename manuscript: {str(e)}"
                )

if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)
        
        # Set application style
        app.setStyle('Fusion')
        
        # Create and show the main window
        window = BashOutWindow()
        window.show()
        
        sys.exit(app.exec_())
    except Exception as e:
        print("\nError: An unexpected error occurred.")
        print("Please make sure you have Python 3.6 or later installed.")
        print(f"Error details: {str(e)}")
        sys.exit(1) 