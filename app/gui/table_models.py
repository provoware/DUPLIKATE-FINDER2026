from __future__ import annotations

from collections import OrderedDict
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from app.models.entities import CollectionItem, DuplicateGroup, SearchHit
from app.storage.database import Database


class SearchResultsModel(QAbstractTableModel):
    """Echte Treffer-Virtualisierung: SQLite + kleiner Seitenpuffer."""

    HEADERS=("Markiert","Quelle","Datei","Zeile","Fundstelle")

    def __init__(self,database:Database,parent=None,page_size:int=200,max_pages:int=8)->None:
        super().__init__(parent)
        self.database=database
        self.page_size=max(25,int(page_size))
        self.max_pages=max(2,int(max_pages))
        self._job_id:int|None=None
        self._count=0
        self._sort_column=2
        self._descending=False
        self._pages:OrderedDict[int,list[tuple[SearchHit,bool]]]=OrderedDict()

    @property
    def cached_row_count(self)->int:
        return sum(len(page) for page in self._pages.values())

    def rowCount(self,parent=QModelIndex())->int:
        return 0 if parent.isValid() else self._count

    def columnCount(self,parent=QModelIndex())->int:
        return 0 if parent.isValid() else len(self.HEADERS)

    def headerData(self,section,orientation,role=Qt.ItemDataRole.DisplayRole):
        if role==Qt.ItemDataRole.DisplayRole and orientation==Qt.Orientation.Horizontal and 0<=section<len(self.HEADERS):
            return self.HEADERS[section]
        return None

    def set_job(self,job_id:int|None,hit_count:int|None=None)->None:
        self.beginResetModel()
        self._job_id=job_id
        self._count=(
            self.database.search_hit_count(job_id)
            if job_id is not None and hit_count is None
            else max(0,int(hit_count or 0))
        )
        self._pages.clear()
        self.endResetModel()

    def _load_page(self,page_number:int)->list[tuple[SearchHit,bool]]:
        if self._job_id is None:
            return []
        if page_number in self._pages:
            page=self._pages.pop(page_number)
            self._pages[page_number]=page
            return page
        page=self.database.search_hits_page(
            self._job_id,
            offset=page_number*self.page_size,
            limit=self.page_size,
            sort_column=self._sort_column,
            descending=self._descending,
        )
        self._pages[page_number]=page
        while len(self._pages)>self.max_pages:
            self._pages.popitem(last=False)
        return page

    def _row(self,row:int)->tuple[SearchHit,bool]|None:
        if row<0 or row>=self._count:
            return None
        page_number=row//self.page_size
        page=self._load_page(page_number)
        local=row%self.page_size
        return page[local] if local<len(page) else None

    def data(self,index:QModelIndex,role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        row=self._row(index.row())
        if row is None:
            return None
        hit,marked=row
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
            return "Ja" if marked else ""
        if index.column()==1:
            return hit.source
        if index.column()==2:
            return str(path)
        if index.column()==3:
            return "" if hit.line_number is None else str(hit.line_number)
        if index.column()==4:
            return hit.excerpt
        return None

    def hit_at(self,row:int)->SearchHit|None:
        value=self._row(row)
        return value[0] if value else None

    def path_at(self,row:int)->Path|None:
        hit=self.hit_at(row)
        return hit.path if hit else None

    def set_marked(self,path:Path,marked:bool)->None:
        changed_rows=[]
        for page_number,page in list(self._pages.items()):
            changed=False
            updated=[]
            for local_row,(hit,current) in enumerate(page):
                new_value=bool(marked) if hit.path==path else current
                changed=changed or (new_value!=current)
                updated.append((hit,new_value))
                if new_value!=current:
                    changed_rows.append(page_number*self.page_size+local_row)
            if changed:
                self._pages[page_number]=updated
        for row in changed_rows:
            self.dataChanged.emit(
                self.index(row,0),self.index(row,0),[Qt.ItemDataRole.DisplayRole]
            )

    def sort(self,column:int,order:Qt.SortOrder=Qt.SortOrder.AscendingOrder)->None:
        self.layoutAboutToBeChanged.emit()
        self._sort_column=max(0,min(len(self.HEADERS)-1,int(column)))
        self._descending=order==Qt.SortOrder.DescendingOrder
        self._pages.clear()
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
