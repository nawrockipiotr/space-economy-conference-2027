# Space Economy Conference 2027 — strona

Statyczna strona, gotowa pod GitHub Pages. Bez buildu, bez zależności zewnętrznych
poza Google Fonts i jednym klipem NASA (patrz niżej).

## Publikacja na GitHub Pages

Strona stoi pod **https://nawrockipiotr.github.io/space-economy-conference-2027/**
(repo `nawrockipiotr/space-economy-conference-2027`, Pages: branch `main`, katalog `/ (root)`).
Każdy `git push` na `main` uruchamia nowy build, zwykle ~1 min.

Plik `.nojekyll` wyłącza przetwarzanie Jekyllem — nie usuwaj go.

## Struktura

```
index.html                  strona główna
conference-information.html academic-track.html      professional-track.html
academic-committee.html     themes.html              submission.html
previous-events.html        pdw-aom-2026.html        pdw-aom-2025.html
space-drinks-2026.html      contact-team.html
support.js                  runtime renderujący strony
assets/video/               19 klipów tła (H.264, maks. 1280 px, bez audio)
assets/vendor/              React 18.3.1, ReactDOM, Babel standalone (lokalnie)
assets/committee/ team/ pdw2025/ pdw2026/ space-drinks/
assets/favicon.svg  assets/og-image.jpg  assets/Space-Economy-Conference-2027-one-pager.pdf
```

Stronę można też otworzyć lokalnie — wystarczy kliknąć `index.html`.

## Co wymaga sieci

- **Google Fonts** (Barlow Condensed, Archivo) — bez internetu zadziała fallback systemowy.
Klip hero na stronie głównej (NASA, domena publiczna) jest już lokalny:
`assets/video/home-hero-nasa.mp4`.

## Open Graph

`og:image` i `og:url` wskazują na `https://nawrockipiotr.github.io/space-economy-conference-2027/`.
Po przeniesieniu repozytorium na inne konto albo podpięciu własnej domeny trzeba
podmienić ten adres we wszystkich 12 plikach HTML — inaczej podgląd linku
na LinkedInie i Facebooku przestanie się ładować.

## Wideo

Klipy tła przekodowano: maks. 1280 px szerokości, CRF 29, bez ścieżki dźwiękowej,
`+faststart`. Razem 28 MB zamiast 131 MB. Oryginały zachowaj poza repozytorium —
gdyby trzeba było przekodować inaczej.
