#!/usr/bin/env python3
"""Tagr — Audio Metadata Editor (PyQt6)"""

import sys, os, io, json, threading, subprocess, urllib.request, urllib.parse
from pathlib import Path
from PIL import Image as PILImage
from mutagen.id3 import ID3, TIT2, TPE1, TALB, APIC, TDRC, TCON, TBPM, ID3NoHeaderError
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QLineEdit, QScrollArea, QFrame, QFileDialog,
    QDialog, QGridLayout, QSizePolicy, QComboBox, QSlider, QRubberBand
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QUrl, QSize, QRect, QPoint
from PyQt6.QtGui  import (QPixmap, QImage, QPainter, QColor, QPen, QBrush,
                           QKeySequence, QShortcut, QPainterPath)

# ── Config ────────────────────────────────────────────────────────────────────
CONFIG_PATH = Path.home() / ".tagr_config.json"

def load_config():
    try: return json.loads(CONFIG_PATH.read_text())
    except: return {}

def save_config(d):
    try: CONFIG_PATH.write_text(json.dumps(d))
    except: pass

# ── Couleurs ──────────────────────────────────────────────────────────────────
# ── Palettes ─────────────────────────────────────────────
DARK_PALETTE = dict(
    BG="#0f0f0f", BG2="#161616", PANEL="#1e1e1e", PANEL2="#272727",
    BORDER="#303030", ACCENT="#1DB954", ACCENT2="#17a349",
    TEXT="#efefef", TEXTM="#aaaaaa", TEXTD="#606060",
    ERROR="#e05252", WARN="#e8a538", FIELDBG="#141414", SELBG="#192b1d"
)
LIGHT_PALETTE = dict(
    BG="#f5f5f5", BG2="#ebebeb", PANEL="#ffffff", PANEL2="#e0e0e0",
    BORDER="#cccccc", ACCENT="#1DB954", ACCENT2="#17a349",
    TEXT="#111111", TEXTM="#555555", TEXTD="#999999",
    ERROR="#d63031", WARN="#e17055", FIELDBG="#f9f9f9", SELBG="#d4f5e0"
)

def _apply_palette(p):
    global BG,BG2,PANEL,PANEL2,BORDER,ACCENT,ACCENT2,TEXT,TEXTM,TEXTD,ERROR,WARN,FIELDBG,SELBG
    BG=p["BG"]; BG2=p["BG2"]; PANEL=p["PANEL"]; PANEL2=p["PANEL2"]
    BORDER=p["BORDER"]; ACCENT=p["ACCENT"]; ACCENT2=p["ACCENT2"]
    TEXT=p["TEXT"]; TEXTM=p["TEXTM"]; TEXTD=p["TEXTD"]
    ERROR=p["ERROR"]; WARN=p["WARN"]; FIELDBG=p["FIELDBG"]; SELBG=p["SELBG"]

_apply_palette(DARK_PALETTE)

BG      = BG
BG2     = BG2
PANEL   = PANEL
PANEL2  = PANEL2
BORDER  = BORDER
ACCENT  = ACCENT
ACCENT2 = ACCENT2
TEXT    = TEXT
TEXTM   = TEXTM
TEXTD   = TEXTD
ERROR   = ERROR
WARN    = WARN
FIELDBG = FIELDBG
SELBG   = SELBG

def is_audio(p): return p.lower().endswith((".mp3",".flac",".m4a",".aac"))
def is_image(p): return p.lower().endswith((".jpg",".jpeg",".png",".webp",".bmp"))
def safe_fn(s):
    for c in r'/\:*?"<>|': s=s.replace(c,"")
    return s.strip()

