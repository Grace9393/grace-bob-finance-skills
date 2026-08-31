#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
deep_extract.py - recursively extract every scrap of content from a document,
including the files embedded *inside* the file (OLE objects, attachments,
package streams), to arbitrary depth.

Handles:
  OOXML   .docx .xlsx .pptx .docm .xlsm .pptm  (body, tables, headers/footers,
          footnotes/endnotes, comments, tracked changes, text boxes, alt text,
          core/app properties, and word|xl|ppt/embeddings/*)
  OLE CFB .doc .xls .ppt .bin .msg             (streams, Ole10Native/Package
          payloads, legacy Word piece table, BIFF SST, PPT text atoms)
  PDF     text per page + /EmbeddedFiles + FileAttachment annots
  EML     MIME parts and attachments
  ZIP     any archive, including truncated ones (local-header salvage)

Everything recovered is written to disk so the embedded documents can be
opened directly, plus a consolidated markdown of all text.

Usage:
    python deep_extract.py INPUT [-o OUTDIR] [--max-depth N] [--no-media]
                                 [--max-text-mb N] [--quiet]

Exit codes: 0 clean, 2 completed with warnings (e.g. truncated container).
"""

from __future__ import annotations

__version__ = "2.0.0"

import argparse
import hashlib
import io
import json
import os
import re
import struct
import sys
import zipfile
import zlib
from xml.etree import ElementTree as ET

# ----------------------------------------------------------------------------
# optional deps - degrade loudly, never crash
# ----------------------------------------------------------------------------
try:
    import olefile
except ImportError:
    olefile = None
try:
    import pypdf
except ImportError:
    pypdf = None

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "o": "urn:schemas-microsoft-com:office:office",
    "v": "urn:schemas-microsoft-com:vml",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "mc": "http://schemas.openxmlformats.org/markup-compatibility/2006",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
    "s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "cp": "http://schemas.openxmlformats.org/package/2006/metadata/core-properties",
    "dc": "http://purl.org/dc/elements/1.1/",
    "dcterms": "http://purl.org/dc/terms/",
    "ep": "http://schemas.openxmlformats.org/officeDocument/2006/extended-properties",
}

MEDIA_EXT = {".emf", ".wmf", ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif",
             ".tiff", ".svg", ".ico", ".webp", ".wdp"}


def q(prefix, tag):
    return "{%s}%s" % (NS[prefix], tag)


def local(tag):
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def sha1(data):
    return hashlib.sha1(data).hexdigest()


def safe_name(name):
    name = name.replace("\\", "/")
    parts = []
    for seg in name.split("/"):
        seg = re.sub(r'[<>:"|?*\x00-\x1f]', "_", seg).rstrip(" .")
        if seg in ("", ".", ".."):
            seg = "_"
        parts.append(seg[:100])
    return "/".join(p for p in parts if p)


def printable(s, keep_newlines=False):
    """Escape control bytes for display.

    Two places produce them legitimately: OLE stream names (`\x01Ole10Native`,
    `\x03ObjInfo`) and the NUL terminator on a .msg PT_UNICODE property.
    Written raw into the output, a single NUL makes the whole markdown file
    read as binary to grep and to editors.

    `keep_newlines` preserves tab/CR/LF for fields whose value is genuinely
    multi-line, such as a mail body or header block.

    The escape is `^01`, not `\\x01`: these strings also become tree paths, and
    a backslash there is read as a directory separator, which would split one
    node name into two levels on disk.
    """
    pattern = r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]" if keep_newlines \
        else r"[\x00-\x1f\x7f]"
    return re.sub(pattern, lambda m: "^%02x" % ord(m.group()), s)


def long_path(p):
    """Windows MAX_PATH escape hatch - the extraction tree nests deeply."""
    if os.name != "nt":
        return p
    p = os.path.abspath(p)
    if p.startswith("\\\\?\\"):
        return p
    if p.startswith("\\\\"):
        return "\\\\?\\UNC\\" + p.lstrip("\\")
    return "\\\\?\\" + p


# ============================================================================
# ZIP reading, with salvage for broken / truncated containers
# ============================================================================

def read_zip_entries(data):
    """Return (ordered list of (name, bytes|None, is_partial), warnings).

    Falls back to walking local file headers when the central directory is
    missing or unreadable - the common failure mode for a truncated download.
    A zip stores its members in order, so the entry straddling the break is
    still worth inflating as far as it goes: for an embedded OOXML document
    the early parts (`[Content_Types].xml`, `word/document.xml`) usually
    survive intact, which recovers the whole body text.
    """
    warnings = []
    try:
        zf = zipfile.ZipFile(io.BytesIO(data))
        entries = []
        for info in zf.infolist():
            if info.is_dir():
                continue
            try:
                entries.append((info.filename, zf.read(info), False))
            except Exception as exc:
                warnings.append("unreadable entry %s: %s" % (info.filename, exc))
                entries.append((info.filename, None, False))
        return entries, warnings
    except Exception as exc:
        warnings.append("central directory unusable (%s) - salvaging via local "
                        "file headers" % exc)

    entries = []
    n = len(data)
    off = 0
    while off + 30 <= n:
        if data[off:off + 4] != b"PK\x03\x04":
            # resync to the next plausible local header
            nxt = data.find(b"PK\x03\x04", off + 1)
            if nxt < 0:
                break
            warnings.append("skipped %d unparsable bytes at offset %d"
                            % (nxt - off, off))
            off = nxt
            continue
        try:
            (_ver, flags, method, _t, _d, _crc, csize, usize, nlen, elen) = \
                struct.unpack("<HHHHHIIIHH", data[off + 4:off + 30])
        except struct.error:
            break
        name = data[off + 30:off + 30 + nlen].decode("utf-8", "replace")
        body_at = off + 30 + nlen + elen

        if flags & 0x08 and csize == 0:
            warnings.append("streamed entry without sizes, cannot salvage "
                            "further: %s" % name)
            break
        end = body_at + csize
        if end > n:
            avail = max(0, n - body_at)
            warnings.append("TRUNCATED: entry %r needs %d bytes but only %d "
                            "remain - container is short by %d bytes"
                            % (name, csize, avail, end - n))
            salvaged = None
            raw = data[body_at:n]
            try:
                if method == 0:
                    salvaged = raw
                elif method == 8:
                    salvaged = zlib.decompressobj(-15).decompress(raw)
            except Exception as exc:
                warnings.append("partial inflate of %s failed: %s" % (name, exc))
            if salvaged:
                warnings.append(
                    "PARTIAL: recovered %d of %d uncompressed bytes (%.1f%%) of "
                    "%r - leading content is intact, the tail is gone"
                    % (len(salvaged), usize,
                       100.0 * len(salvaged) / usize if usize else 0.0, name))
                entries.append((name, salvaged, True))
            else:
                entries.append((name, None, False))
            break
        raw = data[body_at:end]
        payload = None
        try:
            if method == 0:
                payload = raw
            elif method == 8:
                payload = zlib.decompress(raw, -15)
            else:
                warnings.append("unsupported compression %d: %s" % (method, name))
        except Exception as exc:
            warnings.append("inflate failed for %s: %s" % (name, exc))
        if not name.endswith("/"):
            entries.append((name, payload, False))
        off = end
    return entries, warnings


# ============================================================================
# OOXML text extraction
# ============================================================================

def parse_xml(blob):
    if not blob:
        return None
    try:
        return ET.fromstring(blob)
    except ET.ParseError:
        try:
            return ET.fromstring(blob.decode("utf-8", "replace")
                                 .encode("utf-8"))
        except Exception:
            return None


def load_rels(parts, part_name):
    """Relationships for a part: {rId: (Target, Type, TargetMode)}"""
    d = os.path.dirname(part_name)
    rels_name = (d + "/" if d else "") + "_rels/" + os.path.basename(part_name) + ".rels"
    root = parse_xml(parts.get(rels_name))
    out = {}
    if root is None:
        return out
    for rel in root:
        out[rel.get("Id")] = (rel.get("Target", ""), rel.get("Type", ""),
                              rel.get("TargetMode", "Internal"))
    return out


def resolve_target(part_name, target):
    if target.startswith("/"):
        return target.lstrip("/")
    base = os.path.dirname(part_name)
    joined = os.path.normpath(os.path.join(base, target)).replace("\\", "/")
    return joined.lstrip("./")


class DocxTextWriter:
    """Walks wordprocessingml and emits readable text with markers."""

    def __init__(self, parts, part_name, rels, comments, footnotes, endnotes):
        self.parts = parts
        self.part_name = part_name
        self.rels = rels
        self.comments = comments
        self.footnotes = footnotes
        self.endnotes = endnotes
        self.out = []
        self.embeds = []          # (progid, target) in document order

    def emit(self, s):
        if s:
            self.out.append(s)

    def rel_target(self, rid):
        tgt = self.rels.get(rid)
        if not tgt:
            return None
        if tgt[2] == "External":
            return tgt[0]
        return resolve_target(self.part_name, tgt[0])

    # -- inline runs -------------------------------------------------------
    def run_text(self, el, deleted=False, inserted=False):
        buf = []
        for node in el.iter():
            t = local(node.tag)
            if t == "t" and node.text:
                buf.append(node.text)
            elif t == "delText" and node.text:
                buf.append(node.text)
            elif t == "tab":
                buf.append("\t")
            elif t in ("br", "cr"):
                buf.append("\n")
            elif t == "noBreakHyphen":
                buf.append("-")
            elif t == "softHyphen":
                buf.append("")
        s = "".join(buf)
        if deleted and s:
            s = "{-%s-}" % s
        if inserted and s:
            s = "{+%s+}" % s
        return s

    def walk(self, el, deleted=False, inserted=False):
        for child in el:
            tag = local(child.tag)

            if tag == "AlternateContent":
                choice = child.find(q("mc", "Choice"))
                fallback = child.find(q("mc", "Fallback"))
                # OLE objects usually live in Fallback; prefer whichever has one
                pick = choice
                if fallback is not None and fallback.find(".//" + q("o", "OLEObject")) is not None:
                    pick = fallback
                if pick is None:
                    pick = fallback if fallback is not None else choice
                if pick is not None:
                    self.walk(pick, deleted, inserted)
                continue

            if tag == "p":
                self.walk(child, deleted, inserted)
                self.emit("\n")
                continue

            if tag == "tbl":
                self.table(child)
                continue

            if tag == "r":
                self.emit(self.run_text(child, deleted, inserted))
                # OLE objects and pictures live inside the run
                self.object_marker(child)
                seen_img = set()
                for d in child.iter():
                    dt = local(d.tag)
                    if dt == "blip":
                        rid = d.get(q("r", "embed")) or d.get(q("r", "link"))
                        tgt = self.rel_target(rid) if rid else None
                        if tgt and tgt not in seen_img:
                            seen_img.add(tgt)
                            self.emit("\n[IMAGE: %s]\n" % tgt)
                    elif dt == "docPr":
                        descr = d.get("descr")
                        if descr:
                            self.emit("\n[IMAGE ALT-TEXT: %s]\n" % descr.strip())
                continue

            if tag == "ins":
                self.walk(child, deleted, True)
                continue
            if tag == "del":
                self.walk(child, True, inserted)
                continue

            if tag == "hyperlink":
                rid = child.get(q("r", "id"))
                txt_start = len(self.out)
                self.walk(child, deleted, inserted)
                tgt = self.rel_target(rid) if rid else None
                if tgt:
                    self.emit(" <%s>" % tgt)
                elif child.get(q("w", "anchor")):
                    self.emit(" <#%s>" % child.get(q("w", "anchor")))
                del txt_start
                continue

            if tag in ("object", "pict"):
                self.object_marker(child)
                self.walk(child, deleted, inserted)
                continue

            if tag == "commentRangeStart":
                self.emit("\u27e6COMMENT-START %s\u27e7" % child.get(q("w", "id")))
                continue
            if tag == "commentRangeEnd":
                self.emit("\u27e6COMMENT-END %s\u27e7" % child.get(q("w", "id")))
                continue
            if tag == "commentReference":
                cid = child.get(q("w", "id"))
                c = self.comments.get(cid)
                if c:
                    self.emit("\n  \u27e6COMMENT %s by %s (%s): %s\u27e7\n"
                              % (cid, c["author"], c["date"], c["text"].strip()))
                continue

            if tag == "footnoteReference":
                fid = child.get(q("w", "id"))
                body = self.footnotes.get(fid, "").strip()
                if body:
                    self.emit(" [FOOTNOTE %s: %s]" % (fid, body))
                continue
            if tag == "endnoteReference":
                eid = child.get(q("w", "id"))
                body = self.endnotes.get(eid, "").strip()
                if body:
                    self.emit(" [ENDNOTE %s: %s]" % (eid, body))
                continue

            if tag == "subDoc":
                tgt = self.rel_target(child.get(q("r", "id")))
                self.emit("\n[SUBDOCUMENT LINK: %s]\n" % tgt)
                continue

            if tag in ("bookmarkStart", "bookmarkEnd", "proofErr", "lastRenderedPageBreak",
                       "sectPr", "pPr", "rPr", "tblPr", "tblGrid"):
                continue

            self.walk(child, deleted, inserted)

    def object_marker(self, el):
        for ole in el.iter(q("o", "OLEObject")):
            rid = ole.get(q("r", "id"))
            tgt = self.rel_target(rid) if rid else None
            progid = ole.get("ProgID", "?")
            self.embeds.append((progid, tgt))
            self.emit("\n\u27e6EMBEDDED OBJECT progid=%s -> %s\u27e7\n"
                      % (progid, tgt or "(unresolved %s)" % rid))
        for shp in el.iter(q("v", "shape")):
            alt = shp.get("alt")
            if alt:
                self.emit("[OBJECT ALT-TEXT: %s]\n" % alt.strip())

    def table(self, tbl):
        self.emit("\n")
        for row in tbl.findall(q("w", "tr")):
            cells = []
            for cell in row.findall(q("w", "tc")):
                sub = DocxTextWriter(self.parts, self.part_name, self.rels,
                                     self.comments, self.footnotes, self.endnotes)
                sub.walk(cell)
                self.embeds.extend(sub.embeds)
                txt = "".join(sub.out).strip().replace("\n", " / ")
                cells.append(re.sub(r"\s+", " ", txt))
            self.emit("| " + " | ".join(cells) + " |\n")
        self.emit("\n")

    def text(self):
        s = "".join(self.out)
        s = re.sub(r"[ \t]+\n", "\n", s)
        s = re.sub(r"\n{3,}", "\n\n", s)
        return s.strip()


EMBED_REL_TYPES = ("/oleObject", "/package", "/attachedToolbars", "/aFChunk")


def embedding_reconciliation(parts):
    """Every embedding the package *declares* vs what is physically present.

    A container can reference an embedded file whose part is missing - the
    normal cause is a truncated or partially-synced download. Silently
    extracting only what survived would understate the document, so the
    difference is reported explicitly.
    """
    declared = {}          # resolved target -> [(owner part, relId, Type)]
    for rels_name in [n for n in parts if n.lower().endswith(".rels")]:
        root = parse_xml(parts.get(rels_name))
        if root is None:
            continue
        d = os.path.dirname(os.path.dirname(rels_name))     # strip /_rels
        owner = (d + "/" if d else "") + os.path.basename(rels_name)[:-5]
        for rel in root:
            if rel.get("TargetMode") == "External":
                continue
            rtype = rel.get("Type", "")
            target = rel.get("Target", "")
            if not (any(rtype.endswith(t) for t in EMBED_REL_TYPES)
                    or "/embeddings/" in target.replace("\\", "/")):
                continue
            resolved = resolve_target(owner, target)
            declared.setdefault(resolved, []).append(
                (owner, rel.get("Id"), rtype.rsplit("/", 1)[-1]))

    present = [t for t in declared if t in parts]
    missing = sorted(t for t in declared if t not in parts)
    return declared, present, missing


def notes_map(parts, name, tagname):
    root = parse_xml(parts.get(name))
    out = {}
    if root is None:
        return out
    for note in root.findall(q("w", tagname)):
        nid = note.get(q("w", "id"))
        buf = []
        for t in note.iter():
            if local(t.tag) in ("t", "delText") and t.text:
                buf.append(t.text)
        out[nid] = "".join(buf)
    return out


def comments_map(parts):
    root = parse_xml(parts.get("word/comments.xml"))
    out = {}
    if root is None:
        return out
    for c in root.findall(q("w", "comment")):
        buf = []
        for t in c.iter():
            if local(t.tag) in ("t", "delText") and t.text:
                buf.append(t.text)
        out[c.get(q("w", "id"))] = {
            "author": c.get(q("w", "author"), "?"),
            "date": c.get(q("w", "date"), ""),
            "initials": c.get(q("w", "initials"), ""),
            "text": "".join(buf),
        }
    return out


def core_properties(parts):
    lines = []
    root = parse_xml(parts.get("docProps/core.xml"))
    if root is not None:
        for child in root:
            if child.text and child.text.strip():
                lines.append("%s: %s" % (local(child.tag), child.text.strip()))
    root = parse_xml(parts.get("docProps/app.xml"))
    if root is not None:
        for child in root:
            if child.text and child.text.strip() and local(child.tag) in (
                    "Application", "Company", "Manager", "TotalTime", "Pages",
                    "Words", "Template", "AppVersion"):
                lines.append("%s: %s" % (local(child.tag), child.text.strip()))
    root = parse_xml(parts.get("docProps/custom.xml"))
    if root is not None:
        for prop in root:
            nm = prop.get("name")
            val = "".join(x.text or "" for x in prop)
            if nm and val.strip():
                lines.append("custom:%s: %s" % (nm, val.strip()))
    return "\n".join(lines)


def docx_text(parts):
    sections = []
    props = core_properties(parts)
    if props:
        sections.append(("Document properties", props))

    comments = comments_map(parts)
    footnotes = notes_map(parts, "word/footnotes.xml", "footnote")
    endnotes = notes_map(parts, "word/endnotes.xml", "endnote")

    root = parse_xml(parts.get("word/document.xml"))
    all_embeds = []
    if root is not None:
        rels = load_rels(parts, "word/document.xml")
        body = root.find(q("w", "body"))
        writer = DocxTextWriter(parts, "word/document.xml", rels, comments,
                                footnotes, endnotes)
        writer.walk(body if body is not None else root)
        sections.append(("Body", writer.text()))
        all_embeds = writer.embeds

    for kind in ("header", "footer"):
        for name in sorted(n for n in parts if re.match(r"word/%s\d*\.xml$" % kind, n)):
            r = parse_xml(parts.get(name))
            if r is None:
                continue
            wtr = DocxTextWriter(parts, name, load_rels(parts, name), comments,
                                 footnotes, endnotes)
            wtr.walk(r)
            txt = wtr.text()
            if txt:
                sections.append((name, txt))

    if comments:
        rows = ["| id | author | date | text |", "|---|---|---|---|"]
        for cid in sorted(comments, key=lambda x: int(x) if x.isdigit() else 0):
            c = comments[cid]
            rows.append("| %s | %s | %s | %s |" % (
                cid, c["author"], c["date"],
                re.sub(r"\s+", " ", c["text"]).strip()))
        sections.append(("Comments (%d)" % len(comments), "\n".join(rows)))

    orphan = [(k, v) for k, v in footnotes.items() if v.strip()]
    if orphan:
        sections.append(("Footnotes", "\n".join("[%s] %s" % (k, v.strip())
                                                for k, v in orphan)))
    orphan = [(k, v) for k, v in endnotes.items() if v.strip()]
    if orphan:
        sections.append(("Endnotes", "\n".join("[%s] %s" % (k, v.strip())
                                               for k, v in orphan)))
    if all_embeds:
        rows = ["| # | ProgID | part |", "|---|---|---|"]
        for i, (pid, tgt) in enumerate(all_embeds, 1):
            rows.append("| %d | %s | %s |" % (i, pid, tgt or "?"))
        sections.append(("Embedded objects referenced in body (%d)"
                         % len(all_embeds), "\n".join(rows)))
    return sections


def sheet_rows(blob, shared):
    """Stream a worksheet part, emitting only rows that carry content.

    Streaming matters: Excel routinely writes 1,048,576 styled-but-empty rows,
    so a sheet holding a few hundred real values can be a 130 MB XML part.
    Building a DOM for that costs gigabytes; iterparse with per-row clearing
    keeps it flat.
    """
    lines = []
    try:
        ctx = ET.iterparse(io.BytesIO(blob), events=("start", "end"))
        sheetdata = None
        for event, el in ctx:
            if event == "start":
                if el.tag == q("s", "sheetData"):
                    sheetdata = el
                continue
            if el.tag != q("s", "row"):
                continue
            vals = []
            for c in el.findall(q("s", "c")):
                ctype = c.get("t")
                v = c.find(q("s", "v"))
                isel = c.find(q("s", "is"))
                f = c.find(q("s", "f"))
                if ctype == "s" and v is not None and v.text is not None:
                    try:
                        idx = int(v.text)
                    except ValueError:
                        idx = -1
                    txt = shared[idx] if 0 <= idx < len(shared) else ""
                elif ctype == "inlineStr" and isel is not None:
                    txt = "".join(t.text or "" for t in isel.iter(q("s", "t")))
                elif v is not None:
                    txt = v.text or ""
                else:
                    txt = ""
                if f is not None and f.text:
                    txt = "%s\t(=%s)" % (txt, f.text)
                if txt:
                    vals.append("%s=%s" % (c.get("r", ""), txt))
            if vals:
                lines.append("\t".join(vals))
            el.clear()
            if sheetdata is not None:
                sheetdata.clear()          # drop finished rows, bound memory
    except ET.ParseError:
        pass
    return lines


def xlsx_text(parts):
    sections = []
    props = core_properties(parts)
    if props:
        sections.append(("Document properties", props))

    shared = []
    root = parse_xml(parts.get("xl/sharedStrings.xml"))
    if root is not None:
        for si in root:
            shared.append("".join(t.text or "" for t in si.iter(q("s", "t"))))

    wb = parse_xml(parts.get("xl/workbook.xml"))
    rels = load_rels(parts, "xl/workbook.xml")
    sheets = []
    if wb is not None:
        for sh in wb.iter(q("s", "sheet")):
            rid = sh.get(q("r", "id"))
            tgt = rels.get(rid, ("", "", ""))[0]
            sheets.append((sh.get("name", "?"),
                           resolve_target("xl/workbook.xml", tgt) if tgt else None))
    if not sheets:
        sheets = [(n, n) for n in sorted(parts) if re.match(r"xl/worksheets/sheet\d+\.xml$", n)]

    for sheet_name, part in sheets:
        blob = parts.get(part) if part else None
        if blob is None:
            continue
        lines = sheet_rows(blob, shared)
        if lines:
            sections.append(("Sheet: %s (%s)" % (sheet_name, part), "\n".join(lines)))

    for name in sorted(n for n in parts if re.match(r"xl/comments\d*\.xml$", n)):
        root = parse_xml(parts.get(name))
        if root is None:
            continue
        authors = [a.text or "" for a in root.iter(q("s", "author"))]
        lines = []
        for cm in root.iter(q("s", "comment")):
            ai = cm.get("authorId")
            who = authors[int(ai)] if ai and ai.isdigit() and int(ai) < len(authors) else "?"
            body = "".join(t.text or "" for t in cm.iter(q("s", "t")))
            lines.append("%s [%s]: %s" % (cm.get("ref", "?"), who,
                                          re.sub(r"\s+", " ", body).strip()))
        if lines:
            sections.append((name, "\n".join(lines)))
    return sections


def pptx_text(parts):
    sections = []
    props = core_properties(parts)
    if props:
        sections.append(("Document properties", props))

    def slide_no(n):
        m = re.search(r"(\d+)\.xml$", n)
        return int(m.group(1)) if m else 0

    slides = sorted((n for n in parts if re.match(r"ppt/slides/slide\d+\.xml$", n)),
                    key=slide_no)
    for name in slides:
        root = parse_xml(parts.get(name))
        if root is None:
            continue
        lines = []
        for sp in root.iter():
            if local(sp.tag) == "p" and sp.tag.startswith("{%s}" % NS["a"]):
                txt = "".join(t.text or "" for t in sp.iter(q("a", "t")))
                if txt.strip():
                    lines.append(txt)
        for pr in root.iter(q("p", "cNvPr")):
            if pr.get("descr"):
                lines.append("[ALT-TEXT: %s]" % pr.get("descr").strip())
        notes = name.replace("ppt/slides/slide", "ppt/notesSlides/notesSlide")
        nroot = parse_xml(parts.get(notes))
        if nroot is not None:
            ntxt = []
            for sp in nroot.iter():
                if local(sp.tag) == "p" and sp.tag.startswith("{%s}" % NS["a"]):
                    t = "".join(x.text or "" for x in sp.iter(q("a", "t")))
                    if t.strip():
                        ntxt.append(t)
            if ntxt:
                lines.append("[SPEAKER NOTES] " + " / ".join(ntxt))
        if lines:
            sections.append((name, "\n".join(lines)))
    return sections


# ============================================================================
# OLE compound file (CFB)
# ============================================================================

def ole10native(data):
    """Unwrap an Ole10Native / Package stream -> (filename, payload)."""
    try:
        if len(data) < 10:
            raise ValueError("too short")
        pos = 4                                   # total size dword
        flags = struct.unpack("<H", data[pos:pos + 2])[0]
        pos += 2
        del flags

        def zstr(p):
            e = data.index(b"\x00", p)
            return data[p:e].decode("latin-1"), e + 1

        label, pos = zstr(pos)
        filepath, pos = zstr(pos)
        pos += 4                                   # unknown
        tlen = struct.unpack("<I", data[pos:pos + 4])[0]
        pos += 4 + tlen
        size = struct.unpack("<I", data[pos:pos + 4])[0]
        pos += 4
        payload = data[pos:pos + size]
        if not payload:
            raise ValueError("empty payload")
        name = os.path.basename(filepath.replace("\\", "/")) or label or "package.bin"
        return name, payload
    except Exception:
        pass
    # fallback: cut from the first recognisable magic
    for magic, ext in ((b"PK\x03\x04", ".zip"),
                       (b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1", ".bin"),
                       (b"%PDF-", ".pdf"),
                       (b"{\\rtf", ".rtf")):
        i = data.find(magic)
        if 0 <= i < 4096:
            return "package_salvaged" + ext, data[i:]
    return None, None


def doc_text(worddoc, table0, table1):
    """Word 97-2003 text via the piece table."""
    try:
        if len(worddoc) < 0x100:
            return ""
        flags = struct.unpack("<H", worddoc[0x0A:0x0C])[0]
        table = table1 if (flags & 0x0200) else table0
        if not table:
            table = table1 or table0
        if not table:
            return ""
        fcClx, lcbClx = struct.unpack("<II", worddoc[0x01A2:0x01AA])
        clx = table[fcClx:fcClx + lcbClx]
        # skip Prc entries (0x01) to reach the Pcdt (0x02)
        i = 0
        while i < len(clx) and clx[i] == 0x01:
            cb = struct.unpack("<H", clx[i + 1:i + 3])[0]
            i += 3 + cb
        if i >= len(clx) or clx[i] != 0x02:
            return ""
        lcb = struct.unpack("<I", clx[i + 1:i + 5])[0]
        plc = clx[i + 5:i + 5 + lcb]
        n = (len(plc) - 4) // 12
        cps = [struct.unpack("<I", plc[4 * k:4 * k + 4])[0] for k in range(n + 1)]
        out = []
        for k in range(n):
            pcd = plc[4 * (n + 1) + 8 * k: 4 * (n + 1) + 8 * k + 8]
            fc = struct.unpack("<I", pcd[2:6])[0]
            length = cps[k + 1] - cps[k]
            if fc & 0x40000000:
                start = (fc & ~0x40000000) // 2
                chunk = worddoc[start:start + length]
                out.append(chunk.decode("cp1252", "replace"))
            else:
                chunk = worddoc[fc:fc + length * 2]
                out.append(chunk.decode("utf-16-le", "replace"))
        txt = "".join(out)
        txt = txt.replace("\r", "\n").replace("\x07", "\t").replace("\x0b", "\n")
        txt = re.sub(r"[\x00-\x08\x0e-\x1f]", "", txt)
        return re.sub(r"\n{3,}", "\n\n", txt).strip()
    except Exception:
        return ""


def xls_text(workbook):
    """BIFF8 shared string table + label cells - text content of a legacy .xls.

    Best effort: SST records that spill into CONTINUE records are read up to
    the first spill boundary, so very large workbooks may lose the tail.
    """
    out = []
    sst = []
    try:
        pos = 0
        n = len(workbook)
        while pos + 4 <= n:
            rec, size = struct.unpack("<HH", workbook[pos:pos + 4])
            body = workbook[pos + 4:pos + 4 + size]
            pos += 4 + size
            if rec == 0x00FC and len(body) >= 8:                 # SST
                cnt = struct.unpack("<I", body[4:8])[0]
                p = 8
                for _ in range(min(cnt, 500000)):
                    if p + 3 > len(body):
                        break
                    clen = struct.unpack("<H", body[p:p + 2])[0]
                    grbit = body[p + 2]
                    p += 3
                    c_run = 0
                    cb_ext = 0
                    if grbit & 0x08:                             # fRichSt
                        if p + 2 > len(body):
                            break
                        c_run = struct.unpack("<H", body[p:p + 2])[0]
                        p += 2
                    if grbit & 0x04:                             # fExtSt
                        if p + 4 > len(body):
                            break
                        cb_ext = struct.unpack("<I", body[p:p + 4])[0]
                        p += 4
                    if grbit & 0x01:                             # fHighByte
                        s = body[p:p + clen * 2].decode("utf-16-le", "replace")
                        p += clen * 2
                    else:
                        s = body[p:p + clen].decode("latin-1", "replace")
                        p += clen
                    p += 4 * c_run + cb_ext
                    sst.append(s)
            elif rec == 0x0204 and len(body) >= 8:               # LABEL
                row, col = struct.unpack("<HH", body[0:4])
                out.append("R%dC%d\t%s" % (row + 1, col + 1,
                                           body[8:].decode("latin-1", "replace")))
            elif rec == 0x027E and len(body) >= 6:               # RK (numeric)
                row, col = struct.unpack("<HH", body[0:4])
                out.append("R%dC%d\t<numeric>" % (row + 1, col + 1))
    except Exception:
        pass
    if sst:
        out.append("--- shared strings (%d) ---" % len(sst))
        out.extend(s for s in sst if s.strip())
    return "\n".join(out).strip()


def ppt_text(stream):
    """PowerPoint 97-2003 TextBytesAtom / TextCharsAtom records."""
    out = []
    pos = 0
    n = len(stream)
    while pos + 8 <= n:
        try:
            _v, rtype, rlen = struct.unpack("<HHI", stream[pos:pos + 8])
        except struct.error:
            break
        body = stream[pos + 8:pos + 8 + rlen]
        if rtype == 0x0FA8:                                    # TextBytesAtom
            out.append(body.decode("latin-1", "replace"))
        elif rtype == 0x0FA0:                                  # TextCharsAtom
            out.append(body.decode("utf-16-le", "replace"))
        pos += 8 + rlen
        if rlen == 0:
            pos += 1
    txt = "\n".join(out).replace("\r", "\n")
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", txt).strip()


MSG_FIELDS = {"0037": "Subject", "0C1A": "From", "0C1F": "FromAddr",
              "0E04": "To", "0E03": "Cc", "1000": "Body", "007D": "Headers",
              "0070": "Topic", "0039": "Sent", "3007": "Created",
              "3707": "AttachFilename", "3704": "AttachShortName",
              "370E": "AttachMimeType"}


def _msg_decode(raw, kind):
    s = raw.decode("utf-16-le" if kind == "001F" else "latin-1", "replace")
    # PT_UNICODE properties carry a trailing NUL terminator
    return printable(s.rstrip("\x00"), keep_newlines=True)


def msg_fields_by_storage(ole):
    """{storage-prefix: {FieldName: value}} - covers nested .msg attachments."""
    groups = {}
    for entry in ole.listdir(streams=True, storages=False):
        nm = entry[-1]
        m = re.match(r"__substg1\.0_([0-9A-Fa-f]{4})(001F|001E)$", nm)
        if not m:
            continue
        tag = m.group(1).upper()
        if tag not in MSG_FIELDS:
            continue
        try:
            raw = ole.openstream(entry).read()
        except Exception:
            continue
        prefix = "/".join(entry[:-1])
        groups.setdefault(prefix, {})[MSG_FIELDS[tag]] = \
            _msg_decode(raw, m.group(2)).strip()
    return groups


def msg_strings(ole):
    """Outlook .msg headline fields, including nested message attachments."""
    groups = msg_fields_by_storage(ole)
    out = []
    for prefix in sorted(groups, key=lambda p: (p.count("/"), p)):
        fields = groups[prefix]
        if not fields:
            continue
        out.append("--- %s ---" % (prefix or "(top-level message)"))
        for key in ("Subject", "From", "FromAddr", "To", "Cc", "Sent",
                    "AttachFilename", "AttachShortName", "AttachMimeType",
                    "Headers", "Body"):
            if fields.get(key):
                out.append("%s: %s" % (key, fields[key]))
        out.append("")
    return "\n".join(out).strip()


# ============================================================================
# PDF
# ============================================================================

def pdf_extract(data):
    """Return (sections, [(name, bytes)] attachments, warnings)."""
    if pypdf is None:
        return [("PDF", "(pypdf not installed - `pip install pypdf` to read PDFs)")], [], \
               ["pypdf missing"]
    sections, attachments, warnings = [], [], []
    try:
        reader = pypdf.PdfReader(io.BytesIO(data))
    except Exception as exc:
        return [], [], ["pdf unreadable: %s" % exc]

    meta = []
    try:
        for k, v in (reader.metadata or {}).items():
            meta.append("%s: %s" % (k, v))
    except Exception:
        pass
    if meta:
        sections.append(("PDF metadata", "\n".join(meta)))

    pages = []
    empty = 0
    for i, page in enumerate(reader.pages, 1):
        try:
            t = page.extract_text() or ""
        except Exception as exc:
            t = ""
            warnings.append("page %d text failed: %s" % (i, exc))
        if not t.strip():
            empty += 1
        pages.append("--- page %d ---\n%s" % (i, t.strip()))
    if pages:
        sections.append(("PDF text (%d pages)" % len(pages), "\n\n".join(pages)))
    if empty and empty == len(pages):
        warnings.append("all %d pages produced no text - likely a scanned PDF, "
                        "OCR needed" % empty)
    try:
        for name, blob in (reader.attachments or {}).items():
            for j, b in enumerate(blob if isinstance(blob, list) else [blob]):
                attachments.append(("%s%s" % (name, "" if j == 0 else "_%d" % j),
                                    bytes(b)))
    except Exception as exc:
        warnings.append("attachment enumeration failed: %s" % exc)
    return sections, attachments, warnings


# ============================================================================
# recursive driver
# ============================================================================

class Extractor:
    def __init__(self, outdir, max_depth=8, save_media=True, max_text_mb=0,
                 quiet=False, nested=False):
        self.outdir = outdir
        self.max_depth = max_depth
        self.save_media = save_media
        self.max_text_bytes = int(max_text_mb * 1024 * 1024) if max_text_mb else 0
        self.quiet = quiet
        self.nested = nested
        self.indices = {}
        self.manifest = []
        self.text_blocks = []       # (treepath, kind, [(title, text)])
        self.warnings = []
        self.used_paths = set()     # collision guard for truncated names
        self.seen = {}              # sha1 -> treepath (duplicate detection)
        self.partial_paths = set()  # nodes recovered from a cut-off stream
        self.counts = {"containers": 0, "embedded_files": 0, "media": 0,
                       "text_nodes": 0, "partial": 0}

    def log(self, msg):
        if not self.quiet:
            print(msg, flush=True)

    # -- disk -------------------------------------------------------------
    @staticmethod
    def as_relpath(treepath):
        """Map a tree path to a filesystem path.

        Every container level gets a `~` suffix *after* per-component
        truncation, so the directory holding a container's children can never
        collide with the file holding the container itself.
        """
        segs = treepath.split(" > ")
        out = []
        for i, seg in enumerate(segs):
            seg = safe_name(seg)
            if not seg:
                seg = "_"
            if i < len(segs) - 1:
                seg += "~"
            out.append(seg)
        return "/".join(out)

    def _write(self, rel, data, mode="wb", encoding=None):
        # truncation can make two tree paths collide - never silently overwrite
        base, ext = os.path.splitext(rel)
        n = 2
        while rel in self.used_paths:
            rel = "%s__%d%s" % (base, n, ext)
            n += 1
        self.used_paths.add(rel)

        full = os.path.join(self.outdir, rel)
        os.makedirs(long_path(os.path.dirname(full)), exist_ok=True)
        if encoding:
            with io.open(long_path(full), mode, encoding=encoding) as fh:
                fh.write(data)
        else:
            with open(long_path(full), mode) as fh:
                fh.write(data)
        return rel.replace("\\", "/")

    def node_index(self, treepath):
        """Stable number per node, shared by recovered/ and text/ so item 013
        in one is item 013 in the other."""
        if treepath not in self.indices:
            self.indices[treepath] = len(self.indices) + 1
        return self.indices[treepath]

    @staticmethod
    def display_name(treepath):
        """The name a person would recognise.

        Container internals carry machine names - `^01Ole10Native`,
        `__substg1.0_37010102` - with the real filename in parentheses after
        them. Prefer the real one.
        """
        leaf = treepath.split(" > ")[-1].split("/")[-1]
        # greedy, so a name that itself contains parentheses survives whole:
        # "^01Ole10Native (RE Alignment (ZCRQ processing).msg)"
        m = re.search(r"\((.+\.[A-Za-z0-9]{1,8})\)\s*$", leaf)
        if m:
            leaf = m.group(1)
        return safe_name(leaf) or "item"

    def flat_name(self, treepath, suffix=""):
        stem, ext = os.path.splitext(self.display_name(treepath))
        return "%03d_%s%s%s" % (self.node_index(treepath), stem[:70],
                                ext[:12], suffix)

    def save(self, treepath, data, depth=1):
        """Write a recovered file out.

        Flat by default. Mirroring the containment tree on disk produces paths
        that routinely pass 260 characters - Explorer cannot open them and
        ordinary copy tools fail part-way - so recovered files go into one
        `recovered/` directory, numbered in tree order. The containment
        structure is not lost: it is in `_TREE.txt` and in each manifest
        node's `path`. `--nested` restores the mirrored layout.
        """
        if depth == 0:
            return None                      # root is the source file itself
        if self.nested:
            return self._write(os.path.join("files", self.as_relpath(treepath)),
                               data)
        return self._write(os.path.join("recovered",
                                        self.flat_name(treepath)), data)

    def add_text(self, treepath, kind, sections):
        sections = [(t, s) for t, s in sections if s and s.strip()]
        if not sections:
            return None
        self.counts["text_nodes"] += 1
        self.text_blocks.append((treepath, kind, sections))
        rel = os.path.join("text", (self.as_relpath(treepath) + ".md")
                           if self.nested else self.flat_name(treepath, ".md"))
        buf = ["# %s\n\n" % treepath]
        for title, body in sections:
            buf.append("## %s\n\n%s\n\n" % (title, body))
        return self._write(rel, "".join(buf), "w", "utf-8")

    # -- dispatch ---------------------------------------------------------
    @staticmethod
    def sniff(data, name):
        ext = os.path.splitext(name)[1].lower()
        if data[:4] == b"PK\x03\x04":
            return "zip"
        if data[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
            return "ole"
        if data[:5] == b"%PDF-":
            return "pdf"
        if data[:5] == b"{\\rtf":
            return "rtf"
        if ext in MEDIA_EXT:
            return "media"
        if data[:4] == b"\x01\x00\x00\x00" and data[40:44] == b" EMF":
            return "media"
        if data[:4] in (b"\xd7\xcd\xc6\x9a", b"\x01\x00\x09\x00"):
            return "media"
        if data[:8] in (b"\x89PNG\r\n\x1a\n",) or data[:2] == b"\xff\xd8" \
                or data[:6] in (b"GIF87a", b"GIF89a"):
            return "media"
        if ext in (".xml", ".rels", ".txt", ".csv", ".json", ".htm", ".html", ".md"):
            return "text"
        if ext == ".eml" or data[:5] in (b"From ", b"Retur", b"Recei"):
            return "eml"
        return "binary"

    @staticmethod
    def zip_flavour(parts):
        if "word/document.xml" in parts:
            return "docx"
        if "xl/workbook.xml" in parts:
            return "xlsx"
        if "ppt/presentation.xml" in parts:
            return "pptx"
        return "zip"

    def node(self, treepath, name, data, kind, **extra):
        rec = {"path": treepath, "name": name,
               "size": len(data) if data is not None else None,
               "sha1": sha1(data) if data else None, "kind": kind}
        rec.update(extra)
        self.manifest.append(rec)
        return rec

    def process(self, data, name, treepath, depth, partial=False):
        if data is None:
            self.node(treepath, name, None, "missing",
                      status="not recovered (truncated or unreadable)")
            return
        kind = self.sniff(data, name)
        indent = "  " * depth
        self.log("%s%-9s %11s  %s%s" % (indent, kind, "{:,}".format(len(data)),
                                        treepath, "  [PARTIAL]" if partial else ""))
        if partial:
            self.counts["partial"] += 1
            self.partial_paths.add(treepath)

        dup = self.seen.get(sha1(data))
        self.seen.setdefault(sha1(data), treepath)

        if depth > self.max_depth:
            self.node(treepath, name, data, kind,
                      saved_as=self.save(treepath, data, depth),
                      status="max depth %d reached, not descended" % self.max_depth)
            self.warnings.append("max depth reached at %s" % treepath)
            return

        if kind == "zip":
            self.zip_node(data, name, treepath, depth, dup)
        elif kind == "ole":
            self.ole_node(data, name, treepath, depth, dup)
        elif kind == "pdf":
            self.pdf_node(data, name, treepath, depth, dup)
        elif kind == "eml":
            self.eml_node(data, name, treepath, depth, dup)
        elif kind == "media":
            self.counts["media"] += 1
            saved = self.save(treepath, data, depth) if self.save_media else None
            self.node(treepath, name, data, "media", saved_as=saved,
                      duplicate_of=dup)
        elif kind in ("text", "rtf"):
            txt = data.decode("utf-8", "replace")
            if kind == "rtf":
                txt = rtf_to_text(txt)
            tf = self.add_text(treepath, kind, [(name, txt)])
            self.node(treepath, name, data, kind,
                      saved_as=self.save(treepath, data, depth), text_file=tf,
                      duplicate_of=dup)
        else:
            saved = self.save(treepath, data, depth)
            strings = printable_strings(data)
            tf = self.add_text(treepath, "binary-strings",
                               [("recovered strings", strings)]) if strings else None
            self.node(treepath, name, data, "binary", saved_as=saved,
                      text_file=tf, duplicate_of=dup)

    # -- containers -------------------------------------------------------
    def zip_node(self, data, name, treepath, depth, dup):
        self.counts["containers"] += 1
        entries, warns = read_zip_entries(data)
        for w in warns:
            self.warnings.append("%s: %s" % (treepath, w))
            self.log("      ! %s" % w)
        parts = {n: b for n, b, _ in entries if b is not None}
        partials = set(n for n, b, p in entries if p and b is not None)
        flavour = self.zip_flavour(parts)

        sections = []
        missing = []
        if flavour == "docx":
            sections = docx_text(parts)
        elif flavour == "xlsx":
            sections = xlsx_text(parts)
        elif flavour == "pptx":
            sections = pptx_text(parts)

        if flavour in ("docx", "xlsx", "pptx"):
            declared, present, missing = embedding_reconciliation(parts)
            if declared:
                n_part = len([t for t in declared if t in partials])
                rows = ["Declared by the package: %d | physically present: %d "
                        "(of which partial: %d) | MISSING: %d"
                        % (len(declared), len(present), n_part, len(missing)),
                        "", "| embedding part | present | referenced from |",
                        "|---|---|---|"]
                for tgt in sorted(declared):
                    refs = "; ".join("%s#%s" % (o, i) for o, i, _ in declared[tgt])
                    if tgt in partials:
                        state = "**PARTIAL**"
                    elif tgt in parts:
                        state = "yes"
                    else:
                        state = "**NO**"
                    rows.append("| %s | %s | %s |" % (tgt, state, refs))
                sections.append(("Embeddings declared vs recovered", "\n".join(rows)))
            if missing:
                msg = ("%d embedded file(s) are referenced but absent from the "
                       "package: %s" % (len(missing), ", ".join(missing)))
                self.warnings.append("%s: %s" % (treepath, msg))
                self.log("      ! %s" % msg)

        tf = self.add_text(treepath, flavour, sections)

        self.node(treepath, name, data, flavour,
                  saved_as=self.save(treepath, data, depth),
                  text_file=tf, entries=len(entries), duplicate_of=dup,
                  missing_embeddings=missing or None,
                  partial_embeddings=sorted(partials) or None,
                  status="PARTIAL - recovered from a cut-off stream"
                         if treepath in self.partial_paths else None,
                  warnings=warns or None)

        for ename, ebytes, epartial in entries:
            lower = ename.lower()
            child_ext = os.path.splitext(lower)[1]
            is_embedding = "/embeddings/" in lower or "oleobject" in lower
            is_ooxml_plumbing = (flavour in ("docx", "xlsx", "pptx")
                                 and lower.endswith((".xml", ".rels")))
            is_media = (child_ext in MEDIA_EXT or "/media/" in lower
                        or "thumbnail" in lower)

            if is_ooxml_plumbing and not is_embedding:
                continue                      # already rendered above
            if is_media:
                self.counts["media"] += 1
                child = treepath + " > " + ename
                self.node(child, ename, ebytes, "media",
                          saved_as=self.save(child, ebytes, depth + 1)
                          if (self.save_media and ebytes is not None) else None,
                          status="PARTIAL - stream cut off" if epartial else None)
                continue
            if is_embedding:
                self.counts["embedded_files"] += 1
            self.process(ebytes, os.path.basename(ename),
                         treepath + " > " + ename, depth + 1, partial=epartial)

    def ole_node(self, data, name, treepath, depth, dup):
        self.counts["containers"] += 1
        saved = self.save(treepath, data, depth)
        if olefile is None:
            self.warnings.append("olefile not installed - %s not opened" % treepath)
            self.node(treepath, name, data, "ole", saved_as=saved,
                      status="olefile missing (`pip install olefile`)")
            return
        try:
            ole = olefile.OleFileIO(io.BytesIO(data))
        except Exception as exc:
            self.warnings.append("%s: OLE open failed: %s" % (treepath, exc))
            self.node(treepath, name, data, "ole", saved_as=saved,
                      status="unreadable: %s" % exc)
            return

        streams = ole.listdir(streams=True, storages=False)
        stream_names = ["/".join(s) for s in streams]
        sections = []
        try:
            meta = ole.get_metadata()
            mlines = []
            for attr in ("title", "author", "company", "last_saved_by",
                         "create_time", "last_saved_time", "num_pages"):
                v = getattr(meta, attr, None)
                if isinstance(v, bytes):
                    v = v.decode("latin-1", "replace").strip()
                if v:
                    mlines.append("%s: %s" % (attr, v))
            if mlines:
                sections.append(("OLE summary information", "\n".join(mlines)))
        except Exception:
            pass

        def get(path):
            try:
                return ole.openstream(path).read()
            except Exception:
                return b""

        progid = ""
        if ole.exists("\x01CompObj"):
            blob = get("\x01CompObj")
            ascii_bits = re.findall(rb"[ -~]{4,}", blob)
            progid = " | ".join(b.decode("latin-1") for b in ascii_bits[-3:])
            if progid:
                sections.append(("CompObj / ProgID", progid))

        # legacy Office payloads
        if "WordDocument" in stream_names:
            txt = doc_text(get("WordDocument"), get("0Table") if "0Table" in stream_names else b"",
                           get("1Table") if "1Table" in stream_names else b"")
            if txt:
                sections.append(("Word 97-2003 body text", txt))
        if "Workbook" in stream_names or "Book" in stream_names:
            txt = xls_text(get("Workbook" if "Workbook" in stream_names else "Book"))
            if txt:
                sections.append(("Excel 97-2003 text", txt))
        if "PowerPoint Document" in stream_names:
            txt = ppt_text(get("PowerPoint Document"))
            if txt:
                sections.append(("PowerPoint 97-2003 text", txt))
        encrypted = None
        if "EncryptedPackage" in stream_names:
            drm = any("DRMEncryptedTransform" in x for x in stream_names)
            encrypted = ("IRM / sensitivity-label encrypted" if drm
                         else "password-encrypted")
            size = ole.get_size("EncryptedPackage")
            msg = ("contents are %s - %s bytes of payload are present but "
                   "unreadable without the credentials that open it; no text "
                   "was recovered from this file" % (encrypted, format(size, ",")))
            self.warnings.append("%s: %s" % (treepath, msg))
            self.log("      ! %s" % msg)
            sections.append(("Encrypted package",
                             "This container is %s. %s bytes of "
                             "encrypted payload sit in the "
                             "EncryptedPackage stream and nothing inside "
                             "can be read here. The container has been "
                             "saved intact - open it in Office with the "
                             "rights that apply to it."
                             % (encrypted, format(size, ","))))

        # An OLE object can be an empty shell: Word still draws its icon from
        # the cached preview image, so the document looks like it carries a
        # file when the payload was never stored or was later stripped.
        payload_names = ("\x01Ole10Native", "Ole10Native", "Package", "CONTENTS",
                         "WordDocument", "Workbook", "Book",
                         "PowerPoint Document", "EncryptedPackage")
        has_payload = any(s.rsplit("/", 1)[-1] in payload_names
                          or "__substg1.0_" in s for s in stream_names)
        # Streams that carry no content of their own - their presence alone
        # does not mean the object holds anything.
        trivial_names = ("\x03ObjInfo", "\x01CompObj", "\x01Ole", "\x03LinkInfo",
                         "SummaryInformation", "DocumentSummaryInformation")
        substantive = [s for s in stream_names
                       if s.rsplit("/", 1)[-1] not in trivial_names]

        shell_status = None
        if not has_payload and not substantive:
            shell_status = "EMPTY SHELL - no payload, icon has no file behind it"
            msg = ("embedded object is empty (only %s) - the icon shown in the "
                   "document has no file behind it"
                   % ", ".join(printable(s) for s in stream_names[:4]))
            self.warnings.append("%s: %s" % (treepath, msg))
            self.log("      ! %s" % msg)
            sections.append(("Empty object shell",
                             "No content stream is present in this container. "
                             "The parent document displays an icon for it, but "
                             "there is no embedded file to open."))
        elif not has_payload:
            # Data is present in a format this tool does not model - a
            # third-party add-in, for example. Say so rather than claiming the
            # object is empty, and surface anything that reads as text.
            shell_status = ("UNRECOGNISED format - data present, not a known "
                            "embedded file type")
            msg = ("embedded object uses an unrecognised format; %d data "
                   "stream(s) present (%s) - content is not a standard "
                   "embedded file, any readable text is below"
                   % (len(substantive),
                      ", ".join(printable(s) for s in substantive[:4])))
            self.warnings.append("%s: %s" % (treepath, msg))
            self.log("      ! %s" % msg)
            for s in substantive:
                blob = get(s)
                if not blob:
                    continue
                sample = blob[:4]
                looks_text = sample[:1] == b"<" or sum(
                    1 for c in blob[:512] if 32 <= c < 127 or c in (9, 10, 13)
                ) > len(blob[:512]) * 0.9
                if looks_text:
                    sections.append(
                        ("Unrecognised stream: %s" % printable(s),
                         blob.decode("utf-8", "replace")[:200000]))

        msg_groups = {}
        if any("__substg1.0_" in s for s in stream_names):
            msg_groups = msg_fields_by_storage(ole)
            txt = msg_strings(ole)
            if txt:
                sections.append(("Outlook message fields", txt))

        sections.append(("OLE streams (%d)" % len(stream_names),
                         "\n".join("%-46s %10d" % (printable(s), ole.get_size(s))
                                   for s in stream_names)))
        tf = self.add_text(treepath, "ole", sections)
        self.node(treepath, name, data, "ole", saved_as=saved, text_file=tf,
                  progid=progid or None, streams=len(stream_names),
                  encrypted=encrypted, duplicate_of=dup, status=shell_status)

        # nested payloads
        for s in stream_names:
            base = s.rsplit("/", 1)[-1]
            blob = None
            child_name = None
            if base in ("\x01Ole10Native", "Ole10Native", "Package", "CONTENTS"):
                blob = get(s)
                fn, payload = ole10native(blob) if base != "CONTENTS" else (None, None)
                if payload:
                    blob, child_name = payload, fn
                elif base == "CONTENTS" and blob[:4] in (b"PK\x03\x04", b"%PDF"):
                    child_name = base + ".bin"
                else:
                    blob = None
            elif base.upper().startswith("__SUBSTG1.0_3701"):   # attachment data
                blob = get(s)
                fields = msg_groups.get(s.rsplit("/", 1)[0] if "/" in s else "", {})
                child_name = (fields.get("AttachFilename")
                              or fields.get("AttachShortName")
                              or "attachment.bin")
            if blob:
                self.counts["embedded_files"] += 1
                self.process(blob, child_name or base,
                             treepath + " > " + printable(s)
                             + (" (" + child_name + ")" if child_name else ""),
                             depth + 1)
        ole.close()

    def pdf_node(self, data, name, treepath, depth, dup):
        self.counts["containers"] += 1
        sections, attachments, warns = pdf_extract(data)
        for w in warns:
            self.warnings.append("%s: %s" % (treepath, w))
        tf = self.add_text(treepath, "pdf", sections)
        self.node(treepath, name, data, "pdf",
                  saved_as=self.save(treepath, data, depth),
                  text_file=tf, attachments=len(attachments), duplicate_of=dup,
                  warnings=warns or None)
        for aname, ablob in attachments:
            self.counts["embedded_files"] += 1
            self.process(ablob, aname, treepath + " > attachment:" + aname, depth + 1)

    def eml_node(self, data, name, treepath, depth, dup):
        import email
        from email import policy
        self.counts["containers"] += 1
        msg = email.message_from_bytes(data, policy=policy.default)
        head = "\n".join("%s: %s" % (k, v) for k, v in msg.items())
        bodies, atts = [], []
        for part in msg.walk():
            if part.is_multipart():
                continue
            fn = part.get_filename()
            ctype = part.get_content_type()
            try:
                payload = part.get_payload(decode=True)
            except Exception:
                payload = None
            if fn and payload:
                atts.append((fn, payload))
            elif ctype in ("text/plain", "text/html") and payload:
                bodies.append(("body (%s)" % ctype,
                               payload.decode(part.get_content_charset() or "utf-8",
                                              "replace")))
        tf = self.add_text(treepath, "eml", [("headers", head)] + bodies)
        self.node(treepath, name, data, "eml",
                  saved_as=self.save(treepath, data, depth), text_file=tf,
                  attachments=len(atts), duplicate_of=dup)
        for fn, payload in atts:
            self.counts["embedded_files"] += 1
            self.process(payload, fn, treepath + " > attachment:" + fn, depth + 1)

    # -- reporting --------------------------------------------------------
    # status -> (label, what it means, what to do about it)
    STATUS_ACTION = {
        "MISSING": ("the document names this file but does not contain it",
                    "ASK CLIENT - request the file itself"),
        "ENCRYPTED": ("protected; the payload is present but cannot be read",
                      "ASK CLIENT - unprotected copy, or open with your own rights"),
        "PARTIAL": ("recovered only as far as the container was written",
                    "ASK CLIENT - request a complete copy"),
        "EMPTY SHELL": ("an icon with no file behind it",
                        "ASK CLIENT - the attachment was never stored"),
        "UNRECOGNISED": ("a third-party format; readable text was extracted",
                         "no action - check the extracted text is enough"),
        "NO TEXT": ("no text could be read (scanned or image-only)",
                    "OCR needed, or ask the client for a text version"),
        "MAX DEPTH": ("saved but not opened - depth limit reached",
                      "re-run with a higher --max-depth"),
        "OK": ("recovered in full", ""),
    }

    def classify(self, rec):
        st = (rec.get("status") or "")
        if rec.get("encrypted"):
            return "ENCRYPTED"
        if st.startswith("EMPTY SHELL"):
            return "EMPTY SHELL"
        if st.startswith("UNRECOGNISED"):
            return "UNRECOGNISED"
        if st.startswith("PARTIAL"):
            return "PARTIAL"
        if st.startswith("max depth"):
            return "MAX DEPTH"
        if st.startswith("not recovered"):
            return "MISSING"
        return "OK"

    def write_summary(self, source, exit_code):
        """One table per source file, gaps first. Written before anything else
        is read, because a count is only a total when nothing is flagged."""
        rows = []
        for i, rec in enumerate(self.manifest):
            if rec["kind"] == "media":
                continue
            if rec["path"].count(" > ") == 0:
                continue                       # the source file itself
            rows.append({
                "n": len(rows) + 1,
                "name": self.display_name(rec["path"]),
                "kind": rec["kind"],
                "size": rec.get("size"),
                "state": self.classify(rec),
                "saved": rec.get("saved_as") or "",
                "path": rec["path"],
            })
        # embeddings the package names but does not hold are not nodes
        for rec in self.manifest:
            for tgt in (rec.get("missing_embeddings") or []):
                rows.append({"n": len(rows) + 1, "name": tgt.split("/")[-1],
                             "kind": "-", "size": None, "state": "MISSING",
                             "saved": "", "path": rec["path"] + " > " + tgt})

        gaps = [r for r in rows if r["state"] != "OK"]
        ask = [r for r in gaps if self.STATUS_ACTION[r["state"]][1].startswith("ASK")]

        buf = []
        w = buf.append
        w("# %s\n\n" % os.path.basename(source))
        w("Source: `%s`\n\n" % source)
        w("| | |\n|---|---|\n")
        w("| Items found inside | %d |\n" % len(rows))
        w("| Recovered in full | %d |\n" % (len(rows) - len(gaps)))
        w("| **Need the client** | **%d** |\n" % len(ask))
        w("| Other flags | %d |\n" % (len(gaps) - len(ask)))
        w("| Exit code | %d%s |\n\n" % (exit_code,
                                        " - finished with warnings"
                                        if exit_code == 2 else " - clean"))

        if ask:
            w("## Ask the client for these (%d)\n\n" % len(ask))
            w("| # | item | why | what to ask for |\n|---|---|---|---|\n")
            for r in ask:
                why, act = self.STATUS_ACTION[r["state"]]
                w("| %d | `%s` | %s | %s |\n"
                  % (r["n"], r["name"][:58], why, act.replace("ASK CLIENT - ", "")))
            w("\n")
        else:
            w("## Ask the client for these\n\nNothing - every item was "
              "recovered in full.\n\n")

        other = [r for r in gaps if r not in ask]
        if other:
            w("## Flagged, but no client action (%d)\n\n" % len(other))
            w("| # | item | state | note |\n|---|---|---|---|\n")
            for r in other:
                why, act = self.STATUS_ACTION[r["state"]]
                w("| %d | `%s` | %s | %s |\n"
                  % (r["n"], r["name"][:52], r["state"], act or why))
            w("\n")

        w("## Everything found inside the file\n\n")
        w("| # | item | type | size | state | saved as |\n")
        w("|---|---|---|---:|---|---|\n")
        for r in rows:
            w("| %d | `%s` | %s | %s | %s | %s |\n"
              % (r["n"], r["name"][:56], r["kind"],
                 "{:,}".format(r["size"]) if r["size"] else "-",
                 r["state"],
                 ("`%s`" % r["saved"].split("/")[-1]) if r["saved"] else "-"))
        w("\n> Containment (what sits inside what) is in `_TREE.txt`; full "
          "detail per item is in `_MANIFEST.json`.\n")
        return self._write("_SUMMARY.md", "".join(buf), "w", "utf-8")

    def write_reports(self, source):
        os.makedirs(self.outdir, exist_ok=True)

        with io.open(os.path.join(self.outdir, "_MANIFEST.json"), "w",
                     encoding="utf-8") as fh:
            json.dump({"source": source, "counts": self.counts,
                       "warnings": self.warnings, "nodes": self.manifest},
                      fh, indent=2, ensure_ascii=False)

        with io.open(os.path.join(self.outdir, "_TREE.txt"), "w",
                     encoding="utf-8") as fh:
            for rec in self.manifest:
                depth = rec["path"].count(" > ")
                label = rec["path"].split(" > ")[-1]
                size = "{:>13,}".format(rec["size"]) if rec["size"] is not None \
                    else "            -"
                # every condition that costs the reader content is annotated
                # here, so the tree alone shows where the gaps are
                extra = ""
                if rec.get("duplicate_of"):
                    extra = "  [dup of %s]" % rec["duplicate_of"].split(" > ")[-1]
                if rec.get("status"):
                    extra += "  [%s]" % rec["status"]
                if rec.get("encrypted"):
                    extra += "  [ENCRYPTED: %s]" % rec["encrypted"]
                if rec.get("missing_embeddings"):
                    extra += "  [%d declared embedding(s) ABSENT]" \
                        % len(rec["missing_embeddings"])
                if rec.get("partial_embeddings"):
                    extra += "  [%d partial]" % len(rec["partial_embeddings"])
                fh.write("%s%s %-9s %s%s\n" % ("  " * depth, size, rec["kind"],
                                               label, extra))

        total = 0
        truncated = False
        path = os.path.join(self.outdir, "_ALL_TEXT.md")
        with io.open(path, "w", encoding="utf-8") as fh:
            fh.write("# Deep extraction - %s\n\n" % os.path.basename(source))
            fh.write("Source: `%s`\n\n" % source)
            fh.write("Containers opened: %d | embedded files recovered: %d | "
                     "media: %d | text nodes: %d | **partially recovered: %d**\n\n"
                     % (self.counts["containers"], self.counts["embedded_files"],
                        self.counts["media"], self.counts["text_nodes"],
                        self.counts["partial"]))
            if self.partial_paths:
                fh.write("Recovered from a cut-off stream - leading content is "
                         "intact, the tail is gone:\n\n")
                for p in sorted(self.partial_paths):
                    fh.write("- `%s`\n" % p)
                fh.write("\n")
            if self.warnings:
                fh.write("## Warnings (%d)\n\n" % len(self.warnings))
                for w in self.warnings:
                    fh.write("- %s\n" % w)
                fh.write("\n")
            fh.write("---\n\n")
            for treepath, kind, sections in self.text_blocks:
                if self.max_text_bytes and total > self.max_text_bytes:
                    truncated = True
                    break
                block = ["\n\n# [%s] %s\n" % (kind, treepath)]
                for title, body in sections:
                    block.append("\n## %s\n\n%s\n" % (title, body))
                chunk = "".join(block)
                total += len(chunk)
                fh.write(chunk)
            if truncated:
                fh.write("\n\n> TRUNCATED at %d bytes by --max-text-mb; per-node "
                         "text is complete under text/.\n" % self.max_text_bytes)
        return path


def rtf_to_text(rtf):
    s = re.sub(r"\\'([0-9a-fA-F]{2})",
               lambda m: bytes([int(m.group(1), 16)]).decode("cp1252", "replace"), rtf)
    s = re.sub(r"\\par[d]?\b", "\n", s)
    s = re.sub(r"\\tab\b", "\t", s)
    s = re.sub(r"\{\\\*.*?\}", "", s, flags=re.S)
    s = re.sub(r"\\[a-zA-Z]+-?\d* ?", "", s)
    s = s.replace("{", "").replace("}", "")
    return re.sub(r"\n{3,}", "\n\n", s).strip()


def printable_strings(data, minlen=6, limit=4000):
    out = []
    for m in re.finditer(rb"[ -~]{%d,}" % minlen, data[:8 * 1024 * 1024]):
        out.append(m.group(0).decode("latin-1"))
        if len(out) >= limit:
            out.append("... (string extraction capped at %d runs)" % limit)
            break
    for m in re.finditer(rb"(?:[ -~]\x00){%d,}" % minlen, data[:8 * 1024 * 1024]):
        out.append(m.group(0).decode("utf-16-le", "replace"))
        if len(out) >= limit * 2:
            break
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("-o", "--outdir", default=None)
    ap.add_argument("--max-depth", type=int, default=8)
    ap.add_argument("--no-media", action="store_true",
                    help="catalogue images but do not write them to disk")
    ap.add_argument("--max-text-mb", type=float, default=0,
                    help="cap _ALL_TEXT.md size (0 = no cap); per-node text "
                         "under text/ is always complete")
    ap.add_argument("--nested", action="store_true",
                    help="mirror the containment tree under files/ instead of "
                         "the flat recovered/ folder; produces paths that often "
                         "exceed the Windows 260-character limit")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    src = os.path.abspath(args.input)
    if not os.path.isfile(long_path(src)):
        print("ERROR: not a file: %s" % src, file=sys.stderr)
        return 1
    outdir = os.path.abspath(args.outdir or (os.path.splitext(src)[0] + "_extracted"))
    stale = os.path.exists(os.path.join(outdir, "_MANIFEST.json"))
    os.makedirs(outdir, exist_ok=True)

    with open(long_path(src), "rb") as fh:
        data = fh.read()

    ex = Extractor(outdir, args.max_depth, not args.no_media,
                   args.max_text_mb, args.quiet, args.nested)
    if stale:
        ex.warnings.append(
            "output directory already held a previous extraction - files/ and "
            "text/ may contain stale entries from that run. _MANIFEST.json and "
            "_TREE.txt describe THIS run only; use an empty directory for a "
            "clean tree.")
    ex.log("reading %s (%s bytes)" % (src, "{:,}".format(len(data))))
    ex.process(data, os.path.basename(src), os.path.basename(src), 0)
    all_text = ex.write_reports(src)
    code = 2 if ex.warnings else 0
    summary = ex.write_summary(src, code)

    ask = sum(1 for rec in ex.manifest
              if ex.classify(rec) in ("ENCRYPTED", "EMPTY SHELL", "PARTIAL"))
    ask += sum(len(rec.get("missing_embeddings") or []) for rec in ex.manifest)

    print("\n" + "=" * 72)
    print("OUTPUT DIR   %s" % outdir)
    print("  _SUMMARY.md    READ THIS FIRST - one row per item, gaps first")
    print("  _ALL_TEXT.md   %s bytes  consolidated text, whole tree"
          % "{:,}".format(os.path.getsize(all_text)))
    print("  _TREE.txt      containment structure")
    print("  _MANIFEST.json %d nodes" % len(ex.manifest))
    print("  %-14s recovered files, openable directly"
          % ("files/" if ex.nested else "recovered/"))
    print("  text/          per-node text")
    print("containers=%d embedded_files=%d media=%d text_nodes=%d partial=%d"
          % (ex.counts["containers"], ex.counts["embedded_files"],
             ex.counts["media"], ex.counts["text_nodes"], ex.counts["partial"]))
    if ask:
        print("ITEMS NEEDING THE CLIENT: %d  (listed at the top of %s)"
              % (ask, os.path.basename(summary)))
    if ex.warnings:
        print("WARNINGS (%d):" % len(ex.warnings))
        for w in ex.warnings[:25]:
            print("  - %s" % w)
        if len(ex.warnings) > 25:
            print("  ... %d more in _MANIFEST.json" % (len(ex.warnings) - 25))
    return code


if __name__ == "__main__":
    sys.exit(main())
