from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox, QDialog, QDialogButtonBox, QGridLayout, QLabel, QVBoxLayout
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
        layout.addWidget(info)
        grid=QGridLayout()
        self.boxes={}
        for index,(extension,label) in enumerate(COMMON_TYPES):
            box=QCheckBox(f"{extension} · {label}")
            box.setChecked(extension in selected)
            self.boxes[extension]=box
            grid.addWidget(box,index//2,index%2)
        layout.addLayout(grid)
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Übernehmen")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Abbrechen")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def selected_extensions(self)->set[str]:
        return {extension for extension,box in self.boxes.items() if box.isChecked()}
