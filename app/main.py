import sys
import os
from fnmatch import fnmatch
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QScrollArea, QDialog, QFileDialog
from PyQt5.QtGui import QClipboard

class CopyableTextWidget(QWidget):
    def __init__(self, text: str, title: str, path: str, parent=None):
        super().__init__(parent)
        
        self.text = text
        self.title = title
        self.path = path

        # Text label
        self.text_label = QLabel(text)
        self.text_label.setWordWrap(True)

        self.button_layout = QHBoxLayout()
        # "Copy" button
        self.copy_button = QPushButton("Copy")
        self.copy_button.clicked.connect(self.copy_text)
        # Title label
        self.label = QLabel(text=path)
        # "Delete" button
        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_text)
        
        self.button_layout.addWidget(self.copy_button)
        self.button_layout.addWidget(self.label)
        self.button_layout.addWidget(self.delete_button)

        # Horizontal layout for button and label
        hbox = QVBoxLayout()
        hbox.addLayout(self.button_layout)
        hbox.addWidget(self.text_label)

        self.setLayout(hbox)

    def copy_text(self):
        """Copies text to clipboard."""
        clipboard = QApplication.clipboard()
        clipboard.setText('``` ' + self.path + '\n' + self.text_label.text() + '\n```')
        
    def delete_text(self):
        """Removes the widget"""
        # Remove from parent layout
        self.parent().layout().removeWidget(self)
        # Delete the object
        self.deleteLater()

class App(QWidget):
    def __init__(self, directory):
        super().__init__()
        
        self.setMinimumSize(1000, 800)
        
        scroll_layout = QVBoxLayout()
        
        self.text_widgets = []
        self.project_structure = []

        self.ignore_patterns = self.load_ignore_patterns('ignore_list.txt') + self.load_gitignore(directory)

        for dirpath, dirnames, filenames in os.walk(directory):
            dirnames[:] = [d for d in dirnames if not self.is_ignored(os.path.join(dirpath, d))]
            filenames = [f for f in filenames if not self.is_ignored(os.path.join(dirpath, f))]

            depth = dirpath.replace(directory, '').count(os.sep)
            indent = ' ' * 4 * depth
            self.project_structure.append(f'{indent}{os.path.basename(dirpath)}/')
            sub_indent = ' ' * 4 * (depth + 1)
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                self.project_structure.append(f'{sub_indent}{filename}')
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    text_widget = CopyableTextWidget(text=content, title=filename, path=file_path)
                    scroll_layout.addWidget(text_widget)
                    self.text_widgets.append(text_widget)
                except (UnicodeDecodeError, PermissionError):
                    print('continue')
                    continue
                
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        scroll_area.setWidget(QWidget())
        scroll_area.widget().setLayout(scroll_layout)
        
        self.copy_button = QPushButton("Copy All")
        self.copy_button.clicked.connect(self.copy)
        
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.copy_button)
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)

    def load_gitignore(self, directory):
        ignore_patterns = []
        gitignore_path = os.path.join(directory, '.gitignore')
        if os.path.exists(gitignore_path):
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        ignore_patterns.append(line)
        return ignore_patterns

    def load_ignore_patterns(self, filepath):
        ignore_patterns = []
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        ignore_patterns.append(line)
        return ignore_patterns

    def is_ignored(self, path):
        for pattern in self.ignore_patterns:
            if fnmatch(path, pattern) or fnmatch(os.path.basename(path), pattern):
                return True
        return False
        
    def copy(self):
        text = "Project structure:\n"
        text += '\n'.join(self.project_structure) + '\n\n\n'
        
        for i, widget in enumerate(self.text_widgets):
            # Add project structure, if this is not the first file
            if i > 0:
                text += "\n"
            
            # Determine the relative path to the file
            relative_path = os.path.relpath(widget.path, os.path.dirname(widget.path))
            
            # Add file path and content
            text += f"``` {relative_path} \n {widget.text} \n```\n\n"

        clipboard = QApplication.clipboard()
        clipboard.setText(text)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    dialog = QDialog()
    directory = QFileDialog.getExistingDirectory(dialog, "Select Directory")
    
    if directory:
        main_window = App(directory)
        main_window.show()
        sys.exit(app.exec_())