def pil_to_qpixmap(img, size):
    img=img.copy(); img.thumbnail((size,size),PILImage.LANCZOS)
    bg=PILImage.new("RGB",(size,size),(30,30,30))
    bg.paste(img,((size-img.width)//2,(size-img.height)//2))
    data=bg.tobytes("raw","RGB")
    qi=QImage(data,size,size,size*3,QImage.Format.Format_RGB888)
    return QPixmap.fromImage(qi)

def pil_to_qpixmap_exact(img, w, h):
    img=img.copy().convert("RGB"); img=img.resize((w,h),PILImage.LANCZOS)
    data=img.tobytes("raw","RGB")
    qi=QImage(data,w,h,w*3,QImage.Format.Format_RGB888)
    return QPixmap.fromImage(qi)

# ── Tags I/O ──────────────────────────────────────────────────────────────────

def read_tags(path):
    info={"title":"","artist":"","album":"","year":"","genre":"","bpm":"","track":"","cover":None}
    ext=path.lower().rsplit(".",1)[-1]
    try:
        if ext=="mp3":
            try: t=ID3(path)
            except ID3NoHeaderError: t=ID3()
            info["title"] =str(t.get("TIT2","")).strip()
            info["artist"]=str(t.get("TPE1","")).strip()
            info["album"] =str(t.get("TALB","")).strip()
            info["year"]  =str(t.get("TDRC","")).strip()
            info["genre"] =str(t.get("TCON","")).strip()
            info["bpm"]   =str(t.get("TBPM","")).strip()
            info["track"] =str(t.get("TRCK","")).strip()
            for k in t:
                if k.startswith("APIC"):
                    info["cover"]=PILImage.open(io.BytesIO(t[k].data)).convert("RGB"); break
        elif ext=="flac":
            a=FLAC(path)
            info["title"] =(a.get("title", [""])[0]).strip()
            info["artist"]=(a.get("artist",[""])[0]).strip()
            info["album"] =(a.get("album", [""])[0]).strip()
            info["year"]  =(a.get("date",  [""])[0]).strip()
            info["genre"] =(a.get("genre", [""])[0]).strip()
            info["bpm"]   =(a.get("bpm",   [""])[0]).strip()
            info["track"] =(a.get("tracknumber",[""])[0]).strip() if a.get("tracknumber") else ""
            if a.pictures: info["cover"]=PILImage.open(io.BytesIO(a.pictures[0].data)).convert("RGB")
        elif ext in("m4a","aac"):
            a=MP4(path)
            info["title"] =(a.get("\xa9nam",[""])[0]).strip()
            info["artist"]=(a.get("\xa9ART",[""])[0]).strip()
            info["album"] =(a.get("\xa9alb",[""])[0]).strip()
            info["year"]  =(a.get("\xa9day",[""])[0]).strip()
            info["genre"] =(a.get("\xa9gen",[""])[0]).strip()
            tmpo=a.get("tmpo"); info["bpm"]=str(tmpo[0]).strip() if tmpo else ""
            trkn=a.get("trkn"); info["track"]=f'{trkn[0][0]}/{trkn[0][1]}' if trkn and trkn[0][1] else (str(trkn[0][0]) if trkn else "")
            c=a.get("covr")
            if c: info["cover"]=PILImage.open(io.BytesIO(bytes(c[0]))).convert("RGB")
    except Exception as e: print(f"read_tags: {e}")
    if not info["title"]: info["title"]=os.path.splitext(os.path.basename(path))[0]
    return info

def write_tags(path,title,artist,album,year,genre,bpm,track="",cover=None):
    ext=path.lower().rsplit(".",1)[-1]
    try:
        if ext=="mp3":
            try: t=ID3(path)
            except ID3NoHeaderError: t=ID3()
            t["TIT2"]=TIT2(encoding=3,text=title)
            t["TPE1"]=TPE1(encoding=3,text=artist)
            t["TALB"]=TALB(encoding=3,text=album)
            if year:  t["TDRC"]=TDRC(encoding=3,text=year)
            if genre: t["TCON"]=TCON(encoding=3,text=genre)
            if bpm:   t["TBPM"]=TBPM(encoding=3,text=bpm)
            if track:
                from mutagen.id3 import TRCK
                t["TRCK"]=TRCK(encoding=3,text=track)
            if cover:
                buf=io.BytesIO(); cover.save(buf,"JPEG",quality=90)
                t["APIC"]=APIC(encoding=3,mime="image/jpeg",type=3,desc="Cover",data=buf.getvalue())
            t.save(path)
        elif ext=="flac":
            a=FLAC(path)
            a["title"]=title; a["artist"]=artist; a["album"]=album
            if year:  a["date"]=year
            if genre: a["genre"]=genre
            if bpm:   a["bpm"]=bpm
            if track: a["tracknumber"]=track
            if cover:
                from mutagen.flac import Picture
                p=Picture(); buf=io.BytesIO(); cover.save(buf,"JPEG",quality=90)
                p.data=buf.getvalue(); p.type=3; p.mime="image/jpeg"
                p.width,p.height=cover.size; p.depth=24
                a.clear_pictures(); a.add_picture(p)
            a.save()
        elif ext in("m4a","aac"):
            a=MP4(path)
            a["\xa9nam"]=title; a["\xa9ART"]=artist; a["\xa9alb"]=album
            if year:  a["\xa9day"]=year
            if genre: a["\xa9gen"]=genre
            if bpm:
                try: a["tmpo"]=[int(bpm)]
                except: pass
            if track:
                try:
                    parts=track.split("/")
                    tot=int(parts[1]) if len(parts)>1 else 0
                    a["trkn"]=[(int(parts[0]),tot)]
                except: pass
            if cover:
                from mutagen.mp4 import MP4Cover
                buf=io.BytesIO(); cover.save(buf,"JPEG",quality=90)
                a["covr"]=[MP4Cover(buf.getvalue(),imageformat=MP4Cover.FORMAT_JPEG)]
            a.save()
        return True
    except Exception as e: return str(e)


# ── Qualité audio ─────────────────────────────────────────────────────────────

def read_audio_quality(path):
    """Retourne un dict avec les infos de qualité audio du fichier."""
    info = {"bitrate": None, "sample_rate": None, "bits": None,
            "channels": None, "duration": None, "size": None}
    try:
        info["size"] = os.path.getsize(path)
        ext = path.lower().rsplit(".", 1)[-1]
        if ext == "mp3":
            from mutagen.mp3 import MP3
            a = MP3(path)
            info["bitrate"]     = int(a.info.bitrate / 1000)
            info["sample_rate"] = a.info.sample_rate
            info["channels"]    = a.info.channels
            info["duration"]    = a.info.length
            info["bits"]        = None  # MP3 = lossy, pas de bit depth
        elif ext == "flac":
            a = FLAC(path)
            info["bitrate"]     = int(a.info.bits_per_sample * a.info.sample_rate * a.info.channels / 1000)
            info["sample_rate"] = a.info.sample_rate
            info["bits"]        = a.info.bits_per_sample
            info["channels"]    = a.info.channels
            info["duration"]    = a.info.length
        elif ext in ("m4a", "aac"):
            a = MP4(path)
            info["bitrate"]     = int(a.info.bitrate / 1000) if a.info.bitrate else None
            info["sample_rate"] = a.info.sample_rate
            info["channels"]    = a.info.channels
            info["duration"]    = a.info.length
            info["bits"]        = None
        elif ext == "ogg":
            from mutagen.oggvorbis import OggVorbis
            a = OggVorbis(path)
            info["bitrate"]     = int(a.info.bitrate / 1000) if a.info.bitrate else None
            info["sample_rate"] = a.info.sample_rate
            info["channels"]    = a.info.channels
            info["duration"]    = a.info.length
            info["bits"]        = None
    except Exception as e:
        print(f"read_audio_quality: {e}")
    return info

def quality_label(path, q):
    """Retourne (label, couleur) selon la qualité."""
    ext = path.lower().rsplit(".", 1)[-1]
    if ext == "flac":
        bits = q.get("bits") or 16
        sr   = q.get("sample_rate") or 44100
        if bits >= 24 or sr > 48000:
            return "Hi-Res Lossless", "#a78bfa"   # violet
        return "Lossless (CD)", "#1DB954"          # vert
    br = q.get("bitrate") or 0
    if br >= 256:  return "Haute qualité",    "#1DB954"   # vert
    if br >= 192:  return "Bonne qualité",    "#86efac"   # vert clair
    if br >= 128:  return "Qualité standard", "#e8a538"   # orange
    return "Basse qualité", "#e05252"                     # rouge

# ── Recherche ─────────────────────────────────────────────────────────────────

def fetch_image_url(url):
    try: return PILImage.open(io.BytesIO(urllib.request.urlopen(url,timeout=8).read())).convert("RGB")
    except: return None

def search_itunes(q, n=4):
    try:
        p = urllib.parse.urlencode({"term":q,"entity":"song","limit":n,"media":"music"})
        d = json.loads(urllib.request.urlopen(
            f"https://itunes.apple.com/search?{p}", timeout=5).read())
        return [{"title":   r.get("trackName",""),
                 "artist":  r.get("artistName",""),
                 "album":   r.get("collectionName",""),
                 "artwork": r.get("artworkUrl100","").replace("100x100","600x600"),
                 "source":  "iTunes"}
                for r in d.get("results",[]) if r.get("artworkUrl100")]
    except: return []


def search_itunes_artist(q, n=4):
    """Cherche par NOM D'ARTISTE sur iTunes — retourne les images d'artiste."""
    try:
        p = urllib.parse.urlencode({"term":q,"entity":"musicArtist","limit":n})
        d = json.loads(urllib.request.urlopen(
            f"https://itunes.apple.com/search?{p}", timeout=5).read())
        results = []
        for r in d.get("results",[]):
            art = r.get("artworkUrl100","").replace("100x100","600x600")
            if art:
                results.append({
                    "title":   r.get("artistName",""),
                    "artist":  r.get("artistName",""),
                    "album":   "Image artiste",
                    "artwork": art,
                    "source":  "iTunes"
                })
        return results
    except: return []

def search_deezer(q, n=4):
    try:
        p = urllib.parse.urlencode({"q":q,"limit":n})
        d = json.loads(urllib.request.urlopen(
            f"https://api.deezer.com/search?{p}", timeout=5).read())
        return [{"title":   r.get("title",""),
                 "artist":  r.get("artist",{}).get("name",""),
                 "album":   r.get("album",{}).get("title",""),
                 "artwork":  r.get("album",{}).get("cover_xl") or
                             r.get("album",{}).get("cover_big",""),
                 "source":  "Deezer"}
                for r in d.get("data",[])
                if r.get("album",{}).get("cover_xl") or r.get("album",{}).get("cover_big")]
    except: return []


def search_deezer_artist(q, n=4):
    """Cherche par NOM D'ARTISTE sur Deezer — retourne les photos d'artiste."""
    try:
        p = urllib.parse.urlencode({"q":q,"limit":n})
        d = json.loads(urllib.request.urlopen(
            f"https://api.deezer.com/search/artist?{p}", timeout=5).read())
        results = []
        for r in d.get("data",[]):
            pic = r.get("picture_xl") or r.get("picture_big","")
            if pic and "default" not in pic:
                results.append({
                    "title":   r.get("name",""),
                    "artist":  r.get("name",""),
                    "album":   "Photo artiste",
                    "artwork": pic,
                    "source":  "Deezer"
                })
        return results
    except: return []

def search_musicbrainz(q, n=4):
    try:
        headers = {"User-Agent": "Tagr/3.0 (audio-metadata-editor)"}
        p = urllib.parse.urlencode({"query": q, "limit": n, "fmt": "json"})
        req = urllib.request.Request(
            f"https://musicbrainz.org/ws/2/recording/?{p}", headers=headers)
        d = json.loads(urllib.request.urlopen(req, timeout=8).read())
        results = []
        for r in d.get("recordings", []):
            releases = r.get("releases", [])
            if not releases: continue
            rel = releases[0]
            rid = rel.get("id", "")
            artist = ""
            if r.get("artist-credit"):
                artist = r["artist-credit"][0].get("artist", {}).get("name", "")
            results.append({
                "title":   r.get("title", ""),
                "artist":  artist,
                "album":   rel.get("title", ""),
                "artwork": f"https://coverartarchive.org/release/{rid}/front-500" if rid else "",
                "source":  "MusicBrainz"
            })
        return [r for r in results if r["artwork"]]
    except:
        return []


def multi_search(query, n=9):
    """Recherche avec priorité ARTISTE.
    Si un terme artiste est fourni, cherche d'abord par artiste
    puis complète avec les morceaux."""
    results = []
    threads = [
        threading.Thread(target=lambda: results.extend(search_deezer_artist(query, 4)), daemon=True),
        threading.Thread(target=lambda: results.extend(search_itunes_artist(query, 3)), daemon=True),
        threading.Thread(target=lambda: results.extend(search_deezer(query, 3)), daemon=True),
        threading.Thread(target=lambda: results.extend(search_musicbrainz(query, 3)), daemon=True),
    ]
    for t in threads: t.start()
    for t in threads: t.join(8)
    # Dédoublonnage par artwork URL (pas par titre — les images artiste ont des URLs uniques)
    seen_urls = set(); out = []
    for r in results:
        url = r.get("artwork","")
        if url and url not in seen_urls:
            seen_urls.add(url); out.append(r)
    return out[:n]

# ── Crop dialog ───────────────────────────────────────────────────────────────

class CropDialog(QDialog):
    cropped=pyqtSignal(object)

    def __init__(self, parent, img):
        super().__init__(parent)
        self.setWindowTitle("Recadrer la pochette")
        self.setModal(True); self.setStyleSheet(f"background:{BG2};color:{TEXT};")
        self.orig=img; self._zoom=1.0; self._offset=[0,0]
        self._drag_start=None; self._preview_size=400
        self._build()
        self._render()

    def _build(self):
        v=QVBoxLayout(self); v.setContentsMargins(20,20,20,20); v.setSpacing(12)
        tk=QLabel("Recadrer la pochette"); tk.setStyleSheet(f"font-size:14px;font-weight:bold;")
        v.addWidget(tk)

        sub=QLabel("Scroll pour zoomer · Glisser pour déplacer")
        sub.setStyleSheet(f"font-size:9px;color:{TEXTD};"); v.addWidget(sub)

        self.canvas=QLabel(); self.canvas.setFixedSize(self._preview_size,self._preview_size)
        self.canvas.setStyleSheet(f"background:#000;border-radius:6px;")
        self.canvas.setCursor(Qt.CursorShape.OpenHandCursor)
        v.addWidget(self.canvas,alignment=Qt.AlignmentFlag.AlignCenter)

        # Zoom slider
        zrow=QHBoxLayout()
        QLabel("Zoom").setParent(None)
        zl=QLabel("Zoom"); zl.setStyleSheet(f"color:{TEXTD};font-size:9px;")
        self.zoom_slider=QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(10,400); self.zoom_slider.setValue(100)
        self.zoom_slider.setStyleSheet(f"QSlider::groove:horizontal{{background:{BORDER};height:4px;border-radius:2px;}}"
                                        f"QSlider::handle:horizontal{{background:{ACCENT};width:14px;height:14px;border-radius:7px;margin:-5px 0;}}"
                                        f"QSlider::sub-page:horizontal{{background:{ACCENT};height:4px;border-radius:2px;}}")
        self.zoom_slider.valueChanged.connect(lambda v:(setattr(self,'_zoom',v/100),self._render()))
        zrow.addWidget(zl); zrow.addWidget(self.zoom_slider)
        v.addLayout(zrow)

        brow=QHBoxLayout(); brow.setSpacing(10)
        ok=QPushButton("Appliquer")
        ok.setStyleSheet(f"background:{ACCENT};color:#000;font-weight:bold;border:none;padding:9px 20px;border-radius:4px;")
        ok.setCursor(Qt.CursorShape.PointingHandCursor); ok.clicked.connect(self._apply)
        cancel=QPushButton("Annuler")
        cancel.setStyleSheet(f"background:{PANEL};color:{TEXTM};border:none;padding:9px 20px;border-radius:4px;")
        cancel.setCursor(Qt.CursorShape.PointingHandCursor); cancel.clicked.connect(self.reject)
        brow.addStretch(); brow.addWidget(ok); brow.addWidget(cancel)
        v.addLayout(brow)

    def _render(self):
        S=self._preview_size; img=self.orig.copy()
        z=self._zoom
        new_w=max(1,int(img.width*z)); new_h=max(1,int(img.height*z))
        img=img.resize((new_w,new_h),PILImage.LANCZOS)
        ox=int(self._offset[0]); oy=int(self._offset[1])
        # Centre dans canvas carré
        canvas=PILImage.new("RGB",(S,S),(0,0,0))
        px=S//2-new_w//2+ox; py=S//2-new_h//2+oy
        canvas.paste(img,(px,py))
        # Crop central
        self._current_canvas=canvas
        px2=pil_to_qpixmap_exact(canvas,S,S)
        # Overlay : cercle de crop
        painter=QPainter(px2)
        painter.setPen(QPen(QColor(255,255,255,80),1))
        painter.drawEllipse(0,0,S-1,S-1)
        painter.end()
        self.canvas.setPixmap(px2)

    def mousePressEvent(self,e):
        if e.button()==Qt.MouseButton.LeftButton:
            self._drag_start=e.globalPosition().toPoint()
            self.canvas.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self,e):
        if self._drag_start:
            d=e.globalPosition().toPoint()-self._drag_start
            self._drag_start=e.globalPosition().toPoint()
            self._offset[0]+=d.x(); self._offset[1]+=d.y()
            self._render()

    def mouseReleaseEvent(self,e):
        self._drag_start=None
        self.canvas.setCursor(Qt.CursorShape.OpenHandCursor)

    def wheelEvent(self,e):
        delta=e.angleDelta().y()/120
        self._zoom=max(0.1,min(4.0,self._zoom+delta*0.1))
        self.zoom_slider.setValue(int(self._zoom*100))
        self._render()

    def _apply(self):
        S=self._preview_size
        result=self._current_canvas.crop((0,0,S,S))
        self.cropped.emit(result); self.accept()

# ── Workers ───────────────────────────────────────────────────────────────────

class TagLoader(QThread):
    done=pyqtSignal(str,dict)
    def __init__(self,p): super().__init__(); self.p=p
    def run(self): self.done.emit(self.p,read_tags(self.p))

class Searcher(QThread):
    done=pyqtSignal(list)
    def __init__(self,q): super().__init__(); self.q=q
    def run(self): self.done.emit(multi_search(self.q))

class ImageFetcher(QThread):
    done=pyqtSignal(object,dict)
    def __init__(self,url,meta): super().__init__(); self.url=url; self.meta=meta
    def run(self):
        img=fetch_image_url(self.url)
        if img: self.done.emit(img,self.meta)

# ── Cover label (avec drag & drop image) ─────────────────────────────────────

class CoverLabel(QLabel):
    clicked=pyqtSignal()
    image_dropped=pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.setFixedSize(160,160)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setAcceptDrops(True)
        self._reset()

    def _reset(self):
        self.setPixmap(QPixmap())
        self.setScaledContents(False)
        self.setText("Ajouter\nune pochette")
        self.setStyleSheet(f"background:{PANEL};border-radius:6px;color:{TEXTD};"
                           f"font-size:13px;border:2px dashed {BORDER};")

    def set_image(self,img):
        px=pil_to_qpixmap(img,160)
        self.setPixmap(px); self.setScaledContents(True); self.setText("")
        self.setStyleSheet(f"background:{PANEL};border-radius:6px;border:none;")

    def mousePressEvent(self,e): self.clicked.emit()

    def dragEnterEvent(self,e):
        if e.mimeData().hasUrls():
            urls=[u.toLocalFile() for u in e.mimeData().urls()]
            if any(is_image(u) for u in urls):
                e.acceptProposedAction()
                self.setStyleSheet(f"background:{SELBG};border-radius:6px;color:{ACCENT};"
                                   f"font-size:11px;border:2px solid {ACCENT};")
                self.setText("Déposer ici")

    def dragLeaveEvent(self,e):
        if self.pixmap() and not self.pixmap().isNull():
            self.setStyleSheet(f"background:{PANEL};border-radius:6px;border:none;")
        else: self._reset()

    def dropEvent(self,e):
        for url in e.mimeData().urls():
            p=url.toLocalFile()
            if is_image(p):
                try:
                    img=PILImage.open(p).convert("RGB")
                    self.image_dropped.emit(img); break
                except: pass
        e.acceptProposedAction()

# ── FileRow ───────────────────────────────────────────────────────────────────

class FileRow(QFrame):
    selected_signal=pyqtSignal(object)
    delete_signal=pyqtSignal(object)

    def __init__(self,path):
        super().__init__()
        self.path=path; self._selected=False; self._dirty=False
        self.setFixedHeight(60); self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._build(); self._style(False)

    def _build(self):
        lay=QHBoxLayout(self); lay.setContentsMargins(10,8,10,8); lay.setSpacing(10)
        self.thumb=QLabel(); self.thumb.setFixedSize(44,44)
        self.thumb.setStyleSheet(f"background:{PANEL2};border-radius:4px;")
        lay.addWidget(self.thumb)
        mid=QVBoxLayout(); mid.setSpacing(2)
        self.lbl_t=QLabel(os.path.basename(self.path))
        self.lbl_t.setStyleSheet(f"color:{TEXT};font-size:12px;font-weight:bold;background:transparent;")
        self.lbl_a=QLabel("—")
        self.lbl_a.setStyleSheet(f"color:{TEXTM};font-size:10px;background:transparent;")
        mid.addWidget(self.lbl_t); mid.addWidget(self.lbl_a); lay.addLayout(mid,1)
        right=QVBoxLayout(); right.setSpacing(2); right.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.dot=QLabel("●"); self.dot.setStyleSheet("color:transparent;font-size:7px;background:transparent;")
        self.dot.setAlignment(Qt.AlignmentFlag.AlignRight)
        ext=os.path.splitext(self.path)[1].lstrip(".").upper()
        badge=QLabel(ext); badge.setStyleSheet(f"color:{TEXTD};font-size:8px;font-family:'Courier New';"
                                                f"background:{PANEL2};padding:2px 5px;border-radius:3px;")
        right.addWidget(self.dot); right.addWidget(badge); lay.addLayout(right)

    def set_display(self,title,artist,cover=None):
        self.lbl_t.setText(title or os.path.basename(self.path))
        self.lbl_a.setText(artist or "Artiste inconnu")
        if cover:
            px=pil_to_qpixmap(cover,44); self.thumb.setPixmap(px); self.thumb.setScaledContents(True)

    def set_dirty(self,val):
        self._dirty=val
        self.dot.setStyleSheet(f"color:{WARN if val else 'transparent'};font-size:7px;background:transparent;")

    def set_selected(self,val):
        self._selected=val; self._style(val)

    def _style(self,sel):
        bg=SELBG if sel else PANEL
        bl=f"border-left:2px solid {ACCENT};" if sel else "border-left:2px solid transparent;"
        self.setStyleSheet(f"FileRow{{background:{bg};{bl}}}")

    def mousePressEvent(self,e):
        if e.button()==Qt.MouseButton.LeftButton: self.selected_signal.emit(self)
        elif e.button()==Qt.MouseButton.RightButton: self._ctx(e)

    def _ctx(self,e):
        from PyQt6.QtWidgets import QMenu
        m=QMenu(self)
        m.setStyleSheet(f"QMenu{{background:{PANEL2};color:{TEXT};border:1px solid {BORDER};padding:4px;}}"
                        f"QMenu::item{{padding:6px 16px;}}"
                        f"QMenu::item:selected{{background:{ERROR};color:{TEXT};}}")
        m.addAction("Retirer de la liste",lambda:self.delete_signal.emit(self))
        m.exec(e.globalPosition().toPoint())

# ── Cover picker ──────────────────────────────────────────────────────────────

class CoverPicker(QDialog):
    chosen = pyqtSignal(object, dict)

    def __init__(self, parent, results):
        super().__init__(parent)
        self.setWindowTitle("Recherche de pochette")
        self.setStyleSheet(f"background:{BG2};color:{TEXT};")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.results = results
        self.fetchers = []
        self._count = 0
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setSpacing(10); lay.setContentsMargins(20, 18, 20, 18)

        # Titre
        title = QLabel("Recherche de pochette")
        title.setStyleSheet(f"font-size:15px;font-weight:bold;color:{TEXT};")
        lay.addWidget(title)

        # Sources
        src_lbl = QLabel("Sources : Deezer · iTunes · MusicBrainz · Priorité artiste")
        src_lbl.setStyleSheet(f"font-size:9px;color:{TEXTD};")
        lay.addWidget(src_lbl)

        # Champ URL directe
        url_row = QHBoxLayout(); url_row.setSpacing(8)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Coller une URL d'image directement (https://...)")
        self.url_input.setStyleSheet(
            f"background:{FIELDBG};color:{TEXT};border:1px solid {BORDER};"
            f"border-radius:4px;padding:7px 10px;font-size:11px;")
        url_btn = QPushButton("Utiliser")
        url_btn.setStyleSheet(
            f"background:{ACCENT};color:#000;font-weight:bold;border:none;"
            f"padding:7px 14px;border-radius:4px;font-size:11px;")
        url_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        url_btn.clicked.connect(self._use_url)
        url_row.addWidget(self.url_input, 1)
        url_row.addWidget(url_btn)
        lay.addLayout(url_row)

        hint = QLabel("Astuce : clic droit sur une image dans Chrome → Copier l'adresse de l'image")
        hint.setStyleSheet(f"font-size:8px;color:{TEXTD};")
        lay.addWidget(hint)

        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color:{BORDER};"); lay.addWidget(sep)

        # Grille résultats
        results_lbl = QLabel("Résultats automatiques :")
        results_lbl.setStyleSheet(f"font-size:10px;color:{TEXTM};")
        lay.addWidget(results_lbl)

        self.grid = QGridLayout(); self.grid.setSpacing(8)
        lay.addLayout(self.grid)

        self.no_results_lbl = QLabel("Chargement des résultats...")
        self.no_results_lbl.setStyleSheet(f"color:{TEXTD};font-size:10px;")
        self.no_results_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.no_results_lbl)

        cancel = QPushButton("Fermer")
        cancel.setStyleSheet(
            f"background:{PANEL};color:{TEXTM};border:none;"
            f"padding:8px 20px;font-size:11px;border-radius:4px;")
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel.clicked.connect(self.reject)
        lay.addWidget(cancel, alignment=Qt.AlignmentFlag.AlignCenter)

        # Charger les images
        if self.results:
            self.no_results_lbl.hide()
            for r in self.results[:9]:
                if r.get("artwork"):
                    f = ImageFetcher(r["artwork"], r)
                    f.done.connect(self._add)
                    f.start(); self.fetchers.append(f)
        else:
            self.no_results_lbl.setText(
                "Aucun résultat trouvé automatiquement.\n"
                "Colle une URL d'image ci-dessus.")

    def _use_url(self):
        url = self.url_input.text().strip()
        if not url: return
        self.no_results_lbl.setText("Chargement de l'image...")
        self.no_results_lbl.show()
        f = ImageFetcher(url, {"title": "", "artist": "", "album": "",
                                "source": "URL directe"})
        f.done.connect(lambda img, meta: (self.chosen.emit(img, meta), self.accept()))
        f.done.connect(lambda img, meta: None)
        f.start(); self.fetchers.append(f)

    def _add(self, img, meta):
        i = self._count; self._count += 1
        row, col = i // 3, i % 3

        fr = QFrame()
        fr.setStyleSheet(f"background:{PANEL};border-radius:6px;")
        fr.setCursor(Qt.CursorShape.PointingHandCursor)
        v = QVBoxLayout(fr); v.setContentsMargins(5, 5, 5, 5); v.setSpacing(2)

        px = pil_to_qpixmap(img, 120)
        lbl = QLabel(); lbl.setPixmap(px)
        lbl.setScaledContents(True); lbl.setFixedSize(120, 120)

        title_lbl = QLabel((meta.get("title") or "")[:20])
        title_lbl.setStyleSheet(
            f"color:{TEXT};font-size:8px;font-weight:bold;background:transparent;")

        artist_lbl = QLabel((meta.get("artist") or "")[:20])
        artist_lbl.setStyleSheet(f"color:{TEXTM};font-size:7px;background:transparent;")

        src = meta.get("source", "")
        src_colors = {"iTunes": ACCENT, "Deezer": "#0064ff",
                      "MusicBrainz": "#ba8f00"}
        src_lbl = QLabel(src)
        src_lbl.setStyleSheet(
            f"color:{src_colors.get(src, TEXTD)};font-size:7px;background:transparent;")

        for w in [lbl, title_lbl, artist_lbl, src_lbl]:
            v.addWidget(w, alignment=Qt.AlignmentFlag.AlignCenter)

        def click(checked=False, img=img, meta=meta):
            self.chosen.emit(img, meta); self.accept()
        fr.mousePressEvent = lambda e, fn=click: fn()
        lbl.mousePressEvent = lambda e, fn=click: fn()

        self.grid.addWidget(fr, row, col)

