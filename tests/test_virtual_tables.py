from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt

from app.gui.table_models import CollectionItemsModel, SearchResultsModel
from app.models.entities import CollectionItem, SearchHit, SearchJob
from app.storage.database import Database


def _search_database(tmp_path:Path,count:int=100_000)->tuple[Database,int]:
    database=Database(tmp_path/"state.sqlite3")
    database.initialize()
    job=SearchJob(tmp_path,"x")
    job_id=database.create_search_job(job)
    batch=[]
    for index in range(count):
        batch.append(SearchHit(Path(f"/tmp/datei-{index:06d}.txt"),index+1,f"Treffer {index}","inhalt"))
        if len(batch)>=1000:
            database.append_search_hits(job_id,batch)
            batch=[]
    if batch:
        database.append_search_hits(job_id,batch)
    database.finish_search_job(job_id,status="fertig",scanned_files=count,hit_count=count)
    return database,job_id


def test_search_model_pages_100000_rows_instead_of_holding_all(tmp_path:Path):
    database,job_id=_search_database(tmp_path)
    model=SearchResultsModel(database,page_size=200,max_pages=8)
    model.set_job(job_id)
    assert model.rowCount()==100_000
    assert model.cached_row_count==0
    assert model.data(model.index(0,2),Qt.ItemDataRole.DisplayRole)=="/tmp/datei-000000.txt"
    assert model.cached_row_count<=200
    assert model.data(model.index(99_999,3),Qt.ItemDataRole.DisplayRole)=="100000"
    assert model.cached_row_count<=400
    # Selbst nach Zugriffen auf viele weit auseinanderliegende Bereiche bleibt der Puffer begrenzt.
    for row in range(0,100_000,5_000):
        model.data(model.index(row,2),Qt.ItemDataRole.DisplayRole)
    assert model.cached_row_count<=model.page_size*model.max_pages


def test_search_model_sorting_is_database_backed(tmp_path:Path):
    database,job_id=_search_database(tmp_path,1000)
    model=SearchResultsModel(database,page_size=100,max_pages=3)
    model.set_job(job_id)
    model.sort(3,Qt.SortOrder.DescendingOrder)
    assert model.data(model.index(0,3))=="1000"
    assert model.cached_row_count<=100


def test_search_model_marking_refreshes_cached_pages(tmp_path:Path):
    database,job_id=_search_database(tmp_path,10)
    model=SearchResultsModel(database,page_size=25,max_pages=2)
    model.set_job(job_id)
    path=model.path_at(0)
    assert path is not None
    notifications=[]
    model.dataChanged.connect(
        lambda first,last,_roles: notifications.append((first.row(),last.row(),first.column(),last.column()))
    )
    database.set_virtual_item(path,True,"")
    model.set_marked(path,True)
    assert model.data(model.index(0,0))=="Ja"
    assert notifications==[(0,0,0,0)]


def test_compact_navigation_replaces_sidebar_on_narrow_windows():
    source=(Path(__file__).resolve().parents[1]/"app/gui/main_window.py").read_text(encoding="utf-8")
    assert 'self.width() < 960' in source
    assert 'self.compact_nav.setVisible(compact)' in source
    assert 'self.nav.setVisible(not compact)' in source


def test_collection_model_is_virtual_qt_view_and_returns_path():
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
    assert "results_model.set_job" in source
    assert "last_hits" not in source
