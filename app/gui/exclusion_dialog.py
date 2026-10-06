from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox, QDialog, QDialogButtonBox, QGridLayout, QLabel, QPushButton, QHBoxLayout, QVBoxLayout
)

COMMON_TYPES = (
    (".py", "Python-Quelltext"),
    (".pyc", "Python-Zwischendatei"),
    (".log", "Protokolldatei"),
    (".json", "JSON-Daten"),
    (".csv", "Tabellendaten"),
    (".zip", "ZIP-Archiv"),
    (".tar", "TAR-Archiv"),
    (".gz", "GZIP-Archiv"),
    (".jpg", "JPEG-Bild"),
    (".png", "PNG-Bild"),
    (".mp3", "MP3-Audio"),
    (".mp4", "MP4-Video"),
)

PRESETS = {
    "archive": {".zip", ".tar", ".gz"},
    "media": {".jpg", ".png", ".mp3", ".mp4"},
    "python": {".py", ".pyc"},
}


class ExclusionDialog(QDialog):
    def __init__(self,selected:frozenset[str],parent=None)->None:
        super().__init__(parent)
        self.setWindowTitle("Dateitypen ausschließen")
        self.setMinimumWidth(430)
        layout=QVBoxLayout(self)
        info=QLabel(
            "Angekreuzte Dateitypen werden bei Suche und Duplikatprüfung vollständig ausgelassen. "
            "Originaldateien werden dabei nicht verändert."
        )
        info.setWordWrap(True)
        info.setProperty("infoBox", True)
        layout.addWidget(info)

        presets=QHBoxLayout()
        for text,key in (("Archive auslassen","archive"),("Medien auslassen","media"),("Python-Dateien auslassen","python")):
            button=QPushButton(text)
            button.setProperty("compact",True)
            button.clicked.connect(lambda _checked=False,k=key:self._apply_preset(PRESETS[k]))
            presets.addWidget(button)
        clear=QPushButton("Keine Dateitypen auslassen")
        clear.setProperty("compact",True)
        clear.clicked.connect(lambda:self._apply_preset(set(),replace=True))
        presets.addWidget(clear)
        layout.addLayout(presets)

        grid=QGridLayout()
        self.boxes={}
        for index,(extension,label) in enumerate(COMMON_TYPES):
            box=QCheckBox(f"{extension} · {label}")
            box.setChecked(extension in selected)
            box.setToolTip(f"{extension} vollständig von Suche und Duplikatprüfung ausschließen.")
            self.boxes[extension]=box
            grid.addWidget(box,index//2,index%2)
        layout.addLayout(grid)

        note=QLabel("Tipp: Für die Textsuche werden ohnehin nur unterstützte Textdateien gelesen. Die Ausschlüsse gelten zusätzlich auch für die Duplikatprüfung.")
        note.setWordWrap(True)
        note.setProperty("hint",True)
        layout.addWidget(note)

        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Übernehmen")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Abbrechen")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _apply_preset(self,extensions:set[str],replace:bool=False)->None:
        if replace:
            for box in self.boxes.values():
                box.setChecked(False)
            return
        for extension in extensions:
            box=self.boxes.get(extension)
            if box is not None:
                box.setChecked(True)

    def selected_extensions(self)->set[str]:
        return {extension for extension,box in self.boxes.items() if box.isChecked()}
