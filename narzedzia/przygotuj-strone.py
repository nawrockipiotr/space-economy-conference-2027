#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Przygotowuje eksport z Claude Design do publikacji na GitHub Pages.

Uzycie:
    python3 przygotuj-strone.py <eksport.zip albo folder>
    python3 przygotuj-strone.py <eksport.zip> --do ../                (wgraj wprost do repozytorium)
    python3 przygotuj-strone.py <eksport.zip> --do ../ --usun-zbedne  (skasuj tez pliki juz niepotrzebne)
    python3 przygotuj-strone.py <eksport.zip> --bez-wideo             (pomin przekodowanie, np. gdy brak ffmpeg)

Wymaga: Python 3.8+, ffmpeg (do wideo), polaczenia z internetem (pobiera React).
"""
import argparse, glob, html, io, json, os, re, shutil, subprocess, sys, tempfile, urllib.request, zipfile
from pathlib import Path

KAT = Path(__file__).resolve().parent
PROG_MENU = 1099           # ponizej tej szerokosci: hamburger
WIDEO_SZEROKOSC = 1920     # maks. szerokosc klipow tla
WIDEO_CRF = 23

def log(s=""):  print(s, flush=True)
def krok(n, s): log(f"\n[{n}] {s}")
def ostrzez(s): log(f"    UWAGA: {s}")

def wczytaj_konfig():
    p = KAT / "metadane.json"
    if not p.exists(): sys.exit(f"Brak pliku {p}")
    return json.loads(p.read_text(encoding="utf-8"))

# ---------------------------------------------------------------- 0. wejscie
def rozpakuj(zrodlo: Path, cel: Path) -> Path:
    if zrodlo.is_file() and zrodlo.suffix.lower() == ".zip":
        with zipfile.ZipFile(zrodlo) as z: z.extractall(cel)
        src = cel
    else:
        shutil.copytree(zrodlo, cel / "x"); src = cel / "x"
    # eksport bywa zapakowany w podfolder (dist/, strona/ ...)
    for _ in range(3):
        html_tu = list(src.glob("*.html"))
        if html_tu: break
        pod = [d for d in src.iterdir() if d.is_dir()]
        if len(pod) != 1: break
        src = pod[0]
    if not list(src.glob("*.html")):
        sys.exit("Nie znalazlem plikow .html w eksporcie.")
    return src

# ------------------------------------------------- 1. nazwy plikow i odnosniki
def nazwa_docelowa(f: str) -> str:
    n = re.sub(r"\.dc\.html$", ".html", f)
    n = n.replace(" ", "-")
    return n.lower()

def krok_nazwy(s: Path):
    krok(1, "Nazwy plikow i odnosniki")
    mapa = {}
    for p in sorted(s.glob("*.html")):
        nowa = nazwa_docelowa(p.name)
        if nowa != p.name: mapa[p.name] = nowa
    # strona glowna
    if not (s / "index.html").exists():
        kandydaci = [k for k, v in mapa.items() if re.search(r"site|home|strona.?glowna", k, re.I)]
        if kandydaci:
            mapa[kandydaci[0]] = "index.html"
        else:
            sys.exit("Brak index.html i nie potrafie zgadnac, ktora strona jest glowna. "
                     "Nazwij artboard strony glownej 'index' w Claude Design.")
    for stara, nowa in mapa.items(): (s / stara).rename(s / nowa)
    subs = {}
    for stara, nowa in mapa.items():
        subs[stara] = nowa
        subs[stara.replace(" ", "%20")] = nowa
    ile = 0
    for p in sorted(s.glob("*.html")):
        t = o = p.read_text(encoding="utf-8")
        for k in sorted(subs, key=len, reverse=True):
            if k in t: ile += t.count(k); t = t.replace(k, subs[k])
        if t != o: p.write_text(t, encoding="utf-8")
    log(f"    przemianowano {len(mapa)} plikow, przepisano {ile} odnosnikow")
    zostaly = {m for p in s.glob("*.html") for m in re.findall(r"[\w.-]+\.dc\.html", p.read_text(encoding='utf-8'))}
    if zostaly: ostrzez(f"zostaly odnosniki do {sorted(zostaly)[:3]}")

# ------------------------------------------------------ 2. React lokalnie
def krok_react(s: Path):
    krok(2, "Biblioteki (React, ReactDOM, Babel) lokalnie zamiast z unpkg")
    sj = s / "support.js"
    if not sj.exists(): return ostrzez("brak support.js — pomijam")
    t = sj.read_text(encoding="utf-8")
    url_sri = dict(re.findall(r'"(https://unpkg\.com/[^"]+)";\s*\n?\s*var \w+_SRI = "(sha384-[^"]+)"', t))
    urls = re.findall(r'https://unpkg\.com/[^"\']+', t)
    if not urls: return log("    brak odwolan do unpkg — nic do zrobienia")
    (s / "assets" / "vendor").mkdir(parents=True, exist_ok=True)
    import base64, hashlib
    for u in sorted(set(urls)):
        nazwa = u.rsplit("/", 1)[-1]
        cel = s / "assets" / "vendor" / nazwa
        log(f"    pobieram {nazwa} ...")
        with urllib.request.urlopen(u, timeout=120) as r: dane = r.read()
        oczek = url_sri.get(u)
        if oczek:
            mam = "sha384-" + base64.b64encode(hashlib.sha384(dane).digest()).decode()
            if mam != oczek: sys.exit(f"Plik {nazwa} nie zgadza sie z suma kontrolna z support.js — przerywam.")
        cel.write_bytes(dane)
        t = t.replace(u, f"./assets/vendor/{nazwa}")
    stare = 'return typeof v === "string" && v ? { src: v } : { src: url, integrity: sri };'
    nowe  = 'return typeof v === "string" && v ? { src: v } : { src: url };'
    if stare in t: t = t.replace(stare, nowe)
    else: ostrzez("nie znalazlem miejsca z 'integrity' — strona moze nie dzialac po otwarciu z dysku")
    sj.write_text(t, encoding="utf-8")
    log(f"    {len(set(urls))} plikow w assets/vendor, atrybut integrity zdjety")

# ------------------------------------------------------------- 3. metadane
def krok_metadane(s: Path, cfg: dict):
    krok(3, "Tytuly, opisy, favicon i Open Graph")
    baza = cfg["_adres_strony"].rstrip("/"); serwis = cfg["_nazwa_serwisu"]
    kotwica = '<meta name="viewport" content="width=device-width, initial-scale=1">'
    brakuje = []
    for p in sorted(s.glob("*.html")):
        t = p.read_text(encoding="utf-8")
        if kotwica not in t: ostrzez(f"{p.name}: brak znacznika viewport, pomijam"); continue
        if 'property="og:image"' in t: continue
        wpis = cfg["strony"].get(p.name)
        wlasny = bool(wpis) and wpis.get("tytul") is None
        if wpis is None:
            brakuje.append(p.name)
            tytul = p.stem.replace("-", " ").title() + " | " + serwis
            opis = cfg["_opis_domyslny"]
        elif wlasny:
            m = re.search(r"<title>(.*?)</title>", t, re.S); tytul = m.group(1).strip() if m else serwis
            m = re.search(r'name="description" content="(.*?)"', t, re.S); opis = m.group(1) if m else cfg["_opis_domyslny"]
        else:
            tytul, opis = wpis["tytul"], wpis["opis"]
        te, de = html.escape(tytul, quote=True), html.escape(opis, quote=True)
        url = baza + "/" + ("" if p.name == "index.html" else p.name)
        glowa = [kotwica]
        if not wlasny:
            glowa += [f"<title>{te}</title>", f'<meta name="description" content="{de}">']
        glowa += [
            '<link rel="icon" type="image/png" href="./assets/favicon.png">',
            '<meta property="og:type" content="website">',
            f'<meta property="og:site_name" content="{html.escape(serwis, quote=True)}">',
            f'<meta property="og:title" content="{te}">',
            f'<meta property="og:description" content="{de}">',
            f'<meta property="og:image" content="{baza}/assets/og-image.jpg">',
            f'<meta property="og:url" content="{url}">',
            '<meta name="twitter:card" content="summary_large_image">',
        ]
        p.write_text(t.replace(kotwica, "\n".join(glowa), 1), encoding="utf-8")
    zasoby = KAT / "zasoby"
    for nazwa, docelowo in cfg.get("_zasoby_stale", {}).items():
        if nazwa.startswith("_"): continue
        zrod = zasoby / nazwa
        if not zrod.exists(): ostrzez(f"brak narzedzia/zasoby/{nazwa}"); continue
        cel = s / docelowo; cel.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(zrod, cel)
        log(f"    wgrywam staly zasob: {docelowo}")
    if brakuje:
        ostrzez(f"tych stron nie ma w metadane.json, dostaly tytul z nazwy pliku: {', '.join(brakuje)}")
    log(f"    metadane w {len(list(s.glob('*.html')))} plikach, adres bazowy {baza}")

# ---------------------------------------------------------------- 4. wideo
def ffprobe(plik: Path, pola: str, strumien=None):
    cmd = ["ffprobe", "-v", "error"]
    if strumien: cmd += ["-select_streams", strumien]
    cmd += ["-show_entries", pola, "-of", "default=nw=1:nk=1", str(plik)]
    return subprocess.run(cmd, capture_output=True, text=True).stdout.split()

def krok_wideo(s: Path, pomin: bool):
    krok(4, "Wideo: przekodowanie i klatki plakatowe")
    kat = s / "assets" / "video"
    if not kat.exists(): return log("    brak assets/video")
    if pomin: return log("    pominiete (--bez-wideo)")
    if not shutil.which("ffmpeg"): return ostrzez("brak ffmpeg — wideo zostaje w oryginale (repozytorium bedzie ciezkie)")
    przed = sum(f.stat().st_size for f in kat.glob("*.mp4"))
    tmp = kat / "_nowe"; tmp.mkdir(exist_ok=True)
    for f in sorted(kat.glob("*.mp4")):
        out = tmp / f.name
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", str(f), "-an",
                        "-vf", f"scale=min({WIDEO_SZEROKOSC}\\,iw):-2:flags=lanczos",
                        "-c:v", "libx264", "-preset", "slow", "-crf", str(WIDEO_CRF),
                        "-x264-params", "aq-mode=3", "-pix_fmt", "yuv420p",
                        "-profile:v", "high", "-level", "4.2", "-movflags", "+faststart", str(out)], check=True)
        if out.stat().st_size >= f.stat().st_size:
            # zrodlo o niskim bitrate — rekompresja tylko by je powiekszyla
            subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", str(f), "-an",
                            "-c:v", "copy", "-movflags", "+faststart", str(out)], check=True)
            log(f"    {f.name}: zostawiam oryginal (rekompresja powiekszala plik)")
        else:
            log(f"    {f.name}: {f.stat().st_size/1048576:.1f} -> {out.stat().st_size/1048576:.1f} MB")
        f.unlink(); shutil.move(str(out), str(f))
    tmp.rmdir()
    po = sum(f.stat().st_size for f in kat.glob("*.mp4"))
    log(f"    razem {przed/1048576:.0f} MB -> {po/1048576:.0f} MB")

    # klatki plakatowe
    starty = {}
    for p in s.glob("*.html"):
        for m in re.finditer(r'<video([^>]*?)src="\./assets/video/([A-Za-z0-9._-]+\.mp4)"', p.read_text(encoding="utf-8")):
            ds = re.search(r'data-start="([0-9.]+)"', m.group(1))
            t = float(ds.group(1)) if ds else 0.0
            starty[m.group(2)] = min(starty.get(m.group(2), 1e9), t)
    stills = s / "assets" / "stills"
    if stills.exists(): shutil.rmtree(stills)
    stills.mkdir(parents=True)
    for nazwa, t in sorted(starty.items()):
        out = stills / (Path(nazwa).stem + ".jpg")
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", str(t), "-i", str(kat / nazwa),
                        "-vframes", "1", "-vf", "scale=1280:-2", "-q:v", "5", str(out)], check=True)
    ile = 0
    for p in sorted(s.glob("*.html")):
        t = o = p.read_text(encoding="utf-8")
        def rep(m):
            nonlocal ile
            if "poster=" in m.group(1): return m.group(0)
            ile += 1
            return f'<video{m.group(1)}src="./assets/video/{m.group(2)}" poster="./assets/stills/{Path(m.group(2)).stem}.jpg"'
        t = re.sub(r'<video([^>]*?)src="\./assets/video/([A-Za-z0-9._-]+\.mp4)"', rep, t)
        if t != o: p.write_text(t, encoding="utf-8")
    log(f"    {len(starty)} klatek plakatowych, podpiete w {ile} miejscach")


# ------------------------------------------- 5b. logo i przewymiarowane zdjecia
def krok_obrazy(s: Path, cfg: dict):
    krok("5b", "Logo w naglowku i przewymiarowane zdjecia")
    szer = cfg.get("_szerokosc_logo")
    if szer:
        wzor = re.compile(r'(brand/logo\.png"[^>]*?width:)clamp\([^)]*\)')
        ile = 0
        for p in sorted(s.glob("*.html")):
            t = p.read_text(encoding="utf-8")
            n, k = wzor.subn(lambda m: m.group(1) + szer, t)
            if k: p.write_text(n, encoding="utf-8"); ile += k
        log(f"    szerokosc logo ustawiona na {szer} w {ile} miejscach" if ile
            else "    nie znalazlem stylu logo w naglowku — pomijam")
    maks = cfg.get("_maks_szerokosc_portretu")
    if not maks or not shutil.which("ffmpeg"): return
    zmniejszone = 0
    for kat in ("team", "committee"):
        d = s / "assets" / kat
        if not d.exists(): continue
        for f in sorted(d.iterdir()):
            if not f.is_file() or f.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp"): continue
            w = ffprobe(f, "stream=width", "v:0")
            if not w or int(w[0]) <= maks * 1.15: continue
            przed = f.stat().st_size
            tmp = f.with_name("_tmp" + f.name)
            subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", str(f),
                            "-vf", f"scale={maks}:-2:flags=lanczos", "-q:v", "3", str(tmp)], check=True)
            if tmp.stat().st_size < przed:
                f.unlink(); shutil.move(str(tmp), str(f))
                log(f"    {kat}/{f.name}: {przed/1024:.0f} -> {f.stat().st_size/1024:.0f} kB (bylo {w[0]} px szerokosci)")
                zmniejszone += 1
            else:
                tmp.unlink()
    if not zmniejszone: log("    zdjecia w rozsadnych rozmiarach")


# -------------------------------------------------- 5c. link powrotny
def krok_link_powrotny(s: Path, cfg: dict):
    c = cfg.get("_link_powrotny")
    if not c: return
    krok("5c", "Link powrotny na stronie zrobionej poza Claude Design")
    plik = s / c["strona"]
    if not plik.exists(): return ostrzez(f"nie ma {c['strona']} — pomijam")
    t = plik.read_text(encoding="utf-8")
    if 'class="nav-back"' in t: return log("    juz jest")
    kotwica = '<div class="frame nav-inner"><a class="brand" href="#main"'
    zamkniecie = 'Chris Tucci</a><nav aria-label="Main navigation">'
    if kotwica not in t or zamkniecie not in t:
        return ostrzez("uklad gornego paska sie zmienil — link powrotny trzeba dodac recznie")
    t = t.replace(kotwica,
        '<div class="frame nav-inner"><div class="nav-left">'
        f'<a class="nav-back" href="{c["href"]}">'
        '<span aria-hidden="true">&#8592;</span>'
        f'<span class="nav-back-text">{c["etykieta"]}</span>'
        f'<span class="nav-back-short" aria-hidden="true">{c["etykieta_krotka"]}</span></a>'
        '<a class="brand" href="#main"', 1)
    t = t.replace(zamkniecie, 'Chris Tucci</a></div><nav aria-label="Main navigation">', 1)
    css = (".nav-left{display:flex;align-items:center;gap:20px;min-width:0}"
           ".nav-back{display:inline-flex;align-items:center;gap:8px;font-family:var(--mono);"
           "font-size:11px;letter-spacing:.09em;text-transform:uppercase;color:var(--muted);"
           "white-space:nowrap;padding-right:20px;border-right:1px solid var(--line);transition:color .18s}"
           ".nav-back:hover,.nav-back:focus-visible{color:var(--blue)}"
           ".nav-back-short{display:none}"
           "@media(max-width:1100px){.nav-left{gap:14px}.nav-back{padding-right:14px;font-size:10px;letter-spacing:.07em}"
           ".nav-back-text{display:none}.nav-back-short{display:inline}}"
           "@media(max-width:600px){.nav-left{gap:10px}.nav-back{padding-right:10px;font-size:9px;gap:5px}"
           ".nav-back-short{display:inline}}")
    i = t.rfind("</style>")
    if i < 0: return ostrzez("brak arkusza stylow — pomijam")
    plik.write_text(t[:i] + css + t[i:], encoding="utf-8")
    log(f"    dodany: {c['etykieta']} -> {c['href']}")

# ----------------------------------------------------------- 5. prog menu
def krok_menu(s: Path):
    krok(5, f"Prog menu: pasek na desktopie, hamburger ponizej {PROG_MENU} px")
    wzor = re.compile(r"@media \(max-width: (\d+)px\) \{ header nav \{ display: none !important; \} "
                      r"header \[data-burger\] \{ display: inline-flex !important; \} \}")
    ile = 0; stare = set()
    for p in sorted(s.glob("*.html")):
        t = p.read_text(encoding="utf-8")
        def rep(m):
            stare.add(m.group(1))
            return m.group(0).replace(f"max-width: {m.group(1)}px", f"max-width: {PROG_MENU}px")
        n = wzor.sub(rep, t)
        if n != t: p.write_text(n, encoding="utf-8"); ile += 1
    if ile: log(f"    zmienione w {ile} plikach (bylo: {', '.join(sorted(stare))} px)")
    else: ostrzez("nie znalazlem reguly menu — sprawdz wyglad na szerokim ekranie")

# ------------------------------------------------------- 6. porzadki i GH
def krok_porzadki(s: Path, cfg: dict):
    krok(6, "Porzadki i pliki dla GitHub Pages")
    for r in list(s.rglob("README.txt")): r.unlink()
    (s / ".nojekyll").write_text("", encoding="utf-8")
    (s / ".gitignore").write_text(".DS_Store\n", encoding="utf-8")
    dom = cfg["_adres_strony"].split("//", 1)[-1].strip("/")
    if not cfg.get("_tworz_cname", True):
        log("    .nojekyll, .gitignore (bez CNAME — strona nie stoi na GitHub Pages)")
    elif "github.io" in dom:
        log("    .nojekyll, .gitignore (bez CNAME — adres to jeszcze github.io)")
    else:
        (s / "CNAME").write_text(dom + "\n", encoding="utf-8")
        log(f"    .nojekyll, .gitignore, CNAME ({dom})")
        ostrzez(f"CNAME oznacza, ze {dom} MUSI juz wskazywac w DNS na GitHub. "
                "Jesli jeszcze nie wskazuje, strona bedzie niedostepna do czasu zmiany rekordow.")
    # nieuzywane zasoby
    ref = set()
    for f in list(s.glob("*.html")) + list(s.glob("*.js")):
        if not f.exists(): continue
        t = f.read_text(encoding="utf-8", errors="ignore")
        # atrybuty HTML oraz zwykle napisy w JS (tak sa zapisane sciezki do Reacta)
        for wz in (r'(?:src|href|poster)="\.?/?(assets/[^"]+)"', r'["\'`]\.?/?(assets/[^"\'`]+)["\'`]'):
            for m in re.finditer(wz, t): ref.add(m.group(1))
    martwe = []
    for f in (s / "assets").rglob("*"):
        if f.is_file() and str(f.relative_to(s)) not in ref: martwe.append(f)
    if martwe:
        waga = sum(f.stat().st_size for f in martwe)
        log(f"    usuwam {len(martwe)} nieuzywanych plikow ({waga/1048576:.1f} MB)")
        for f in martwe: f.unlink()

# ------------------------------------------------------------- 7. kontrola
def krok_kontrola(s: Path) -> bool:
    krok(7, "Kontrola koncowa")
    bledy = []
    if not (s / "index.html").exists(): bledy.append("brak index.html")
    for p in sorted(s.glob("*.html")):
        t = p.read_text(encoding="utf-8")
        if "<title>" not in t: bledy.append(f"{p.name}: brak <title>")
        for m in re.finditer(r'(?:src|href|poster)="\./?((?:assets|[a-z0-9-]+\.html)[^"#]*)', t):
            if not (s / m.group(1)).exists(): bledy.append(f"{p.name}: brak pliku {m.group(1)}")
    if (s / "support.js").exists() and "unpkg.com" in (s / "support.js").read_text(encoding="utf-8"):
        bledy.append("support.js dalej siega do unpkg.com")
    waga = sum(f.stat().st_size for f in s.rglob("*") if f.is_file())
    duze = [f for f in s.rglob("*") if f.is_file() and f.stat().st_size > 100*1024*1024]
    for f in duze: bledy.append(f"{f.name} wiekszy niz 100 MB — GitHub odrzuci")
    if bledy:
        log("    ZNALEZIONE PROBLEMY:")
        for b in sorted(set(bledy))[:20]: log(f"      - {b}")
    else:
        log("    bez zastrzezen")
    log(f"    rozmiar strony: {waga/1048576:.0f} MB, stron HTML: {len(list(s.glob('*.html')))}")
    return not bledy

# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser(description="Przygotowuje eksport z Claude Design do publikacji.")
    ap.add_argument("eksport", help="plik .zip albo folder z eksportem")
    ap.add_argument("--do", dest="repo", help="folder repozytorium — wgraj wynik wprost tam")
    ap.add_argument("--usun-zbedne", action="store_true", help="skasuj w repozytorium pliki, ktorych nowa wersja juz nie ma")
    ap.add_argument("--bez-wideo", action="store_true", help="pomin przekodowanie wideo")
    ap.add_argument("--zip", action="store_true",
                    help="spakuj wynik do strona.zip — do wgrania przez cPanel na hostingu")
    a = ap.parse_args()
    cfg = wczytaj_konfig()
    zrodlo = Path(a.eksport).expanduser().resolve()
    if not zrodlo.exists(): sys.exit(f"Nie ma czegos takiego: {zrodlo}")
    tmp = Path(tempfile.mkdtemp(prefix="strona-"))
    log(f"Rozpakowuje {zrodlo.name} ...")
    s = rozpakuj(zrodlo, tmp)
    krok_nazwy(s); krok_react(s); krok_metadane(s, cfg)
    krok_wideo(s, a.bez_wideo)
    krok_obrazy(s, cfg); krok_link_powrotny(s, cfg); krok_menu(s); krok_porzadki(s, cfg)
    ok = krok_kontrola(s)

    if a.repo:
        repo = Path(a.repo).expanduser().resolve()
        krok(8, f"Wgrywam do {repo}")
        nowe = {str(f.relative_to(s)) for f in s.rglob("*") if f.is_file()}
        stare = {str(f.relative_to(repo)) for f in repo.rglob("*")
                 if f.is_file() and ".git/" not in str(f.relative_to(repo)) and not str(f.relative_to(repo)).startswith("narzedzia/")}
        for r in sorted(nowe):
            c = repo / r; c.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(s / r, c)
        zbedne = sorted(stare - nowe - {".DS_Store"})
        if zbedne:
            if a.usun_zbedne:
                for r in zbedne: (repo / r).unlink()
                log(f"    skasowano {len(zbedne)} niepotrzebnych plikow")
            else:
                log(f"    {len(zbedne)} plikow jest juz niepotrzebnych (uruchom z --usun-zbedne, zeby je skasowac):")
                for r in zbedne[:15]: log(f"      {r}")
        log(f"    wgrane {len(nowe)} plikow")
    else:
        cel = Path.cwd() / "strona-gotowa"
        if cel.exists(): shutil.rmtree(cel)
        shutil.copytree(s, cel)
        log(f"\nGotowe: {cel}")
    if a.zip:
        paczka = Path.cwd() / "strona.zip"
        if paczka.exists(): paczka.unlink()
        with zipfile.ZipFile(paczka, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
            for f in sorted(s.rglob("*")):
                if f.is_file(): z.write(f, f.relative_to(s))
        log(f"Paczka do wgrania: {paczka} ({paczka.stat().st_size/1048576:.0f} MB)")
        log("   cPanel -> File Manager -> public_html -> Upload, potem Extract na tym pliku.")
    shutil.rmtree(tmp, ignore_errors=True)
    log("\n" + ("Mozesz publikowac." if ok else "Popraw problemy wypisane wyzej przed publikacja."))
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
