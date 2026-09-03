"""Read embedded worksheet images from an .xlsx zip."""

from __future__ import annotations

import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

NS_R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
DRAWING_TYPE = f"{NS_R}/drawing"


def _local(tag: str) -> str:
    return tag.split("}")[-1]


def _attr_rid(attrib: dict) -> str | None:
    for key, value in attrib.items():
        if _local(key) == "id":
            return value
    return None


def _resolve(base: str, target: str) -> str:
    target = target.replace("\\", "/")
    if target.startswith("/"):
        return target.lstrip("/")
    parts = base.replace("\\", "/").split("/")[:-1]
    for chunk in target.split("/"):
        if chunk == "..":
            if parts:
                parts.pop()
        elif chunk not in ("", "."):
            parts.append(chunk)
    return "/".join(parts)


def _read_rels(zf: zipfile.ZipFile, rels_path: str) -> dict[str, dict]:
    root = ET.fromstring(zf.read(rels_path))
    rels = {}
    for rel in root:
        if _local(rel.tag) != "Relationship":
            continue
        rels[rel.attrib["Id"]] = {
            "target": rel.attrib["Target"],
            "type": rel.attrib.get("Type", ""),
        }
    return rels


def sheet_paths(zf: zipfile.ZipFile) -> dict[str, str]:
    wb_rels = _read_rels(zf, "xl/_rels/workbook.xml.rels")
    root = ET.fromstring(zf.read("xl/workbook.xml"))
    mapping = {}
    for el in root.iter():
        if _local(el.tag) != "sheet":
            continue
        name = el.attrib.get("name")
        rid = _attr_rid(el.attrib)
        if not name or not rid or rid not in wb_rels:
            continue
        mapping[name] = _resolve("xl/workbook.xml", wb_rels[rid]["target"])
    return mapping


def row_to_media(zf: zipfile.ZipFile, sheet_xml_path: str) -> dict[int, str]:
    rels_path = str(Path(sheet_xml_path).parent / "_rels" / (Path(sheet_xml_path).name + ".rels"))
    rels_path = rels_path.replace("\\", "/")
    if rels_path not in zf.namelist():
        return {}

    rels = _read_rels(zf, rels_path)
    drawing_path = None
    for rel in rels.values():
        if rel["type"] == DRAWING_TYPE or rel["type"].endswith("/drawing"):
            drawing_path = _resolve(sheet_xml_path, rel["target"])
            break
    if not drawing_path:
        return {}

    drawing_rels_path = str(
        Path(drawing_path).parent / "_rels" / (Path(drawing_path).name + ".rels")
    ).replace("\\", "/")
    drawing_rels = _read_rels(zf, drawing_rels_path) if drawing_rels_path in zf.namelist() else {}

    rid_to_media = {}
    for rid, rel in drawing_rels.items():
        media_path = _resolve(drawing_path, rel["target"])
        rid_to_media[rid] = media_path

    root = ET.fromstring(zf.read(drawing_path))
    row_media: dict[int, str] = {}
    for anchor in root.iter():
        if _local(anchor.tag) not in {"twoCellAnchor", "oneCellAnchor"}:
            continue
        row_el = None
        embed = None
        for child in anchor.iter():
            local = _local(child.tag)
            if local == "from":
                for marker in child:
                    if _local(marker.tag) == "row":
                        row_el = marker
            if local == "blip":
                embed = child.attrib.get(f"{{{NS_R}}}embed") or child.attrib.get("embed")
        if row_el is None or embed is None or embed not in rid_to_media:
            continue
        # xml broji od 0, excel/openpyxl od 1 — bez +1 bi sve bilo pomereno
        excel_row = int(row_el.text) + 1
        row_media[excel_row] = rid_to_media[embed]
    return row_media