# ── Panel empilé ──────────────────────────────────────────────────────────────

class StackPanel(QWidget):
    def __init__(self):
        super().__init__(); self.setStyleSheet(f"background:{BG};")
        self._lay=QVBoxLayout(self); self._lay.setContentsMargins(0,0,0,0)
        self.empty=None; self.editor=None
    def addWidget(self,w): self._lay.addWidget(w)
    def show_empty(self):
        if self.empty: self.empty.show()
        if self.editor: self.editor.hide()
    def show_editor(self):
        if self.empty: self.empty.hide()
        if self.editor: self.editor.show()

# ── App principale ────────────────────────────────────────────────────────────

# ── Waveform loader ───────────────────────────────────────────────────────────

def load_waveform(path, n_bars=100):
    """Génère les données de forme d'onde. Retourne liste de 0.0-1.0."""
    import struct, wave as wavemod
    tmp = "/tmp/tagr_wave.wav"
    try:
        r = subprocess.run(
            ["afconvert","-f","WAVE","-d","LEI16@8000","-c","1", path, tmp],
            capture_output=True, timeout=15)
        if r.returncode != 0:
            raise Exception("afconvert failed")
        with wavemod.open(tmp,"rb") as wf:
            raw = wf.readframes(wf.getnframes())
        samples = struct.unpack(f"<{len(raw)//2}h", raw)
        chunk = max(1, len(samples) // n_bars)
        bars = []
        for i in range(n_bars):
            sl = samples[i*chunk:(i+1)*chunk]
            bars.append(max(abs(s) for s in sl)/32768.0 if sl else 0.0)
        return bars
    except:
        # Fallback : barres simulées si afconvert échoue
        import math, random; random.seed(0)
        return [abs(math.sin(i/4))*0.6 + random.random()*0.4 for i in range(n_bars)]


class WaveformLoader(QThread):
    done = pyqtSignal(list)
    def __init__(self, path): super().__init__(); self.path = path
    def run(self): self.done.emit(load_waveform(self.path))


# ── iPhone-style timeline ─────────────────────────────────────────────────────

class IPhoneTimeline(QWidget):
    """Timeline de découpe style éditeur vidéo iPhone.
    Poignée gauche (start) et droite (end) sur fond waveform.
    Zone sélectionnée éclairée, zones hors sélection assombries.
    """
    range_changed = pyqtSignal(float, float)
    HANDLE_W = 18   # largeur des poignées
    MIN_SEL  = 0.02 # sélection minimum en ratio

    def __init__(self, duration):
        super().__init__()
        self.duration = duration
        self.setFixedHeight(72)
        self.setMinimumWidth(500)
        self._start   = 0.0
        self._end     = 1.0
        self._bars    = []
        self._drag    = None   # "start" | "end" | "body"
        self._drag_offset = 0.0
        self.setMouseTracking(True)

    def set_waveform(self, bars):
        self._bars = bars
        self.update()

    def set_range(self, s, e):
        self._start = max(0.0, min(1.0, s))
        self._end   = max(0.0, min(1.0, e))
        self.update()

    def _r2x(self, r):
        W = self.width()
        return int(self.HANDLE_W + r * (W - 2 * self.HANDLE_W))

    def _x2r(self, x):
        W = self.width()
        inner = W - 2 * self.HANDLE_W
        return max(0.0, min(1.0, (x - self.HANDLE_W) / inner))

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        W, H = self.width(), self.height()
        HW   = self.HANDLE_W
        inner_w = W - 2 * HW

        xs = self._r2x(self._start)
        xe = self._r2x(self._end)

        # ── Fond total ─────────────────────────────────────────────────
        p.fillRect(0, 0, W, H, QColor(20, 20, 20))

        # ── Waveform ───────────────────────────────────────────────────
        bars = self._bars
        n    = len(bars) if bars else 1
        bar_w = max(1.0, inner_w / n)
        mid_y = H // 2

        for i, v in enumerate(bars):
            bx = HW + int(i * inner_w / n)
            bh = max(2, int(v * (H - 10)))
            by = mid_y - bh // 2

            # Couleur : sélectionnée vs hors sélection
            ratio = i / n
            if self._start <= ratio <= self._end:
                c = QColor(ACCENT); c.setAlpha(220)
            else:
                c = QColor(70, 70, 70)
            p.fillRect(int(bx), by, max(1, int(bar_w) - 1), bh, c)

        # ── Overlay sombre hors sélection ──────────────────────────────
        shadow = QColor(0, 0, 0, 140)
        p.fillRect(HW, 0, max(0, xs - HW), H, shadow)
        p.fillRect(xe, 0, max(0, W - xe - HW), H, shadow)

        # ── Bordures de sélection (haut et bas) ────────────────────────
        p.setPen(QPen(QColor(ACCENT), 2))
        p.drawLine(xs, 0, xe, 0)
        p.drawLine(xs, H-1, xe, H-1)

        # ── Poignée GAUCHE ─────────────────────────────────────────────
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(ACCENT)))
        p.drawRoundedRect(0, 0, HW, H, 5, 5)
        # Ligne blanche centrale
        p.setPen(QPen(QColor(0, 0, 0, 200), 3, Qt.PenStyle.SolidLine,
                      Qt.PenCapStyle.RoundCap))
        cx = HW // 2
        p.drawLine(cx - 2, H//2 - 8, cx - 2, H//2 + 8)
        p.drawLine(cx + 2, H//2 - 8, cx + 2, H//2 + 8)

        # ── Poignée DROITE ─────────────────────────────────────────────
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(ACCENT)))
        p.drawRoundedRect(W - HW, 0, HW, H, 5, 5)
        p.setPen(QPen(QColor(0, 0, 0, 200), 3, Qt.PenStyle.SolidLine,
                      Qt.PenCapStyle.RoundCap))
        cx2 = W - HW // 2
        p.drawLine(cx2 - 2, H//2 - 8, cx2 - 2, H//2 + 8)
        p.drawLine(cx2 + 2, H//2 - 8, cx2 + 2, H//2 + 8)

        # ── Repositionner les poignées sur xs/xe ───────────────────────
        # Poignée start (colle au marqueur xs)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(ACCENT)))
        p.drawRoundedRect(xs - HW, 0, HW, H, 4, 4)
        p.setPen(QPen(QColor(0,0,0,180), 3, Qt.PenStyle.SolidLine,
                      Qt.PenCapStyle.RoundCap))
        lx = xs - HW//2
        p.drawLine(lx-2, H//2-8, lx-2, H//2+8)
        p.drawLine(lx+2, H//2-8, lx+2, H//2+8)

        # Poignée end
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(ACCENT)))
        p.drawRoundedRect(xe, 0, HW, H, 4, 4)
        p.setPen(QPen(QColor(0,0,0,180), 3, Qt.PenStyle.SolidLine,
                      Qt.PenCapStyle.RoundCap))
        rx = xe + HW//2
        p.drawLine(rx-2, H//2-8, rx-2, H//2+8)
        p.drawLine(rx+2, H//2-8, rx+2, H//2+8)

        p.end()

    def mousePressEvent(self, e):
        x  = e.position().x()
        xs = self._r2x(self._start)
        xe = self._r2x(self._end)
        HW = self.HANDLE_W

        if xs - HW <= x <= xs + 4:
            self._drag = "start"
        elif xe - 4 <= x <= xe + HW:
            self._drag = "end"
        elif xs < x < xe:
            self._drag = "body"
            self._drag_offset = self._x2r(x) - self._start
        self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, e):
        if not self._drag:
            # Cursor adaptatif
            x  = e.position().x()
            xs = self._r2x(self._start)
            xe = self._r2x(self._end)
            HW = self.HANDLE_W
            if xs - HW <= x <= xs + 4 or xe - 4 <= x <= xe + HW:
                self.setCursor(Qt.CursorShape.SizeHorCursor)
            elif xs < x < xe:
                self.setCursor(Qt.CursorShape.SizeAllCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)
            return

        r = self._x2r(e.position().x())
        if self._drag == "start":
            self._start = max(0.0, min(r, self._end - self.MIN_SEL))
        elif self._drag == "end":
            self._end = min(1.0, max(r, self._start + self.MIN_SEL))
        elif self._drag == "body":
            w = self._end - self._start
            s = max(0.0, min(1.0 - w, r - self._drag_offset))
            self._start = s
            self._end   = s + w
        self.update()
        self.range_changed.emit(self._start, self._end)

    def mouseReleaseEvent(self, _):
        self._drag = None
        self.setCursor(Qt.CursorShape.ArrowCursor)


# ── TrimDialog ────────────────────────────────────────────────────────────────

class TrimDialog(QDialog):
    def __init__(self, parent, path, duration):
        super().__init__(parent)
        self.setWindowTitle("Couper le morceau")
        self.setModal(True)
        self.setMinimumWidth(620)
        self.setStyleSheet(f"background:{BG2};color:{TEXT};")
        self.path     = path
        self.duration = duration
        self._play_proc   = None
        self._ffmpeg_proc = None
        self._preview_tmp = None
        self._build()
        # Charge la waveform en arrière-plan
        self._wf_loader = WaveformLoader(path)
        self._wf_loader.done.connect(self.timeline.set_waveform)
        self._wf_loader.start()

    def _build(self):
        v = QVBoxLayout(self)
        v.setContentsMargins(20, 18, 20, 18)
        v.setSpacing(10)

        # Titre + nom fichier
        tk = QLabel("Couper le morceau")
        tk.setStyleSheet(f"font-size:15px;font-weight:bold;color:{TEXT};")
        fn = QLabel(os.path.basename(self.path))
        fn.setStyleSheet(f"font-size:10px;color:{TEXTD};")
        v.addWidget(tk); v.addWidget(fn)

        # ── Timeline iPhone-style ──────────────────────────────────────
        self.timeline = IPhoneTimeline(self.duration)
        self.timeline.range_changed.connect(self._on_range)
        v.addWidget(self.timeline)

        # ── Temps start / durée / end ──────────────────────────────────
        row = QHBoxLayout()
        self.lbl_s = QLabel("0:00.0")
        self.lbl_s.setStyleSheet(f"color:{ACCENT};font-size:12px;font-weight:bold;")
        self.lbl_d = QLabel(f"Durée : {self._fmt(self.duration)}")
        self.lbl_d.setStyleSheet(f"color:{TEXTM};font-size:11px;")
        self.lbl_d.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_e = QLabel(self._fmt(self.duration))
        self.lbl_e.setStyleSheet(f"color:{ACCENT};font-size:12px;font-weight:bold;")
        self.lbl_e.setAlignment(Qt.AlignmentFlag.AlignRight)
        row.addWidget(self.lbl_s)
        row.addWidget(self.lbl_d, 1)
        row.addWidget(self.lbl_e)
        v.addLayout(row)

        # ── Champs saisie précise ──────────────────────────────────────
        pr = QHBoxLayout(); pr.setSpacing(16)

        def tfield(label, attr, placeholder):
            col = QVBoxLayout(); col.setSpacing(3)
            col.addWidget(QLabel(label, styleSheet=f"color:{TEXTD};font-size:9px;"))
            e = QLineEdit(); e.setPlaceholderText(placeholder)
            e.setMaximumWidth(100)
            e.setStyleSheet(
                f"background:{FIELDBG};color:{TEXT};border:1px solid {BORDER};"
                f"border-radius:4px;padding:6px 8px;font-size:12px;"
                f"font-family:'Courier New';")
            col.addWidget(e); pr.addLayout(col)
            setattr(self, attr, e); return e

        tfield("Début (m:ss.s)", "edit_s", "0:00.0").setText("0:00.0")
        tfield("Fin (m:ss.s)",   "edit_e", self._fmt(self.duration)).setText(self._fmt(self.duration))
        self.edit_s.editingFinished.connect(self._from_text_s)
        self.edit_e.editingFinished.connect(self._from_text_e)

        pr.addStretch()
        reset = QPushButton("Tout sélectionner")
        reset.setStyleSheet(
            f"background:{PANEL};color:{TEXTM};border:none;"
            f"padding:8px 12px;font-size:10px;border-radius:4px;")
        reset.setCursor(Qt.CursorShape.PointingHandCursor)
        reset.clicked.connect(self._reset)
        pr.addWidget(reset, alignment=Qt.AlignmentFlag.AlignBottom)
        v.addLayout(pr)

        hint = QLabel("Glisse les poignées vertes pour sélectionner · Déplace la sélection par le centre")
        hint.setStyleSheet(f"color:{TEXTD};font-size:9px;")
        v.addWidget(hint)

        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color:{BORDER};"); v.addWidget(sep)

        # ── Boutons ────────────────────────────────────────────────────
        br = QHBoxLayout(); br.setSpacing(10)

        self.prev_btn = QPushButton("▶  Écouter la sélection")
        self.prev_btn.setStyleSheet(
            f"background:{PANEL};color:{TEXT};border:none;"
            f"padding:10px 18px;font-size:11px;border-radius:5px;")
        self.prev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.prev_btn.clicked.connect(self._toggle_preview)

        apply_btn = QPushButton("Appliquer le découpage")
        apply_btn.setStyleSheet(
            f"background:{ACCENT};color:#000;font-weight:bold;border:none;"
            f"padding:10px 22px;font-size:12px;border-radius:5px;")
        apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        apply_btn.clicked.connect(self._apply)

        cancel_btn = QPushButton("Annuler")
        cancel_btn.setStyleSheet(
            f"background:{PANEL};color:{TEXTM};border:none;"
            f"padding:10px 16px;font-size:11px;border-radius:5px;")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)

        br.addWidget(self.prev_btn); br.addStretch()
        br.addWidget(cancel_btn); br.addWidget(apply_btn)
        v.addLayout(br)

        self.status = QLabel("")
        self.status.setStyleSheet(f"color:{ACCENT};font-size:10px;")
        v.addWidget(self.status)

    # ── Helpers ───────────────────────────────────────────────────────

    def _fmt(self, s):
        m, sec = divmod(float(s), 60)
        return f"{int(m)}:{sec:04.1f}"

    def _parse(self, txt):
        try:
            txt = txt.strip()
            if ":" in txt:
                p = txt.split(":")
                return int(p[0]) * 60 + float(p[1])
            return float(txt)
        except:
            return None

    def _get_times(self):
        return (self.timeline._start * self.duration,
                self.timeline._end   * self.duration)

    def _update_labels(self, ts, te):
        self.lbl_s.setText(self._fmt(ts))
        self.lbl_e.setText(self._fmt(te))
        self.lbl_d.setText(f"Durée : {self._fmt(te - ts)}")
        self.edit_s.blockSignals(True); self.edit_e.blockSignals(True)
        self.edit_s.setText(self._fmt(ts))
        self.edit_e.setText(self._fmt(te))
        self.edit_s.blockSignals(False); self.edit_e.blockSignals(False)

    def _on_range(self, s, e):
        self._update_labels(s * self.duration, e * self.duration)

    def _from_text_s(self):
        t = self._parse(self.edit_s.text())
        if t is None: return
        t = max(0.0, min(t, self.duration - 0.5))
        te = self.timeline._end * self.duration
        t = min(t, te - 0.5)
        self.timeline.set_range(t / self.duration, self.timeline._end)
        self._update_labels(t, te)

    def _from_text_e(self):
        t = self._parse(self.edit_e.text())
        if t is None: return
        t = max(0.5, min(t, self.duration))
        ts = self.timeline._start * self.duration
        t = max(t, ts + 0.5)
        self.timeline.set_range(self.timeline._start, t / self.duration)
        self._update_labels(ts, t)

    def _reset(self):
        self.timeline.set_range(0.0, 1.0)
        self._update_labels(0.0, self.duration)

    def _find_ffmpeg(self):
        for c in ["/opt/homebrew/bin/ffmpeg","/usr/local/bin/ffmpeg",
                  "/usr/bin/ffmpeg","/opt/local/bin/ffmpeg"]:
            if os.path.isfile(c): return c
        r = subprocess.run(["which","ffmpeg"], capture_output=True)
        return r.stdout.decode().strip() if r.returncode == 0 else None

    # ── Preview ───────────────────────────────────────────────────────

    def _toggle_preview(self):
        # Si en cours → stop
        if self._play_proc and self._play_proc.poll() is None:
            self._play_proc.terminate()
            self._play_proc = None
            self.prev_btn.setText("▶  Écouter la sélection")
            return

        ts, te = self._get_times()
        dur = te - ts
        if dur < 0.1: return

        ffmpeg = self._find_ffmpeg()
        if not ffmpeg:
            self.status.setStyleSheet(f"color:{ERROR};font-size:10px;")
            self.status.setText("ffmpeg introuvable — brew install ffmpeg")
            return

        # Extraire la sélection dans un fichier tmp puis jouer avec afplay
        import tempfile
        tmp = tempfile.mktemp(suffix=os.path.splitext(self.path)[1])
        self._preview_tmp = tmp

        cmd = [ffmpeg, "-y", "-ss", str(ts), "-t", str(dur),
               "-i", self.path, "-c", "copy", tmp]
        r = subprocess.run(cmd, capture_output=True)
        if r.returncode != 0:
            self.status.setStyleSheet(f"color:{ERROR};font-size:10px;")
            self.status.setText("Erreur ffmpeg preview")
            return

        try:
            self._play_proc = subprocess.Popen(
                ["/usr/bin/afplay", tmp],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.prev_btn.setText("⏹  Stop")
            def watch():
                self._play_proc.wait()
                try:
                    os.remove(tmp)
                except: pass
                QTimer.singleShot(0, lambda: self.prev_btn.setText("▶  Écouter la sélection"))
            threading.Thread(target=watch, daemon=True).start()
        except Exception as ex:
            self.status.setStyleSheet(f"color:{ERROR};font-size:10px;")
            self.status.setText(f"Erreur lecture : {ex}")

    # ── Apply ─────────────────────────────────────────────────────────

    def _apply(self):
        ts, te = self._get_times()
        if te - ts < 0.5:
            self.status.setStyleSheet(f"color:{ERROR};font-size:10px;")
            self.status.setText("Sélection trop courte"); return

        ffmpeg = self._find_ffmpeg()
        if not ffmpeg:
            self.status.setStyleSheet(f"color:{ERROR};font-size:10px;")
            self.status.setText("ffmpeg introuvable — brew install ffmpeg"); return

        base, ext = os.path.splitext(self.path)
        out = f"{base}_cut{ext}"
        i = 1
        while os.path.exists(out):
            out = f"{base}_cut{i}{ext}"; i += 1

        self.status.setStyleSheet(f"color:{ACCENT};font-size:10px;")
        self.status.setText("Découpage en cours…")
        QApplication.processEvents()

        r = subprocess.run(
            [ffmpeg,"-y","-ss",str(ts),"-t",str(te-ts),
             "-i",self.path,"-c","copy", out],
            capture_output=True)

        if r.returncode == 0:
            try:
                orig = read_tags(self.path)
                write_tags(out, orig["title"], orig["artist"], orig["album"],
                           orig.get("year",""), orig.get("genre",""),
                           orig.get("bpm",""), orig.get("cover"))
            except: pass
            subprocess.run(["mdimport", out], capture_output=True)
            subprocess.run(["open", "-R", out])
            self.status.setText(f"Créé : {os.path.basename(out)}")
        else:
            self.status.setStyleSheet(f"color:{ERROR};font-size:10px;")
            self.status.setText(f"Erreur ffmpeg : {r.stderr.decode()[-80:]}")

    def closeEvent(self, e):
        for proc in [self._play_proc, self._ffmpeg_proc]:
            if proc and proc.poll() is None:
                proc.terminate()
        if self._preview_tmp and os.path.exists(self._preview_tmp):
            try: os.remove(self._preview_tmp)
            except: pass
        e.accept()


class FfmpegWorker(QThread):
    progress = pyqtSignal(int)    # 0-100
    finished = pyqtSignal(bool, str)  # success, message

    def __init__(self, cmd, duration_ms=0):
        super().__init__()
        self.cmd = cmd
        self.duration_ms = duration_ms

    def run(self):
        import re as _re
        try:
            cmd = self.cmd + ["-progress", "pipe:2", "-nostats"]
            proc = subprocess.Popen(
                cmd, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL,
                text=True, bufsize=1)
            for line in proc.stderr:
                line = line.strip()
                m = _re.search(r"out_time_ms=(-?\d+)", line)
                if m and self.duration_ms > 0:
                    t = max(0, int(m.group(1)))
                    pct = min(99, int(t / self.duration_ms * 100))
                    self.progress.emit(pct)
                elif "progress=end" in line:
                    self.progress.emit(100)
            proc.wait()
            if proc.returncode == 0:
                self.finished.emit(True, "")
            else:
                self.finished.emit(False, "Erreur ffmpeg")
        except Exception as e:
            self.finished.emit(False, str(e))


class Tagr(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tagr"); self.resize(1060,720); self.setMinimumSize(820,560)
        self.setStyleSheet(f"QMainWindow{{background:{BG};}}")
        self.setAcceptDrops(True)
        self.files=[]; self.rows=[]; self.current_index=-1
        self.current_cover=None; self.tags_cache={}
        self._play_proc=None; self._workers=[]
        self._sort_key="name"; self._filter_text=""
        self._cfg=load_config()
        self._build_ui()
        QShortcut(QKeySequence("Ctrl+S"),self,self._save_current)
        QShortcut(QKeySequence("Meta+S"),self,self._save_current)
        QShortcut(QKeySequence(Qt.Key.Key_Delete),self,self._delete_selected)
        QShortcut(QKeySequence(Qt.Key.Key_Backspace),self,self._delete_selected)
        QShortcut(QKeySequence(Qt.Key.Key_Up),self,self._prev_file)
        QShortcut(QKeySequence(Qt.Key.Key_Down),self,self._next_file)
        # Espace géré via keyPressEvent pour respecter le focus des champs
        QShortcut(QKeySequence("Ctrl+I"),self,self._show_shortcuts)
        QShortcut(QKeySequence("Meta+I"),self,self._show_shortcuts)
        # Cleanup workers toutes les 30 secondes
        self._cleanup_timer = QTimer(self)
        self._cleanup_timer.timeout.connect(self._cleanup_workers)
        self._cleanup_timer.start(30000)
        # Restaurer theme
        self._is_dark = self._cfg.get("is_dark", True)
        if not self._is_dark:
            _apply_palette(LIGHT_PALETTE)
        QShortcut(QKeySequence("Ctrl+Z"),self,self._undo_current)
        QShortcut(QKeySequence("Meta+Z"),self,self._undo_current)
        QShortcut(QKeySequence("Ctrl+Shift+S"),self,self._save_all)
        QShortcut(QKeySequence("Meta+Shift+S"),self,self._save_all)
        # Restaure geometry
        geo = self._cfg.get("geometry")
        if geo:
            try:
                from PyQt6.QtCore import QByteArray
                self.restoreGeometry(QByteArray.fromHex(geo.encode()))
            except: pass
        # Restaure les fichiers de la session précédente
        for p in self._cfg.get("recent_files", []):
            if os.path.isfile(p) and p not in self.files:
                self.files.append(p); self._add_row(p)
        if self.files: self._update_count()

    # ── Drag & drop (fenêtre entière) ─────────────────────────────────────────

    def dragEnterEvent(self,e):
        if e.mimeData().hasUrls():
            urls=[u.toLocalFile() for u in e.mimeData().urls()]
            if any(is_audio(u) or os.path.isdir(u) for u in urls):
                e.acceptProposedAction()
                self.list_widget.setStyleSheet(f"background:{SELBG};border-right:1px solid {BORDER};")

    def dragLeaveEvent(self,e):
        self.list_widget.setStyleSheet(f"background:{BG2};border-right:1px solid {BORDER};")

    def dropEvent(self,e):
        self.list_widget.setStyleSheet(f"background:{BG2};border-right:1px solid {BORDER};")
        for url in e.mimeData().urls():
            path=url.toLocalFile()
            if os.path.isdir(path): self._add_folder(path)
            elif is_audio(path) and path not in self.files:
                self.files.append(path); self._add_row(path)
        self._update_count(); e.acceptProposedAction()

    def _add_folder(self,folder):
        for root,_,fnames in os.walk(folder):
            for f in sorted(fnames):
                p=os.path.join(root,f)
                if is_audio(p) and p not in self.files:
                    self.files.append(p); self._add_row(p)

    def keyPressEvent(self,e):
        if e.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            focused=QApplication.focusWidget()
            if not isinstance(focused, QLineEdit):
                self._save_current()
        else: super().keyPressEvent(e)

    # ── Navigation clavier ────────────────────────────────────────────────────

    def _prev_file(self):
        if self.current_index>0 and self._check_dirty_before_nav():
            self._on_row_select(self.rows[self.current_index-1])

    def _next_file(self):
        if 0<=self.current_index<len(self.rows)-1 and self._check_dirty_before_nav():
            self._on_row_select(self.rows[self.current_index+1])

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root=QWidget(); self.setCentralWidget(root)
        main=QVBoxLayout(root); main.setContentsMargins(0,0,0,0); main.setSpacing(0)

        # Barre titre
        bar=QFrame(); bar.setFixedHeight(54)
        bar.setStyleSheet(f"background:{BG};border-bottom:1px solid {BORDER};")
        bl=QHBoxLayout(bar); bl.setContentsMargins(24,0,24,0)
        bl.addWidget(QLabel("Tagr",styleSheet=f"color:{TEXT};font-size:20px;font-weight:bold;"))
        bl.addStretch()
        def top_btn(label, fn, w=None):
            b = QPushButton(label)
            b.setStyleSheet(f"background:{PANEL};color:{TEXTM};border:1px solid {BORDER};"
                            f"border-radius:4px;font-size:9px;padding:3px 8px;")
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.clicked.connect(fn)
            if w: b.setFixedSize(w, 24)
            bl.addWidget(b)
            return b

        top_btn("CSV", self._export_csv)
        top_btn("Stats", self._show_stats)
        self.album_btn = top_btn("Vue album", self._toggle_album_view)
        top_btn("Theme", self._toggle_theme)
        info_btn = top_btn("i", self._show_shortcuts, w=26)
        info_btn.setStyleSheet(f"background:{PANEL};color:{TEXTM};border:1px solid {BORDER};"
                               f"border-radius:13px;font-size:11px;font-weight:bold;")
        main.addWidget(bar)

        body=QHBoxLayout(); body.setSpacing(0); body.setContentsMargins(0,0,0,0)
        main.addLayout(body,1)

        # ── Colonne gauche ──
        self.list_widget=QFrame()
        self.list_widget.setFixedWidth(290)
        self.list_widget.setStyleSheet(f"background:{BG2};border-right:1px solid {BORDER};")
        lv=QVBoxLayout(self.list_widget); lv.setContentsMargins(0,0,0,0); lv.setSpacing(0)

        # Header
        hdr=QFrame(); hdr.setFixedHeight(48)
        hdr.setStyleSheet(f"background:{BG2};border-bottom:1px solid {BORDER};")
        hl=QHBoxLayout(hdr); hl.setContentsMargins(12,0,12,0)
        self.count_lbl=QLabel("Aucun fichier",styleSheet=f"color:{TEXTD};font-size:10px;")
        add_btn=QPushButton("+ Ajouter")
        add_btn.setStyleSheet(f"background:{ACCENT};color:#000;font-weight:bold;font-size:10px;"
                              f"border:none;padding:4px 10px;border-radius:4px;")
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor); add_btn.clicked.connect(self._browse_files)
        hl.addWidget(self.count_lbl); hl.addStretch(); hl.addWidget(add_btn)
        lv.addWidget(hdr)

        # Filtre + tri
        ctrl=QFrame(); ctrl.setStyleSheet(f"background:{BG2};border-bottom:1px solid {BORDER};")
        cl=QVBoxLayout(ctrl); cl.setContentsMargins(10,8,10,8); cl.setSpacing(6)

        self.filter_input=QLineEdit(); self.filter_input.setPlaceholderText("Filtrer les fichiers…")
        self.filter_input.setStyleSheet(f"background:{FIELDBG};color:{TEXT};border:1px solid {BORDER};"
                                         f"border-radius:4px;padding:5px 8px;font-size:11px;")
        self.filter_input.textChanged.connect(self._apply_filter)

        sort_row=QHBoxLayout(); sort_row.setSpacing(6)
        sort_lbl=QLabel("Tri :"); sort_lbl.setStyleSheet(f"color:{TEXTD};font-size:9px;")
        self.sort_combo=QComboBox()
        self.sort_combo.addItems(["Nom","Artiste","Non sauvegardés"])
        self.sort_combo.setStyleSheet(f"background:{FIELDBG};color:{TEXT};border:1px solid {BORDER};"
                                      f"border-radius:4px;padding:3px 6px;font-size:10px;")
        self.sort_combo.currentIndexChanged.connect(self._apply_sort)
        sort_row.addWidget(sort_lbl); sort_row.addWidget(self.sort_combo,1)

        cl.addWidget(self.filter_input); cl.addLayout(sort_row)
        lv.addWidget(ctrl)

        # Liste
        scroll=QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"QScrollArea{{background:{BG2};border:none;}}"
                             f"QScrollBar:vertical{{background:{BG2};width:4px;}}"
                             f"QScrollBar::handle:vertical{{background:{BORDER};border-radius:2px;}}"
                             f"QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0;}}")
        self.list_container=QWidget(); self.list_container.setStyleSheet(f"background:{BG2};")
        self.list_layout=QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0,0,0,0); self.list_layout.setSpacing(1)
        self.list_layout.addStretch()
        scroll.setWidget(self.list_container); lv.addWidget(scroll,1)
        self._scroll_area = scroll

        self.hint=QLabel("Glisse des fichiers audio\nou un dossier entier ici\n\nMP3  FLAC  M4A  AAC")
        self.hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hint.setStyleSheet(f"color:{TEXTD};font-size:11px;padding:40px 16px;background:{BG2};")
        self.list_layout.insertWidget(0,self.hint)

        body.addWidget(self.list_widget)

        # ── Colonne droite ──
        self.right=StackPanel(); body.addWidget(self.right,1)
        self._build_empty(); self._build_editor()

    def _build_empty(self):
        w=QWidget(); w.setStyleSheet(f"background:{BG};")
        v=QVBoxLayout(w); v.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.addWidget(QLabel("Sélectionne un fichier",styleSheet=f"color:{TEXTD};font-size:14px;"),
                    alignment=Qt.AlignmentFlag.AlignCenter)
        v.addWidget(QLabel("↑ ↓ pour naviguer · Cmd+S pour sauvegarder · Entrée pour sauvegarder",
                           styleSheet=f"color:{TEXTD};font-size:10px;"),
                    alignment=Qt.AlignmentFlag.AlignCenter)
        self.right.empty=w; self.right.addWidget(w)

    def _build_editor(self):
        scroll=QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"QScrollArea{{background:{BG};border:none;}}"
                             f"QScrollBar:vertical{{background:{BG};width:4px;}}"
                             f"QScrollBar::handle:vertical{{background:{BORDER};border-radius:2px;}}"
                             f"QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0;}}")
        w=QWidget(); w.setStyleSheet(f"background:{BG};")
        v=QVBoxLayout(w); v.setContentsMargins(32,28,32,24); v.setSpacing(0)
        scroll.setWidget(w)

        # Pochette + boutons
        top=QHBoxLayout(); top.setSpacing(20); top.setAlignment(Qt.AlignmentFlag.AlignTop)
        cc=QVBoxLayout(); cc.setSpacing(6); cc.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.cover_lbl=CoverLabel()
        self.cover_lbl.clicked.connect(self._browse_cover)
        self.cover_lbl.image_dropped.connect(self._on_image_dropped)
        sub=QLabel("Cliquer ou glisser une image")
        sub.setStyleSheet(f"color:{TEXTD};font-size:9px;"); sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover_info=QLabel("")
        self.cover_info.setStyleSheet(f"color:{TEXTD};font-size:8px;"); self.cover_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cc.addWidget(self.cover_lbl); cc.addWidget(sub); cc.addWidget(self.cover_info)
        top.addLayout(cc)

        bc=QVBoxLayout(); bc.setSpacing(6); bc.setAlignment(Qt.AlignmentFlag.AlignTop)
        def abtn(txt,fn):
            b=QPushButton(txt)
            b.setStyleSheet(f"background:{PANEL};color:{TEXTM};border:none;padding:9px 14px;"
                            f"font-size:11px;text-align:left;border-radius:4px;")
            b.setCursor(Qt.CursorShape.PointingHandCursor); b.clicked.connect(fn); bc.addWidget(b); return b
        abtn("Recherche de pochette",self._search_cover_smart)
        self.play_btn=abtn("Ecouter",self._toggle_play)
        abtn("Exporter la pochette",self._export_cover)
        sep=QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color:{BORDER};"); bc.addWidget(sep)
        abtn("Couper le morceau",self._open_trim)
        sep2=QFrame(); sep2.setFrameShape(QFrame.Shape.HLine); sep2.setStyleSheet(f"color:{BORDER};"); bc.addWidget(sep2)
        abtn("Normaliser le volume",self._normalize_volume)
        abtn("Avant / Apres norm.",self._preview_before_after)
        abtn("Convertir le format",self._convert_format)
        sep3=QFrame(); sep3.setFrameShape(QFrame.Shape.HLine); sep3.setStyleSheet(f"color:{BORDER};"); bc.addWidget(sep3)
        abtn("Renommer par lot",self._batch_rename)
        top.addLayout(bc,1)
        v.addLayout(top)

        # Qualité audio
        v.addSpacing(16)
        self.quality_frame = QFrame()
        self.quality_frame.setStyleSheet(f"background:{PANEL};border-radius:6px;")
        ql = QHBoxLayout(self.quality_frame)
        ql.setContentsMargins(14,10,14,10); ql.setSpacing(20)

        self.qlbl_badge  = QLabel(); self.qlbl_badge.setStyleSheet(f"color:{TEXT};font-size:11px;font-weight:bold;background:transparent;")
        self.qlbl_detail = QLabel(); self.qlbl_detail.setStyleSheet(f"color:{TEXTM};font-size:10px;background:transparent;")
        self.qlbl_grade  = QLabel(); self.qlbl_grade.setStyleSheet(f"font-size:10px;font-weight:bold;background:transparent;")
        self.qlbl_size   = QLabel(); self.qlbl_size.setStyleSheet(f"color:{TEXTD};font-size:9px;background:transparent;")

        ql.addWidget(self.qlbl_badge)
        ql.addWidget(self.qlbl_detail, 1)
        ql.addWidget(self.qlbl_grade)
        ql.addWidget(self.qlbl_size)
        v.addWidget(self.quality_frame)

        # Champs
        def field(label,attr):
            lbl=QLabel(label); lbl.setStyleSheet(f"color:{TEXTD};font-size:9px;margin-top:12px;")
            e=QLineEdit()
            e.setStyleSheet(f"background:{FIELDBG};color:{TEXT};border:1px solid {BORDER};"
                            f"border-radius:4px;padding:9px 10px;font-size:13px;"
                            f"selection-background-color:{ACCENT};selection-color:#000;")
            e.textChanged.connect(self._mark_dirty); setattr(self,attr,e)
            v.addWidget(lbl); v.addWidget(e)

        v.addSpacing(8)
        field("TITRE",   "field_title")
        field("ARTISTE", "field_artist")
        field("ALBUM",   "field_album")

        # Ligne année / genre / bpm
        row3=QHBoxLayout(); row3.setSpacing(12)
        def small_field(label,attr,placeholder=""):
            col=QVBoxLayout(); col.setSpacing(3)
            lbl=QLabel(label); lbl.setStyleSheet(f"color:{TEXTD};font-size:9px;margin-top:12px;")
            e=QLineEdit(); e.setPlaceholderText(placeholder)
            e.setStyleSheet(f"background:{FIELDBG};color:{TEXT};border:1px solid {BORDER};"
                            f"border-radius:4px;padding:9px 10px;font-size:12px;"
                            f"selection-background-color:{ACCENT};selection-color:#000;")
            e.textChanged.connect(self._mark_dirty); setattr(self,attr,e)
            col.addWidget(lbl); col.addWidget(e); row3.addLayout(col)
        small_field("PISTE","field_track","1/12")
        small_field("ANNEE","field_year","2024")
        small_field("GENRE","field_genre","Pop")
        small_field("BPM",  "field_bpm", "120")
        bpm_btn = QPushButton("Detecter")
        bpm_btn.setStyleSheet(f"background:{PANEL};color:{ACCENT};border:1px solid {BORDER};"
                              f"border-radius:4px;font-size:9px;padding:3px 8px;margin-top:12px;")
        bpm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        bpm_btn.clicked.connect(self._detect_bpm)
        row3.addWidget(bpm_btn)
        v.addLayout(row3)

        # Boutons bas
        bot=QHBoxLayout(); bot.setSpacing(8); bot.setContentsMargins(0,20,0,0)
        save=QPushButton("Sauvegarder")
        save.setStyleSheet(f"background:{ACCENT};color:#000;font-weight:bold;font-size:12px;"
                           f"border:none;padding:10px 28px;border-radius:5px;")
        save.setCursor(Qt.CursorShape.PointingHandCursor); save.clicked.connect(self._save_current)
        save_all=QPushButton("Tout sauvegarder")
        save_all.setStyleSheet(f"background:{PANEL};color:{TEXTM};font-size:11px;border:none;padding:10px 14px;border-radius:5px;")
        save_all.setCursor(Qt.CursorShape.PointingHandCursor); save_all.clicked.connect(self._save_all)
        bot.addWidget(save); bot.addWidget(save_all); bot.addStretch()
        v.addLayout(bot)

        self.status_lbl=QLabel("")
        self.status_lbl.setStyleSheet(f"color:{ACCENT};font-size:10px;margin-top:6px;")
        v.addWidget(self.status_lbl); v.addStretch()

        self.right.editor=scroll; self.right.addWidget(scroll)

    # ── Fichiers ──────────────────────────────────────────────────────────────

    def _browse_files(self):
        last=self._cfg.get("last_folder","")
        paths,_=QFileDialog.getOpenFileNames(self,"Choisir des fichiers audio",last,
            "Audio (*.mp3 *.flac *.m4a *.aac);;Tous (*)")
        if paths:
            self._cfg["last_folder"]=os.path.dirname(paths[0]); save_config(self._cfg)
        for p in paths:
            if p not in self.files: self.files.append(p); self._add_row(p)
        self._update_count()

    def _add_row(self,path):
        self.hint.hide()
        row=FileRow(path)
        row.selected_signal.connect(self._on_row_select)
        row.delete_signal.connect(self._on_delete_row)
        self.list_layout.insertWidget(self.list_layout.count()-1,row)
        self.rows.append(row)
        self._apply_filter()
        self._cfg["recent_files"]=[r.path for r in self.rows]; save_config(self._cfg)
        w=TagLoader(path); w.done.connect(self._on_tags_loaded); w.start(); self._workers.append(w)

    def _on_tags_loaded(self,path,tags):
        self.tags_cache[path]=tags
        for row in self.rows:
            if row.path==path: row.set_display(tags["title"],tags["artist"],tags["cover"]); break
        self._detect_duplicates()

    def _update_count(self):
        n=len(self.files)
        self.count_lbl.setText(f"{n} fichier{'s' if n>1 else ''}" if n else "Aucun fichier")

    # ── Filtre & tri ──────────────────────────────────────────────────────────

    def _apply_filter(self):
        txt=self.filter_input.text().lower()
        for row in self.rows:
            tags=self.tags_cache.get(row.path,{})
            match=(txt in os.path.basename(row.path).lower() or
                   txt in tags.get("title","").lower() or
                   txt in tags.get("artist","").lower())
            row.setVisible(not txt or match)

    def _apply_sort(self):
        idx=self.sort_combo.currentIndex()
        if idx==0: key=lambda r:(os.path.basename(r.path).lower(),)
        elif idx==1: key=lambda r:(self.tags_cache.get(r.path,{}).get("artist","").lower(),)
        else: key=lambda r:(not r._dirty,)
        sorted_rows=sorted(self.rows,key=key)
        for r in sorted_rows:
            self.list_layout.removeWidget(r)
            self.list_layout.insertWidget(self.list_layout.count()-1,r)

    # ── Sélection ─────────────────────────────────────────────────────────────

    def _on_row_select(self,row):
        self._stop_play()
        if self.current_index>=0: self.rows[self.current_index].set_selected(False)
        idx=self.rows.index(row); self.current_index=idx; row.set_selected(True)
        # Auto-scroll vers le fichier sélectionné
        QTimer.singleShot(50, lambda: self._scroll_area.ensureWidgetVisible(row))
        path=self.files[idx]
        tags=self.tags_cache.get(path) or read_tags(path)
        self.tags_cache[path]=tags
        for f,k in[(self.field_title,"title"),(self.field_artist,"artist"),
                   (self.field_album,"album"),(self.field_year,"year"),
                   (self.field_genre,"genre"),(self.field_bpm,"bpm"),(self.field_track,"track")]:
            f.blockSignals(True); f.setText(tags.get(k,"")); f.blockSignals(False)
        self.current_cover=tags["cover"]
        if tags["cover"]:
            self.cover_lbl.set_image(tags["cover"])
            self._update_cover_info(tags["cover"])
        else:
            self.cover_lbl._reset()
            try: self.cover_info.setText("")
            except: pass
        self.right.show_editor(); self.status_lbl.setText("")
        self.play_btn.setText("Ecouter")
        # Qualité audio
        self._update_quality(path)


    def _update_quality(self, path):
        q = read_audio_quality(path)
        ext = path.lower().rsplit(".", 1)[-1].upper()
        sr  = q.get("sample_rate")
        br  = q.get("bitrate")
        bits= q.get("bits")
        dur = q.get("duration")
        sz  = q.get("size")

        # Badge format
        self.qlbl_badge.setText(ext)

        # Détail technique
        parts = []
        if br:   parts.append(f"{br} kbps")
        if sr:   parts.append(f"{sr/1000:.1f} kHz")
        if bits: parts.append(f"{bits}-bit")
        if dur:  m,s=divmod(int(dur),60); parts.append(f"{m}:{s:02d}")
        self.qlbl_detail.setText("  ·  ".join(parts))

        # Grade
        label, color = quality_label(path, q)
        self.qlbl_grade.setText(label)
        self.qlbl_grade.setStyleSheet(f"font-size:10px;font-weight:bold;color:{color};background:transparent;")

        # Taille fichier
        if sz:
            if sz > 1_000_000: self.qlbl_size.setText(f"{sz/1_000_000:.1f} Mo")
            else: self.qlbl_size.setText(f"{sz/1000:.0f} Ko")

    def _mark_dirty(self):
        if self.current_index>=0: self.rows[self.current_index].set_dirty(True)

    # ── Supprimer ─────────────────────────────────────────────────────────────

    def _on_delete_row(self,row):
        idx=self.rows.index(row); was=idx==self.current_index
        self.files.pop(idx); self.rows.pop(idx)
        self.list_layout.removeWidget(row); row.deleteLater()
        if was: self.current_index=-1; self.right.show_empty()
        elif self.current_index>idx: self.current_index-=1
        if not self.files: self.hint.show()
        self._update_count()

    def _delete_selected(self):
        if self.current_index>=0: self._on_delete_row(self.rows[self.current_index])

    # ── Pochette ──────────────────────────────────────────────────────────────

    def _browse_cover(self):
        path,_=QFileDialog.getOpenFileName(self,"Choisir une image",
            filter="Images (*.jpg *.jpeg *.png *.webp *.bmp);;Tous (*)")
        if path:
            try:
                img=PILImage.open(path).convert("RGB")
                self._open_crop(img)
            except Exception as e: self._flash(f"Erreur : {e}",err=True)

    def _on_image_dropped(self,img):
        self._open_crop(img)

    def _open_crop(self,img):
        d=CropDialog(self,img); d.cropped.connect(self._apply_cover); d.exec()

    def _apply_cover(self,img):
        self.current_cover=img; self.cover_lbl.set_image(img)
        self._mark_dirty(); self._flash("Pochette appliquée")

    def _export_cover(self):
        if not self.current_cover:
            self._flash("Aucune pochette à exporter",err=True); return
        path,_=QFileDialog.getSaveFileName(self,"Exporter la pochette",
            os.path.expanduser("~/Desktop/pochette.jpg"),
            "JPEG (*.jpg);;PNG (*.png)")
        if path:
            try:
                self.current_cover.save(path,quality=95)
                self._flash("Pochette exportée")
            except Exception as e: self._flash(f"Erreur : {e}",err=True)

    def _search_cover(self):
        q=f"{self.field_artist.text()} {self.field_title.text()}".strip()
        if not q: self._flash("Renseigne titre ou artiste d'abord",err=True); return
        self._flash("Recherche en cours…")
        w=Searcher(q); w.done.connect(self._on_search_done); w.start(); self._workers.append(w)

    def _on_search_done(self,results):
        if not results: self._flash("Aucun résultat",err=True); return
        d=CoverPicker(self,results); d.chosen.connect(self._on_cover_chosen); d.exec()

    def _on_cover_chosen(self,img,meta):
        self._open_crop(img)

    def _auto_identify(self):
        if self.current_index<0: return
        t=self.field_title.text().strip(); a=self.field_artist.text().strip()
        q=(f"{a} {t}".strip() or
           os.path.splitext(os.path.basename(self.files[self.current_index]))[0])
        self._flash("Identification en cours…")
        w=Searcher(q); w.done.connect(self._on_identify_done); w.start(); self._workers.append(w)

    def _on_identify_done(self,results):
        if not results: self._flash("Aucun résultat",err=True); return
        r=results[0]
        for f,k in[(self.field_title,"title"),(self.field_artist,"artist"),(self.field_album,"album")]:
            f.blockSignals(True); f.setText(r.get(k,"")); f.blockSignals(False)
        self._mark_dirty(); self._flash(f"{r['artist']} — {r['title']}")
        if r.get("artwork"):
            f=ImageFetcher(r["artwork"],r)
            f.done.connect(lambda img,m:(setattr(self,'current_cover',img),self.cover_lbl.set_image(img)))
            f.start(); self._workers.append(f)

    # ── Lecture ───────────────────────────────────────────────────────────────

    def _toggle_play(self):
        if self._play_proc and self._play_proc.poll() is None: self._stop_play()
        else: self._start_play()

    def _start_play(self):
        if self.current_index<0: return
        self._play_proc=subprocess.Popen(["afplay",self.files[self.current_index]])
        self.play_btn.setText("Stop")
        def watch():
            self._play_proc.wait()
            QTimer.singleShot(0,lambda:self.play_btn.setText("Ecouter"))
        threading.Thread(target=watch,daemon=True).start()

    def _stop_play(self):
        if self._play_proc and self._play_proc.poll() is None: self._play_proc.terminate()
        self._play_proc=None
        try: self.play_btn.setText("Ecouter")
        except: pass

    # ── Sauvegarder ───────────────────────────────────────────────────────────

    def _save_current(self):
        if self.current_index<0: return
        path=self.files[self.current_index]
        title=self.field_title.text().strip(); artist=self.field_artist.text().strip()
        album=self.field_album.text().strip(); year=self.field_year.text().strip()
        genre=self.field_genre.text().strip(); bpm=self.field_bpm.text().strip()
        track=self.field_track.text().strip()
        res=write_tags(path,title,artist,album,year,genre,bpm,track,self.current_cover)
        if res is True:
            self.tags_cache[path]={"title":title,"artist":artist,"album":album,
                                   "year":year,"genre":genre,"bpm":bpm,"track":track,"cover":self.current_cover}
            self.rows[self.current_index].set_display(title,artist,self.current_cover)
            self.rows[self.current_index].set_dirty(False)
            subprocess.run(["mdimport",path],capture_output=True)
            self._flash("Sauvegardé")
        else: self._flash(f"Erreur : {res}",err=True)

    # ── Renommer ──────────────────────────────────────────────────────────────

    def _rename_file(self):
        if self.current_index<0: return
        path=self.files[self.current_index]
        title=self.field_title.text().strip(); artist=self.field_artist.text().strip()
        if not title: self._flash("Renseigne un titre d'abord",err=True); return
        ext=os.path.splitext(path)[1]
        new_name=safe_fn(f"{artist} - {title}" if artist else title)+ext
        new_path=os.path.join(os.path.dirname(path),new_name)
        if new_path==path: self._flash("Déjà ce nom"); return
        if os.path.exists(new_path): self._flash("Ce nom existe déjà",err=True); return
        try:
            os.rename(path,new_path)
            self.files[self.current_index]=new_path
            self.tags_cache[new_path]=self.tags_cache.pop(path,{})
            self.rows[self.current_index].path=new_path
            subprocess.run(["mdimport",new_path],capture_output=True)
            self._flash(f"Renommé : {new_name}")
        except Exception as e: self._flash(f"Erreur : {e}",err=True)


    def _open_trim(self):
        if self.current_index < 0: return
        path = self.files[self.current_index]
        duration = None
        try:
            ext = path.lower().rsplit(".", 1)[-1]
            if ext == "mp3":
                from mutagen.mp3 import MP3; duration = MP3(path).info.length
            elif ext == "flac":
                duration = FLAC(path).info.length
            elif ext in ("m4a","aac"):
                duration = MP4(path).info.length
        except: pass
        if not duration:
            self._flash("Impossible de lire la durée du fichier", err=True); return
        TrimDialog(self, path, duration).exec()

    def keyPressEvent(self, event):
        from PyQt6.QtWidgets import QLineEdit
        focused = QApplication.focusWidget()
        if event.key() == Qt.Key.Key_Space and not isinstance(focused, QLineEdit):
            self._toggle_play()
            event.accept()
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if not isinstance(focused, QLineEdit):
                self._save_current()
                event.accept()
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        if self._play_proc and self._play_proc.poll() is None:
            self._play_proc.terminate()
        self._cfg["recent_files"] = [r.path for r in self.rows]
        self._cfg["geometry"] = self.saveGeometry().toHex().data().decode()
        self._cfg["is_dark"] = getattr(self, "_is_dark", True)
        save_config(self._cfg)
        dirty = [r for r in self.rows if r._dirty]
        if dirty:
            from PyQt6.QtWidgets import QMessageBox
            msg = QMessageBox(self)
            msg.setWindowTitle("Modifications non sauvegardées")
            msg.setText(f"{len(dirty)} fichier(s) non sauvegardé(s).")
            msg.setInformativeText("Sauvegarder avant de quitter ?")
            msg.setStyleSheet(f"background:{BG2};color:{TEXT};")
            save_btn   = msg.addButton("Sauvegarder et quitter", QMessageBox.ButtonRole.AcceptRole)
            nosave_btn = msg.addButton("Quitter sans sauvegarder", QMessageBox.ButtonRole.DestructiveRole)
            cancel_btn = msg.addButton("Annuler", QMessageBox.ButtonRole.RejectRole)
            msg.exec()
            clicked = msg.clickedButton()
            if clicked == cancel_btn:
                event.ignore(); return
            elif clicked == save_btn:
                self._save_all()
        event.accept()

    def _reveal_finder(self):
        if self.current_index>=0:
            subprocess.run(["open","-R",self.files[self.current_index]])


    def _undo_current(self):
        if self.current_index < 0: return
        path = self.files[self.current_index]
        tags = read_tags(path)
        self.tags_cache[path] = tags
        for f, k in [(self.field_title,"title"),(self.field_artist,"artist"),
                     (self.field_album,"album"),(self.field_year,"year"),
                     (self.field_genre,"genre"),(self.field_bpm,"bpm"),(self.field_track,"track")]:
            f.blockSignals(True); f.setText(tags.get(k,"")); f.blockSignals(False)
        self.current_cover = tags["cover"]
        if tags["cover"]: self.cover_lbl.set_image(tags["cover"])
        else: self.cover_lbl._reset()
        self.rows[self.current_index].set_dirty(False)
        self._flash("Modifications annulées")

    def _save_all(self):
        if self.current_index >= 0: self._save_current()
        saved = 0
        for i, row in enumerate(self.rows):
            if row._dirty and i != self.current_index:
                path = self.files[i]
                tags = self.tags_cache.get(path, {})
                res = write_tags(path,
                    tags.get("title",""), tags.get("artist",""),
                    tags.get("album",""), tags.get("year",""),
                    tags.get("genre",""), tags.get("bpm",""), tags.get("cover"))
                if res is True:
                    row.set_dirty(False)
                    subprocess.run(["mdimport", path], capture_output=True)
                    saved += 1
        self._flash(f"Tout sauvegardé ({saved} fichier(s))")

    def _check_dirty_before_nav(self):
        if self.current_index < 0: return True
        row = self.rows[self.current_index]
        if not row._dirty: return True
        from PyQt6.QtWidgets import QMessageBox
        msg = QMessageBox(self)
        msg.setWindowTitle("Modifications non sauvegardées")
        msg.setText(f"Fichier modifié : {os.path.basename(self.files[self.current_index])}")
        msg.setStyleSheet(f"background:{BG2};color:{TEXT};")
        save_btn   = msg.addButton("Sauvegarder", QMessageBox.ButtonRole.AcceptRole)
        skip_btn   = msg.addButton("Ignorer",     QMessageBox.ButtonRole.DestructiveRole)
        cancel_btn = msg.addButton("Annuler",     QMessageBox.ButtonRole.RejectRole)
        msg.exec()
        clicked = msg.clickedButton()
        if clicked == cancel_btn: return False
        if clicked == save_btn: self._save_current()
        return True


    def _update_cover_info(self, img):
        try:
            w, h = img.size
            # Taille approximative réelle (pixels * 3 canaux / compression ~10:1)
            kb_approx = max(1, (w * h * 3) // (1024 * 8))
            # Évaluation qualité
            if w >= 1000 and h >= 1000:
                quality = "Bonne qualité"
                qcolor = ACCENT
            elif w >= 500 and h >= 500:
                quality = "Qualité correcte"
                qcolor = WARN
            else:
                quality = "Trop petite"
                qcolor = ERROR
            self.cover_info.setText(f"{w}x{h} px  •  {quality}")
            self.cover_info.setStyleSheet(f"color:{qcolor};font-size:8px;")
        except:
            pass

    def _find_ffmpeg(self):
        for c in ["/opt/homebrew/bin/ffmpeg", "/usr/local/bin/ffmpeg",
                  "/usr/bin/ffmpeg", "/opt/local/bin/ffmpeg"]:
            if os.path.isfile(c): return c
        r = subprocess.run(["which", "ffmpeg"], capture_output=True)
        return r.stdout.decode().strip() if r.returncode == 0 else None

    def _normalize_volume(self):
        if self.current_index < 0: return
        path = self.files[self.current_index]
        ff = self._find_ffmpeg()
        if not ff: self._flash("ffmpeg introuvable", err=True); return

        from PyQt6.QtWidgets import QDialog, QCheckBox, QProgressDialog
        d = QDialog(self); d.setWindowTitle("Normaliser le volume")
        d.setStyleSheet(f"background:{BG2};color:{TEXT};"); d.setMinimumWidth(360)
        v = QVBoxLayout(d); v.setContentsMargins(20,20,20,20); v.setSpacing(10)
        v.addWidget(QLabel(f"Fichier : {os.path.basename(path)}",
                           styleSheet=f"color:{TEXTD};font-size:10px;"))
        v.addWidget(QLabel("Normalisation a -14 LUFS (standard Spotify / Apple Music)",
                           styleSheet=f"color:{TEXT};font-size:11px;"))
        overwrite_chk = QCheckBox("Ecraser le fichier original")
        overwrite_chk.setStyleSheet(f"color:{TEXTM};font-size:10px;")
        v.addWidget(overwrite_chk)
        brow = QHBoxLayout()
        ok = QPushButton("Normaliser")
        ok.setStyleSheet(f"background:{ACCENT};color:#000;font-weight:bold;border:none;padding:9px 20px;border-radius:4px;")
        ok.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel = QPushButton("Annuler")
        cancel.setStyleSheet(f"background:{PANEL};color:{TEXTM};border:none;padding:9px 16px;border-radius:4px;")
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        ok.clicked.connect(d.accept); cancel.clicked.connect(d.reject)
        brow.addStretch(); brow.addWidget(cancel); brow.addWidget(ok)
        v.addLayout(brow)
        if d.exec() != QDialog.DialogCode.Accepted: return

        if overwrite_chk.isChecked():
            import tempfile
            tmp_out = tempfile.mktemp(suffix=os.path.splitext(path)[1])
        else:
            base, ext = os.path.splitext(path)
            tmp_out = f"{base}_norm{ext}"
            i = 1
            while os.path.exists(tmp_out): tmp_out = f"{base}_norm{i}{ext}"; i += 1

        # Obtenir durée
        duration_ms = 0
        try:
            import mutagen
            af = mutagen.File(path)
            if af: duration_ms = int(af.info.length * 1000)
        except: pass

        prog = QProgressDialog("Normalisation en cours...", "Annuler", 0, 100, self)
        prog.setWindowTitle("Tagr"); prog.setMinimumWidth(300)
        prog.setStyleSheet(f"background:{BG2};color:{TEXT};")
        prog.setWindowModality(Qt.WindowModality.WindowModal)
        prog.setValue(0); prog.show()

        cmd = [ff, "-y", "-i", path, "-af", "loudnorm=I=-14:TP=-1:LRA=11",
               "-ar", "44100", tmp_out]
        worker = FfmpegWorker(cmd, duration_ms)
        worker.progress.connect(prog.setValue)

        def on_done(ok_flag, msg):
            prog.close()
            if ok_flag:
                try:
                    orig = read_tags(path)
                    write_tags(tmp_out, orig["title"], orig["artist"], orig["album"],
                               orig.get("year",""), orig.get("genre",""),
                               orig.get("bpm",""), orig.get("track",""), orig.get("cover"))
                except: pass
                if overwrite_chk.isChecked():
                    try:
                        import shutil
                        shutil.move(tmp_out, path)
                        subprocess.run(["mdimport", path], capture_output=True)
                        self._flash("Normalise (-14 LUFS) — fichier original remplace")
                    except Exception as e:
                        self._flash(f"Erreur remplacement : {e}", err=True)
                else:
                    subprocess.run(["mdimport", tmp_out], capture_output=True)
                    self._flash(f"Normalise : {os.path.basename(tmp_out)}")
            else:
                self._flash("Erreur normalisation", err=True)

        worker.finished.connect(on_done)
        prog.canceled.connect(worker.terminate)
        worker.start()
        self._workers.append(worker)

    def _convert_format(self):
        if self.current_index < 0: return
        from PyQt6.QtWidgets import QDialog, QComboBox
        path = self.files[self.current_index]
        ext_cur = os.path.splitext(path)[1].lstrip(".").upper()
        fmts = [f for f in ["MP3", "FLAC", "M4A", "AAC", "WAV"] if f != ext_cur]
        d = QDialog(self)
        d.setWindowTitle("Convertir le format")
        d.setStyleSheet(f"background:{BG2};color:{TEXT};")
        v = QVBoxLayout(d); v.setContentsMargins(20,20,20,20); v.setSpacing(12)
        lbl_f = QLabel(f"Fichier : {os.path.basename(path)}")
        lbl_f.setStyleSheet(f"color:{TEXTD};font-size:10px;")
        v.addWidget(lbl_f)
        v.addWidget(QLabel("Format cible :", styleSheet=f"color:{TEXT};font-size:11px;"))
        combo = QComboBox(); combo.addItems(fmts)
        combo.setStyleSheet(f"background:{FIELDBG};color:{TEXT};border:1px solid {BORDER};"
                            f"border-radius:4px;padding:6px;font-size:12px;")
        v.addWidget(combo)
        lbl_note = QLabel("MP3 320 kbps. Le fichier original est conserve.")
        lbl_note.setStyleSheet(f"color:{TEXTD};font-size:9px;")
        v.addWidget(lbl_note)
        brow = QHBoxLayout()
        ok = QPushButton("Convertir")
        ok.setStyleSheet(f"background:{ACCENT};color:#000;font-weight:bold;border:none;"
                         f"padding:9px 20px;border-radius:4px;")
        ok.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel = QPushButton("Annuler")
        cancel.setStyleSheet(f"background:{PANEL};color:{TEXTM};border:none;"
                             f"padding:9px 16px;border-radius:4px;")
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        ok.clicked.connect(d.accept); cancel.clicked.connect(d.reject)
        brow.addStretch(); brow.addWidget(cancel); brow.addWidget(ok)
        v.addLayout(brow)
        if d.exec() != QDialog.DialogCode.Accepted: return
        fmt = combo.currentText().lower()
        ext_map = {"mp3":".mp3","flac":".flac","m4a":".m4a","aac":".aac","wav":".wav"}
        base = os.path.splitext(path)[0]
        out = base + ext_map[fmt]
        if os.path.exists(out): out = base + f"_conv{ext_map[fmt]}"
        ff = self._find_ffmpeg()
        if not ff: self._flash("ffmpeg introuvable", err=True); return
        self._flash("Conversion en cours...")
        QApplication.processEvents()
        codecs = {"mp3":["-codec:a","libmp3lame","-b:a","320k"],
                  "flac":["-codec:a","flac"],
                  "m4a":["-codec:a","aac","-b:a","256k"],
                  "aac":["-codec:a","aac","-b:a","256k"],
                  "wav":["-codec:a","pcm_s16le"]}
        cmd = [ff, "-y", "-i", path] + codecs.get(fmt, []) + [out]
        r = subprocess.run(cmd, capture_output=True)
        duration_ms = 0
        try:
            import mutagen as _m
            af = _m.File(path)
            if af: duration_ms = int(af.info.length * 1000)
        except: pass

        prog = QProgressDialog(f"Conversion en cours...", "Annuler", 0, 100, self)
        prog.setWindowTitle("Tagr"); prog.setMinimumWidth(300)
        prog.setStyleSheet(f"background:{BG2};color:{TEXT};")
        prog.setWindowModality(Qt.WindowModality.WindowModal)
        prog.setValue(0); prog.show()

        worker = FfmpegWorker(cmd, duration_ms)
        worker.progress.connect(prog.setValue)

        def on_conv_done(ok_flag, msg, out=out, path=path):
            prog.close()
            if ok_flag:
                try:
                    orig = read_tags(path)
                    write_tags(out, orig["title"], orig["artist"], orig["album"],
                               orig.get("year",""), orig.get("genre",""),
                               orig.get("bpm",""), orig.get("track",""), orig.get("cover"))
                except: pass
                subprocess.run(["mdimport", out], capture_output=True)
                self._flash(f"Converti : {os.path.basename(out)}")
            else:
                self._flash("Erreur conversion", err=True)

        worker.finished.connect(on_conv_done)
        prog.canceled.connect(worker.terminate)
        worker.start()
        self._workers.append(worker)

    def _batch_rename(self):
        from PyQt6.QtWidgets import QDialog, QLineEdit, QCheckBox
        d = QDialog(self)
        d.setWindowTitle("Renommer par lot")
        d.setStyleSheet(f"background:{BG2};color:{TEXT};")
        v = QVBoxLayout(d); v.setContentsMargins(20,20,20,20); v.setSpacing(10)
        v.addWidget(QLabel("Pattern de renommage :", styleSheet=f"color:{TEXT};font-size:11px;"))
        pattern_edit = QLineEdit("{artiste} - {titre}")
        pattern_edit.setStyleSheet(f"background:{FIELDBG};color:{TEXT};border:1px solid {BORDER};"
                                   f"border-radius:4px;padding:8px;font-size:12px;")
        v.addWidget(pattern_edit)
        hint = QLabel("Variables : {titre}  {artiste}  {album}  {piste}  {annee}")
        hint.setStyleSheet(f"color:{TEXTD};font-size:9px;")
        v.addWidget(hint)
        all_chk = QCheckBox("Appliquer a tous les fichiers de la liste")
        all_chk.setChecked(True)
        all_chk.setStyleSheet(f"color:{TEXTM};font-size:10px;")
        v.addWidget(all_chk)
        brow = QHBoxLayout()
        ok = QPushButton("Renommer")
        ok.setStyleSheet(f"background:{ACCENT};color:#000;font-weight:bold;border:none;"
                         f"padding:9px 20px;border-radius:4px;")
        ok.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel = QPushButton("Annuler")
        cancel.setStyleSheet(f"background:{PANEL};color:{TEXTM};border:none;"
                             f"padding:9px 16px;border-radius:4px;")
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        ok.clicked.connect(d.accept); cancel.clicked.connect(d.reject)
        brow.addStretch(); brow.addWidget(cancel); brow.addWidget(ok)
        v.addLayout(brow)
        self.status_lbl2 = QLabel("")
        self.status_lbl2.setStyleSheet(f"color:{TEXTD};font-size:9px;")
        v.addWidget(self.status_lbl2)
        if d.exec() != QDialog.DialogCode.Accepted: return
        pattern = pattern_edit.text().strip()
        if not pattern: return
        targets = self.rows if all_chk.isChecked() else (
            [self.rows[self.current_index]] if self.current_index >= 0 else [])
        renamed = 0
        for row in targets:
            path = row.path
            tags = self.tags_cache.get(path) or read_tags(path)
            name = pattern
            name = name.replace("{titre}",   tags.get("title","") or os.path.splitext(os.path.basename(path))[0])
            name = name.replace("{artiste}", tags.get("artist","") or "Inconnu")
            name = name.replace("{album}",   tags.get("album","") or "")
            name = name.replace("{piste}",   tags.get("track","") or "")
            name = name.replace("{annee}",   tags.get("year","") or "")
            name = safe_fn(name.strip())
            if not name: continue
            ext = os.path.splitext(path)[1]
            new_path = os.path.join(os.path.dirname(path), name + ext)
            if new_path == path: continue
            if os.path.exists(new_path): continue
            try:
                os.rename(path, new_path)
                idx = self.rows.index(row)
                self.files[idx] = new_path
                row.path = new_path
                self.tags_cache[new_path] = self.tags_cache.pop(path, {})
                row.update_display(tags.get("title",""), tags.get("artist",""),
                                   tags.get("cover"))
                subprocess.run(["mdimport", new_path], capture_output=True)
                renamed += 1
            except: pass
        self._flash(f"{renamed} fichier(s) renomme(s)")

    def _show_shortcuts(self):
        from PyQt6.QtWidgets import QDialog
        d = QDialog(self)
        d.setWindowTitle("Raccourcis clavier")
        d.setStyleSheet(f"background:{BG2};color:{TEXT};")
        d.setMinimumWidth(380)
        v = QVBoxLayout(d); v.setContentsMargins(24,20,24,20); v.setSpacing(4)
        title = QLabel("Raccourcis clavier")
        title.setStyleSheet(f"font-size:15px;font-weight:bold;color:{TEXT};")
        v.addWidget(title)
        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color:{BORDER};margin:8px 0;"); v.addWidget(sep)
        shortcuts = [
            ("Cmd+S",           "Sauvegarder"),
            ("Cmd+Shift+S",     "Tout sauvegarder"),
            ("Cmd+Z",           "Annuler les modifications"),
            ("Entree",          "Sauvegarder"),
            ("Espace",          "Lecture / Pause"),
            ("Haut / Bas",      "Fichier precedent / suivant"),
            ("Suppr / Retour",  "Retirer le fichier de la liste"),
        ]
        for keys, desc in shortcuts:
            row = QHBoxLayout(); row.setSpacing(12)
            k = QLabel(keys)
            k.setStyleSheet(f"background:{PANEL};color:{ACCENT};font-family:'Courier New';"
                            f"font-size:10px;padding:3px 8px;border-radius:3px;")
            k.setFixedWidth(160)
            d_lbl = QLabel(desc)
            d_lbl.setStyleSheet(f"color:{TEXT};font-size:11px;")
            row.addWidget(k); row.addWidget(d_lbl); row.addStretch()
            w = QWidget(); w.setLayout(row); v.addWidget(w)
        v.addSpacing(8)
        close = QPushButton("Fermer")
        close.setStyleSheet(f"background:{PANEL};color:{TEXTM};border:none;"
                            f"padding:8px 20px;border-radius:4px;")
        close.setCursor(Qt.CursorShape.PointingHandCursor)
        close.clicked.connect(d.accept)
        v.addWidget(close, alignment=Qt.AlignmentFlag.AlignCenter)
        d.exec()

    def _detect_duplicates(self):
        seen = {}
        # Reset d'abord toutes les couleurs
        for row in self.rows:
            try:
                sel = row._selected
                color = TEXT if not sel else TEXT
                row.lbl_t.setStyleSheet(
                    f"color:{TEXT};font-size:12px;font-weight:bold;background:transparent;")
            except: pass
        # Signaler uniquement si titre ET artiste sont tous les deux renseignés
        for i, row in enumerate(self.rows):
            try:
                tags = self.tags_cache.get(row.path, {})
                t = tags.get("title","").lower().strip()
                a = tags.get("artist","").lower().strip()
                if not t or not a:
                    continue  # Ignorer si l'un des deux est vide
                key = (t, a)
                if key in seen:
                    row.lbl_t.setStyleSheet(
                        f"color:{WARN};font-size:12px;font-weight:bold;background:transparent;")
                    try:
                        self.rows[seen[key]].lbl_t.setStyleSheet(
                            f"color:{WARN};font-size:12px;font-weight:bold;background:transparent;")
                    except: pass
                else:
                    seen[key] = i
            except: pass


    def _export_csv(self):
        if not self.files:
            self._flash("Aucun fichier dans la liste", err=True); return
        path, _ = QFileDialog.getSaveFileName(
            self, "Exporter en CSV", os.path.expanduser("~/Desktop/tagr_export.csv"),
            "CSV (*.csv)")
        if not path: return
        import csv
        fields = ["fichier","titre","artiste","album","piste","annee","genre","bpm","qualite"]
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=fields)
                w.writeheader()
                for row in self.rows:
                    tags = self.tags_cache.get(row.path, {})
                    q = read_audio_quality(row.path)
                    label, _ = quality_label(row.path, q)
                    w.writerow({
                        "fichier": os.path.basename(row.path),
                        "titre":   tags.get("title",""),
                        "artiste": tags.get("artist",""),
                        "album":   tags.get("album",""),
                        "piste":   tags.get("track",""),
                        "annee":   tags.get("year",""),
                        "genre":   tags.get("genre",""),
                        "bpm":     tags.get("bpm",""),
                        "qualite": label,
                    })
            self._flash(f"CSV exporte : {os.path.basename(path)}")
            subprocess.run(["open", "-R", path])
        except Exception as e:
            self._flash(f"Erreur export : {e}", err=True)

    def _suggest_with_ai(self):
        if self.current_index < 0: return
        api_key = self._cfg.get("anthropic_key", "").strip()
        if not api_key:
            self._ask_api_key(); return
        path = self.files[self.current_index]
        filename = os.path.splitext(os.path.basename(path))[0]
        t = self.field_title.text().strip()
        a = self.field_artist.text().strip()
        self._flash("Analyse IA en cours...")

        def do():
            try:
                import urllib.request, json
                prompt = (f"Fichier audio : \"{filename}\"\n"
                          f"Titre actuel : \"{t}\"\n"
                          f"Artiste actuel : \"{a}\"\n\n"
                          f"Analyse le nom du fichier et suggere les metadonnees les plus probables.\n"
                          f"Reponds UNIQUEMENT en JSON avec ces cles exactes (sans markdown) :\n"
                          f"{{\"title\":\"...\",\"artist\":\"...\",\"album\":\"...\","
                          f"\"year\":\"...\",\"genre\":\"...\",\"confidence\":\"high|medium|low\"}}")
                body = json.dumps({
                    "model": "claude-sonnet-4-6",
                    "max_tokens": 300,
                    "messages": [{"role": "user", "content": prompt}]
                }).encode()
                req = urllib.request.Request(
                    "https://api.anthropic.com/v1/messages",
                    data=body,
                    headers={
                        "Content-Type": "application/json",
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01"
                    })
                resp = urllib.request.urlopen(req, timeout=15)
                data = json.loads(resp.read())
                text = data["content"][0]["text"].strip()
                # Nettoyer si besoin
                if text.startswith("```"): text = text.split("```")[1].lstrip("json").strip()
                suggestion = json.loads(text)
                QTimer.singleShot(0, lambda: self._apply_ai_suggestion(suggestion))
            except Exception as e:
                QTimer.singleShot(0, lambda: self._flash(f"Erreur IA : {e}", err=True))

        import threading
        threading.Thread(target=do, daemon=True).start()

    def _apply_ai_suggestion(self, s):
        conf = s.get("confidence","")
        for f, k in [(self.field_title,"title"),(self.field_artist,"artist"),
                     (self.field_album,"album"),(self.field_year,"year"),
                     (self.field_genre,"genre")]:
            val = s.get(k,"").strip()
            if val and not f.text().strip():
                f.blockSignals(True); f.setText(val); f.blockSignals(False)
        self._mark_dirty()
        label = {"high":"(confiance elevee)","medium":"(confiance moyenne)","low":"(confiance basse)"}.get(conf,"")
        self._flash(f"Suggestion IA appliquee {label}")

    def _ask_api_key(self):
        from PyQt6.QtWidgets import QInputDialog
        key, ok = QInputDialog.getText(
            self, "Cle API Anthropic",
            "Entre ta cle API Anthropic :\n(https://console.anthropic.com)",
            QLineEdit.EchoMode.Password)
        if ok and key.strip():
            self._cfg["anthropic_key"] = key.strip()
            save_config(self._cfg)
            self._flash("Cle API enregistree")
            self._suggest_with_ai()

    def _search_cover_smart(self):
        if self.current_index < 0: return
        a = self.field_artist.text().strip()
        t = self.field_title.text().strip()
        # Priorité à l'artiste — si vide, fallback sur le titre ou le nom de fichier
        q = a or t or os.path.splitext(
            os.path.basename(self.files[self.current_index]))[0]
        if not q: return
        label = ("Recherche artiste: " + q + "...") if a else ("Recherche: " + q + "...")
        self._flash(label)
        w = Searcher(q); w.done.connect(self._on_search_done)
        w.start(); self._workers.append(w)


    # ── Worker cleanup ────────────────────────────────────────────
    def _cleanup_workers(self):
        self._workers = [w for w in self._workers if w.isRunning()]

    # ── Theme toggle ──────────────────────────────────────────────
    def _toggle_theme(self):
        self._is_dark = not getattr(self, "_is_dark", True)
        p = DARK_PALETTE if self._is_dark else LIGHT_PALETTE
        _apply_palette(p)
        self._rebuild_stylesheet()

    def _rebuild_stylesheet(self):
        self.setStyleSheet(f"QMainWindow{{background:{BG};}}")
        # Rebuild barre titre
        for w in self.findChildren(QFrame):
            try:
                if w.height() == 54:
                    w.setStyleSheet(f"background:{BG};border-bottom:1px solid {BORDER};")
            except: pass
        # Rebuild liste
        if hasattr(self, 'list_widget'):
            self.list_widget.setStyleSheet(
                f"background:{BG2};border-right:1px solid {BORDER};")
        self._flash("Theme " + ("sombre" if self._is_dark else "clair"))

    # ── BPM auto-detect ───────────────────────────────────────────
    def _detect_bpm(self):
        if self.current_index < 0: return
        path = self.files[self.current_index]
        ff = self._find_ffmpeg()
        if not ff: self._flash("ffmpeg introuvable", err=True); return
        self._flash("Detection BPM en cours...")
        def do():
            try:
                import struct, wave as wavemod, math
                tmp = "/tmp/tagr_bpm.wav"
                r = subprocess.run(
                    [ff, "-y", "-i", path, "-ar", "22050", "-ac", "1",
                     "-t", "60", "-f", "wav", tmp],
                    capture_output=True, timeout=20)
                if r.returncode != 0: raise Exception("Conversion echouee")
                with wavemod.open(tmp, "rb") as wf:
                    sr = wf.getframerate()
                    raw = wf.readframes(wf.getnframes())
                samples = [s/32768.0 for s in struct.unpack(f"<{len(raw)//2}h", raw)]
                # Energie par fenetre de 512 samples
                win = 512
                energies = []
                for i in range(0, len(samples)-win, win//2):
                    chunk = samples[i:i+win]
                    e = sum(x*x for x in chunk)/win
                    energies.append(e)
                if len(energies) < 4:
                    raise Exception("Fichier trop court")
                # Detection de pics d'energie (beats)
                avg_e = sum(energies)/len(energies)
                beats = []
                hop_sec = (win//2) / sr
                for i in range(1, len(energies)-1):
                    if (energies[i] > avg_e * 1.3 and
                        energies[i] > energies[i-1] and
                        energies[i] > energies[i+1]):
                        t = i * hop_sec
                        if not beats or t - beats[-1] > 0.2:
                            beats.append(t)
                if len(beats) > 4:
                    intervals = [beats[i+1]-beats[i] for i in range(len(beats)-1)]
                    median = sorted(intervals)[len(intervals)//2]
                    bpm = round(60.0 / median)
                    # Ajustement si hors plage raisonnable
                    while bpm < 60: bpm *= 2
                    while bpm > 200: bpm //= 2
                    QTimer.singleShot(0, lambda b=bpm: self._apply_bpm(b))
                else:
                    QTimer.singleShot(0, lambda: self._flash("BPM non detectable", err=True))
            except Exception as e:
                QTimer.singleShot(0, lambda: self._flash(f"Erreur BPM: {e}", err=True))
        import threading
        threading.Thread(target=do, daemon=True).start()

    def _apply_bpm(self, bpm):
        self.field_bpm.blockSignals(True)
        self.field_bpm.setText(str(bpm))
        self.field_bpm.blockSignals(False)
        self._mark_dirty()
        self._flash(f"BPM detecte : {bpm}")

    # ── Stats bibliotheque ────────────────────────────────────────
    def _show_stats(self):
        if not self.files:
            self._flash("Aucun fichier dans la liste", err=True); return
        from PyQt6.QtWidgets import QDialog
        d = QDialog(self); d.setWindowTitle("Statistiques")
        d.setStyleSheet(f"background:{BG2};color:{TEXT};")
        d.setMinimumWidth(340)
        v = QVBoxLayout(d); v.setContentsMargins(24,20,24,20); v.setSpacing(6)

        title = QLabel("Statistiques de la bibliotheque")
        title.setStyleSheet(f"font-size:14px;font-weight:bold;color:{TEXT};")
        v.addWidget(title)

        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color:{BORDER};"); v.addWidget(sep)

        # Calcul stats
        formats = {}; qualities = {}; artists = set(); albums = set()
        total_dur = 0; missing_cover = 0; missing_tags = 0

        for row in self.rows:
            ext = os.path.splitext(row.path)[1].lstrip(".").upper()
            formats[ext] = formats.get(ext, 0) + 1
            tags = self.tags_cache.get(row.path, {})
            if tags.get("artist"): artists.add(tags["artist"])
            if tags.get("album"):  albums.add(tags["album"])
            if not tags.get("cover"): missing_cover += 1
            if not tags.get("title") or not tags.get("artist"): missing_tags += 1
            try:
                q = read_audio_quality(row.path)
                lbl, _ = quality_label(row.path, q)
                qualities[lbl] = qualities.get(lbl, 0) + 1
                if q.get("duration"): total_dur += q["duration"]
            except: pass

        def stat_row(label, value, color=None):
            row_w = QWidget(); row_l = QHBoxLayout(row_w)
            row_l.setContentsMargins(0,2,0,2)
            lbl = QLabel(label); lbl.setStyleSheet(f"color:{TEXTM};font-size:10px;")
            val = QLabel(str(value))
            val.setStyleSheet(f"color:{color or ACCENT};font-size:10px;font-weight:bold;")
            val.setAlignment(Qt.AlignmentFlag.AlignRight)
            row_l.addWidget(lbl); row_l.addStretch(); row_l.addWidget(val)
            v.addWidget(row_w)

        stat_row("Fichiers total", len(self.files))
        h, m = divmod(int(total_dur), 3600)
        m, s = divmod(m, 60)
        stat_row("Duree totale", f"{h}h {m}m {s}s")
        stat_row("Artistes uniques", len(artists))
        stat_row("Albums uniques", len(albums))
        stat_row("Sans pochette", missing_cover, ERROR if missing_cover else ACCENT)
        stat_row("Tags incomplets", missing_tags, WARN if missing_tags else ACCENT)

        sep2 = QFrame(); sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet(f"color:{BORDER};"); v.addWidget(sep2)
        v.addWidget(QLabel("Formats :", styleSheet=f"color:{TEXTD};font-size:9px;"))
        for fmt, count in sorted(formats.items()):
            stat_row(f"  {fmt}", count, TEXT)
        v.addWidget(QLabel("Qualite :", styleSheet=f"color:{TEXTD};font-size:9px;"))
        for ql, count in sorted(qualities.items()):
            stat_row(f"  {ql}", count, TEXT)

        close = QPushButton("Fermer")
        close.setStyleSheet(f"background:{PANEL};color:{TEXTM};border:none;"
                            f"padding:8px 20px;border-radius:4px;")
        close.setCursor(Qt.CursorShape.PointingHandCursor)
        close.clicked.connect(d.accept)
        v.addWidget(close, alignment=Qt.AlignmentFlag.AlignCenter)
        d.exec()

    # ── Vue album ─────────────────────────────────────────────────
    def _toggle_album_view(self):
        self._album_view = not getattr(self, "_album_view", False)
        if self._album_view:
            self._build_album_view()
            self.album_btn.setText("Vue liste")
        else:
            self._clear_album_groups()
            self.album_btn.setText("Vue album")

    def _build_album_view(self):
        self._clear_album_groups()
        # Grouper par album
        groups = {}
        for i, row in enumerate(self.rows):
            tags = self.tags_cache.get(row.path, {})
            album = tags.get("album","") or "Sans album"
            if album not in groups: groups[album] = []
            groups[album].append((i, row))
        # Re-organiser la liste avec headers
        self._album_headers = []
        pos = 0
        for album, items in sorted(groups.items()):
            hdr = QFrame()
            hdr.setStyleSheet(f"background:{PANEL2};border-radius:4px;")
            hdr.setFixedHeight(28)
            hl = QHBoxLayout(hdr); hl.setContentsMargins(10,0,10,0)
            lbl = QLabel(album); lbl.setStyleSheet(
                f"color:{ACCENT};font-size:10px;font-weight:bold;")
            count = QLabel(f"{len(items)} titre(s)")
            count.setStyleSheet(f"color:{TEXTD};font-size:9px;")
            hl.addWidget(lbl); hl.addStretch(); hl.addWidget(count)
            self.list_layout.insertWidget(pos, hdr)
            self._album_headers.append(hdr)
            pos += 1
            for _, row in items:
                self.list_layout.removeWidget(row)
                self.list_layout.insertWidget(pos, row)
                pos += 1

    def _clear_album_groups(self):
        for hdr in getattr(self, "_album_headers", []):
            self.list_layout.removeWidget(hdr)
            hdr.deleteLater()
        self._album_headers = []
        # Remettre les rows dans l'ordre original
        for row in self.rows:
            self.list_layout.removeWidget(row)
            self.list_layout.insertWidget(self.list_layout.count()-1, row)

    # ── Before/After normalisation ────────────────────────────────
    def _preview_before_after(self):
        if self.current_index < 0: return
        path = self.files[self.current_index]
        ff = self._find_ffmpeg()
        if not ff: self._flash("ffmpeg introuvable", err=True); return

        from PyQt6.QtWidgets import QDialog
        d = QDialog(self); d.setWindowTitle("Avant / Apres normalisation")
        d.setStyleSheet(f"background:{BG2};color:{TEXT};")
        d.setMinimumWidth(360)
        v = QVBoxLayout(d); v.setContentsMargins(20,18,20,18); v.setSpacing(10)

        v.addWidget(QLabel("Ecoute comparee : Original vs Normalise (-14 LUFS)",
                           styleSheet=f"font-size:13px;font-weight:bold;color:{TEXT};"))
        v.addWidget(QLabel(os.path.basename(path),
                           styleSheet=f"font-size:9px;color:{TEXTD};"))

        self._ba_proc = None
        self._ba_tmp = None

        def play_original():
            _stop()
            self._ba_proc = subprocess.Popen(
                ["/usr/bin/afplay", path],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            status.setText("Lecture : Original")

        def play_norm():
            _stop()
            import tempfile
            tmp = tempfile.mktemp(suffix=".mp3")
            self._ba_tmp = tmp
            status.setText("Normalisation rapide en cours...")
            QApplication.processEvents()
            r = subprocess.run(
                [ff, "-y", "-i", path, "-af", "loudnorm=I=-14:TP=-1:LRA=11",
                 "-ar", "44100", "-t", "30", tmp], capture_output=True)
            if r.returncode == 0:
                self._ba_proc = subprocess.Popen(
                    ["/usr/bin/afplay", tmp],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                status.setText("Lecture : Normalise (-14 LUFS)")
            else:
                status.setText("Erreur normalisation")

        def _stop():
            if self._ba_proc and self._ba_proc.poll() is None:
                self._ba_proc.terminate()
            self._ba_proc = None

        brow = QHBoxLayout(); brow.setSpacing(10)
        btn_orig = QPushButton("▶  Original")
        btn_orig.setStyleSheet(f"background:{PANEL};color:{TEXT};border:none;"
                               f"padding:10px 18px;font-size:11px;border-radius:5px;")
        btn_orig.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_orig.clicked.connect(play_original)

        btn_norm = QPushButton("▶  Normalise")
        btn_norm.setStyleSheet(f"background:{ACCENT};color:#000;font-weight:bold;border:none;"
                               f"padding:10px 18px;font-size:11px;border-radius:5px;")
        btn_norm.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_norm.clicked.connect(play_norm)

        btn_stop = QPushButton("⏹  Stop")
        btn_stop.setStyleSheet(f"background:{PANEL};color:{TEXTM};border:none;"
                               f"padding:10px 14px;font-size:11px;border-radius:5px;")
        btn_stop.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_stop.clicked.connect(_stop)

        status = QLabel("Clique sur Original ou Normalise pour ecouter")
        status.setStyleSheet(f"color:{TEXTD};font-size:9px;")

        brow.addWidget(btn_orig); brow.addWidget(btn_norm); brow.addWidget(btn_stop)
        v.addLayout(brow); v.addWidget(status)

        def _on_close():
            _stop()
            if self._ba_tmp and os.path.exists(self._ba_tmp):
                try: os.remove(self._ba_tmp)
                except: pass
        d.rejected.connect(_on_close)
        d.accepted.connect(_on_close)

        close = QPushButton("Fermer")
        close.setStyleSheet(f"background:{PANEL};color:{TEXTM};border:none;"
                            f"padding:8px 20px;border-radius:4px;")
        close.setCursor(Qt.CursorShape.PointingHandCursor)
        close.clicked.connect(d.accept)
        v.addWidget(close, alignment=Qt.AlignmentFlag.AlignCenter)
        d.exec()

    def _flash(self,msg,err=False):
        self.status_lbl.setStyleSheet(f"color:{ERROR if err else ACCENT};font-size:10px;margin-top:6px;")
        self.status_lbl.setText(msg)
        QTimer.singleShot(4000,lambda:self.status_lbl.setText(""))



# ── Trim Dialog ───────────────────────────────────────────────────────────────


if __name__=="__main__":
    app=QApplication(sys.argv); app.setStyle("Fusion")
    win=Tagr(); win.show(); sys.exit(app.exec())
