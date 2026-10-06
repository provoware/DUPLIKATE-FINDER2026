from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)

COMMON_TYPES = (
    (".txt", "Text"),
    (".md", "Markdown-Text"),
    (".csv", "Tabellendaten"),
    (".log", "Protokolldatei"),
    (".json", "JSON-Daten"),
    (".xml", "XML-Daten"),
    (".yaml", "YAML-Daten"),
    (".yml", "YAML-Daten"),
    (".ini", "Einstellungsdatei"),
    (".conf", "Konfigurationsdatei"),
    (".py", "Python-Code"),
    (".sh", "Shell-Skript"),
    (".pdf", "PDF"),
    (".zip", "ZIP-Archiv"),
    (".7z", "7-Zip-Archiv"),
    (".tar", "TAR-Archiv"),
    (".gz", "GZip-Archiv"),
    (".iso", "Datenträger-Abbild"),
    (".jpg", "JPEG-Bild"),
    (".jpeg", "JPEG-Bild"),
    (".png", "PNG-Bild"),
    (".gif", "GIF-Bild"),
    (".mp3", "MP3-Audio"),
    (".wav", "WAV-Audio"),
    (".flac", "FLAC-Audio"),
    (".mp4", "MP4-Video"),
    (".mkv", "MKV-Video"),
    (".avi", "AVI-Video"),
)


class ScanOptionsDialog(QDialog):
    def __init__(
        self,
        parent,
        *,
        skip_python_project_dirs: bool,
        skip_hidden_dirs: bool,
        excluded_extensions: set[str],
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Prüfoptionen")
        self.resize(520, 560)
        layout = QVBoxLayout(self)

        info = QLabel(
            "Diese Optionen gelten für Textsuche und Duplikatprüfung. "
            "Originaldateien werden dadurch nicht verändert."
        )
        info.setWordWrap(True)
        info.setProperty("card", True)
        layout.addWidget(info)

        self.python_dirs = QCheckBox(
            "Entwicklungs-/Python-Arbeitsordner auslassen (.venv, __pycache__, build …)"
        )
        self.python_dirs.setChecked(skip_python_project_dirs)
        self.python_dirs.setToolTip(
            "Empfohlen. Überspringt typische technische Projektordner, die selten Nutzdaten enthalten."
        )
        layout.addWidget(self.python_dirs)

        self.hidden_dirs = QCheckBox("Versteckte Ordner auslassen (.cache, .config …)")
        self.hidden_dirs.setChecked(skip_hidden_dirs)
        self.hidden_dirs.setToolTip(
            "Optional. Kann die Prüfung deutlich verkürzen, blendet aber auch versteckte Nutzordner aus."
        )
        layout.addWidget(self.hidden_dirs)

        label = QLabel("Dateitypen ausklammern")
        label.setProperty("heading", True)
        layout.addWidget(label)

        self.types = QListWidget()
        self.types.setObjectName("excluded_types_list")
        for extension, description in COMMON_TYPES:
            item = QListWidgetItem(f"{extension}  ·  {description}")
            item.setData(Qt.ItemDataRole.UserRole, extension)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(
                Qt.CheckState.Checked
                if extension in excluded_extensions
                else Qt.CheckState.Unchecked
            )
            self.types.addItem(item)
        layout.addWidget(self.types, 1)

        presets = QHBoxLayout()
        none = QPushButton("Keine ausklammern")
        none.clicked.connect(lambda: self._set_all(False))
        media = QPushButton("Große Medien ausklammern")
        media.clicked.connect(self._exclude_large_media)
        presets.addWidget(none)
        presets.addWidget(media)
        layout.addLayout(presets)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Save
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Übernehmen")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Abbrechen")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _set_all(self, checked: bool) -> None:
        state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        for index in range(self.types.count()):
            self.types.item(index).setCheckState(state)

    def _exclude_large_media(self) -> None:
        targets = {".iso", ".zip", ".7z", ".tar", ".gz", ".mp3", ".wav", ".flac", ".mp4", ".mkv", ".avi"}
        for index in range(self.types.count()):
            item = self.types.item(index)
            ext = item.data(Qt.ItemDataRole.UserRole)
            item.setCheckState(
                Qt.CheckState.Checked if ext in targets else Qt.CheckState.Unchecked
            )

    def excluded_extensions(self) -> set[str]:
        result: set[str] = set()
        for index in range(self.types.count()):
            item = self.types.item(index)
            if item.checkState() == Qt.CheckState.Checked:
                result.add(str(item.data(Qt.ItemDataRole.UserRole)))
        return result
