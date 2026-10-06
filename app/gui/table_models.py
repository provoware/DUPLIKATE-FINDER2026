from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from app.models.entities import CollectionItem, DuplicateGroup, SearchHit
from app.storage.database import Database


class SearchResultsModel(QAbstractTableModel):
    """Virtuelle Trefferliste: Qt erzeugt keine Widgets pro Ergebniszeile."""

    HEADERS=("Markiert","Quelle","Datei","Zeile","Fundstelle")

    def __init__(self,database:Database,parent=None)->None:
        super().__init__(parent)
        self.database=database
        self._hits:list[SearchHit]=[]
        self._marked:dict[Path,bool]={}

    def rowCount(self,parent=QModelIndex())->int:
        return 0 if parent.isValid() else len(self._hits)

    def columnCount(self,parent=QModelIndex())->int:
        return 0 if parent.isValid() else len(self.HEADERS)

    def headerData(self,section,orientation,role=Qt.ItemDataRole.DisplayRole):
        if role==Qt.ItemDataRole.DisplayRole and orientation==Qt.Orientation.Horizontal and 0<=section<len(self.HEADERS):
            return self.HEADERS[section]
        return None

    def data(self,index:QModelIndex,role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not (0<=index.row()<len(self._hits)):
            return None
        hit=self._hits[index.row()]
        path=hit.path
        if role==Qt.ItemDataRole.UserRole:
            return str(path)
        if role==Qt.ItemDataRole.ToolTipRole:
            return str(path) if index.column()!=4 else hit.excerpt
        if role==Qt.ItemDataRole.TextAlignmentRole and index.column() in (0,3):
            return int(Qt.AlignmentFlag.AlignCenter)
        if role!=Qt.ItemDataRole.DisplayRole:
            return None
        if index.column()==0:
            marked=self._marked.get(path)
            if marked is None:
                marked=self.database.virtual_item(path).marked
                self._marked[path]=marked
            return "★" if marked else ""
        if index.column()==1:
            return hit.source
        if index.column()==2:
            return str(path)
        if index.column()==3:
            return "" if hit.line_number is None else str(hit.line_number)
        if index.column()==4:
            return hit.excerpt
        return None

    def set_hits(self,hits:list[SearchHit])->None:
        self.beginResetModel()
        self._hits=list(hits)
        self._marked.clear()
        self.endResetModel()

    def hit_at(self,row:int)->SearchHit|None:
        return self._hits[row] if 0<=row<len(self._hits) else None

    def path_at(self,row:int)->Path|None:
        hit=self.hit_at(row)
        return hit.path if hit else None

    def set_marked(self,path:Path,marked:bool)->None:
        self._marked[path]=bool(marked)
        for row,hit in enumerate(self._hits):
            if hit.path==path:
                index=self.index(row,0)
                self.dataChanged.emit(index,index,[Qt.ItemDataRole.DisplayRole])

    def sort(self,column:int,order:Qt.SortOrder=Qt.SortOrder.AscendingOrder)->None:
        if not self._hits:
            return
        reverse=order==Qt.SortOrder.DescendingOrder
        def key(hit:SearchHit):
            if column==0:
                return (not self._marked.get(hit.path,self.database.virtual_item(hit.path).marked),str(hit.path).casefold())
            if column==1:
                return hit.source.casefold()
            if column==2:
                return str(hit.path).casefold()
            if column==3:
                return -1 if hit.line_number is None else hit.line_number
            return hit.excerpt.casefold()
        self.layoutAboutToBeChanged.emit()
        self._hits.sort(key=key,reverse=reverse)
        self.layoutChanged.emit()


class DuplicateMembersModel(QAbstractTableModel):
    HEADERS=("Datei","Ordner","Größe","Geändert")

    def __init__(self,parent=None)->None:
        super().__init__(parent)
        self._group:DuplicateGroup|None=None
        self._paths:list[Path]=[]
        self._stats:dict[Path,tuple[int,float]|None]={}

    def rowCount(self,parent=QModelIndex())->int:
        return 0 if parent.isValid() else len(self._paths)

    def columnCount(self,parent=QModelIndex())->int:
        return 0 if parent.isValid() else len(self.HEADERS)

    def headerData(self,section,orientation,role=Qt.ItemDataRole.DisplayRole):
        if role==Qt.ItemDataRole.DisplayRole and orientation==Qt.Orientation.Horizontal and 0<=section<len(self.HEADERS):
            return self.HEADERS[section]
        return None

    def _stat(self,path:Path)->tuple[int,float]|None:
        if path not in self._stats:
            try:
                st=path.stat()
                self._stats[path]=(st.st_size,st.st_mtime)
            except OSError:
                self._stats[path]=None
        return self._stats[path]

    @staticmethod
    def _human_size(size:int)->str:
        value=float(size)
        for unit in ("B","KB","MB","GB","TB"):
            if value<1024 or unit=="TB":
                return f"{value:.1f} {unit}" if unit!="B" else f"{int(value)} B"
            value/=1024
        return f"{size} B"

    def data(self,index:QModelIndex,role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not (0<=index.row()<len(self._paths)):
            return None
        path=self._paths[index.row()]
        if role==Qt.ItemDataRole.UserRole:
            return str(path)
        if role==Qt.ItemDataRole.ToolTipRole:
            return str(path)
        if role!=Qt.ItemDataRole.DisplayRole:
            return None
        if index.column()==0:
            return path.name
        if index.column()==1:
            return str(path.parent)
        if index.column()==2:
            size=self._group.size if self._group else ((self._stat(path) or (0,0))[0])
            return self._human_size(size)
        if index.column()==3:
            stat=self._stat(path)
            return datetime.fromtimestamp(stat[1]).strftime("%Y-%m-%d %H:%M") if stat else "nicht verfügbar"
        return None

    def set_group(self,group:DuplicateGroup|None)->None:
        self.beginResetModel()
        self._group=group
        self._paths=list(group.paths) if group else []
        self._stats.clear()
        self.endResetModel()

    def path_at(self,row:int)->Path|None:
        return self._paths[row] if 0<=row<len(self._paths) else None

    def sort(self,column:int,order:Qt.SortOrder=Qt.SortOrder.AscendingOrder)->None:
        reverse=order==Qt.SortOrder.DescendingOrder
        def key(path:Path):
            if column==0:
                return path.name.casefold()
            if column==1:
                return str(path.parent).casefold()
            stat=self._stat(path)
            if column==2:
                return self._group.size if self._group else ((stat or (0,0))[0])
            return (stat or (0,0))[1]
        self.layoutAboutToBeChanged.emit()
        self._paths.sort(key=key,reverse=reverse)
        self.layoutChanged.emit()


class CollectionItemsModel(QAbstractTableModel):
    HEADERS=("Datei","Ordner","Notiz")

    def __init__(self,parent=None)->None:
        super().__init__(parent)
        self._items:list[CollectionItem]=[]

    def rowCount(self,parent=QModelIndex())->int:
        return 0 if parent.isValid() else len(self._items)

    def columnCount(self,parent=QModelIndex())->int:
        return 0 if parent.isValid() else len(self.HEADERS)

    def headerData(self,section,orientation,role=Qt.ItemDataRole.DisplayRole):
        if role==Qt.ItemDataRole.DisplayRole and orientation==Qt.Orientation.Horizontal and 0<=section<len(self.HEADERS):
            return self.HEADERS[section]
        return None

    def data(self,index:QModelIndex,role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not (0<=index.row()<len(self._items)):
            return None
        item=self._items[index.row()]
        if role==Qt.ItemDataRole.UserRole:
            return str(item.path)
        if role==Qt.ItemDataRole.ToolTipRole:
            return str(item.path)
        if role!=Qt.ItemDataRole.DisplayRole:
            return None
        if index.column()==0:
            return item.path.name
        if index.column()==1:
            return str(item.path.parent)
        if index.column()==2:
            return item.note
        return None

    def set_items(self,items:list[CollectionItem])->None:
        self.beginResetModel()
        self._items=list(items)
        self.endResetModel()

    def path_at(self,row:int)->Path|None:
        return self._items[row].path if 0<=row<len(self._items) else None

    def sort(self,column:int,order:Qt.SortOrder=Qt.SortOrder.AscendingOrder)->None:
        reverse=order==Qt.SortOrder.DescendingOrder
        def key(item:CollectionItem):
            if column==0:
                return item.path.name.casefold()
            if column==1:
                return str(item.path.parent).casefold()
            return item.note.casefold()
        self.layoutAboutToBeChanged.emit()
        self._items.sort(key=key,reverse=reverse)
        self.layoutChanged.emit()
