from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt

from app.gui.table_models import CollectionItemsModel, SearchResultsModel
from app.models.entities import CollectionItem, SearchHit


class FakeDatabase:
    def __init__(self)->None:
        self.exports=0
        self.individual_reads=0

    def export_virtual_state(self)->dict:
        self.exports+=1
        return {
            "collections":[],
            "collection_items":[],
            "virtual_items":[{"path":"/tmp/marked.txt","marked":True,"note":""}],
        }

    def virtual_item(self,_path):
        self.individual_reads+=1
        raise AssertionError("Virtuelle Trefferliste darf nicht pro Zelle einzeln aus SQLite lesen.")


def test_search_model_handles_100000_rows_without_widget_rows():
    database=FakeDatabase()
    model=SearchResultsModel(database)  # type: ignore[arg-type]
    hits=[
        SearchHit(Path(f"/tmp/datei-{index}.txt"),index+1,f"Treffer {index}","inhalt")
        for index in range(100_000)
    ]
    model.set_hits(hits)
    assert model.rowCount()==100_000
    assert model.columnCount()==5
    assert database.exports==1
    assert model.data(model.index(0,2),Qt.ItemDataRole.DisplayRole)=="/tmp/datei-0.txt"
    assert model.data(model.index(99_999,3),Qt.ItemDataRole.DisplayRole)=="100000"
    assert database.individual_reads==0


def test_search_model_marking_updates_all_hits_of_same_path():
    database=FakeDatabase()
    model=SearchResultsModel(database)  # type: ignore[arg-type]
    path=Path("/tmp/gleich.txt")
    model.set_hits([
        SearchHit(path,1,"eins","inhalt"),
        SearchHit(path,2,"zwei","inhalt"),
    ])
    model.set_marked(path,True)
    assert model.data(model.index(0,0))=="★"
    assert model.data(model.index(1,0))=="★"


def test_collection_model_is_virtual_and_returns_path():
    model=CollectionItemsModel()
    items=[
        CollectionItem(collection_id=1,path=Path(f"/tmp/{index}.txt"),note="n")
        for index in range(20_000)
    ]
    model.set_items(items)
    assert model.rowCount()==20_000
    assert model.path_at(19_999)==Path("/tmp/19999.txt")


def test_main_window_no_longer_builds_qtablewidget_rows():
    source=(Path(__file__).resolve().parents[1]/"app/gui/main_window.py").read_text(encoding="utf-8")
    assert "QTableView" in source
    assert "QTableWidget" not in source
    assert ".insertRow(" not in source
