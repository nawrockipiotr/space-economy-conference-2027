# Space Economy Conference 2027 — strona

**Live: https://nawrockipiotr.github.io/space-economy-conference-2027/**

Statyczny HTML, bez buildu. Pages: branch `main`, katalog `/ (root)`.
Każdy push na `main` uruchamia nowy build (~1 min). `.nojekyll` wyłącza
przetwarzanie Jekyllem — nie usuwaj go.

## Struktura

```
index.html                    strona główna
conference-information.html   academic-track.html      professional-track.html
academic-committee.html       themes.html              program.html
submission.html               registration.html        community-recognition.html
previous-events.html          pdw-aom-2026.html        pdw-aom-2025.html
space-drinks-2026.html        contact-team.html
support.js                    runtime renderujący strony .dc
assets/video/                 16 klipów tła (H.264, maks. 1920 px, bez audio)
assets/stills/                klatki plakatowe (poster) do każdego klipu
assets/vendor/                React 18.3.1, ReactDOM, Babel standalone — lokalnie
assets/brand/logo.png  assets/favicon.png  assets/og-image.jpg
assets/committee/ team/ pdw2025/ pdw2026/ space-drinks/
```

`community-recognition.html` to strona wolnostojąca (własny CSS i fonty w base64),
nie korzysta z `support.js`.

## Czego NIE robić przy kolejnym eksporcie z Claude Design

Eksport nadpisuje cztery rzeczy, które trzeba nakładać za każdym razem:

1. **Nazwy plików.** Eksport daje `Nazwa.dc.html`; muszą być małe litery bez
   `.dc`, a strona główna jako `index.html`. Odwołania w HTML trzeba przepisać.
2. **`support.js` ciągnie React, ReactDOM i Babel z unpkg.com.** Bez sieci
   albo przy awarii CDN strona nie renderuje się w ogóle. Pliki leżą lokalnie
   w `assets/vendor/`, a w `support.js` podmienione są URL-e i zdjęty atrybut
   `integrity` (przy lokalnych plikach `file://` wywala się na CORS).
3. **Metadane.** Eksport nie daje `<title>` ani `description`. Bez nich karta
   przeglądarki i wyniki wyszukiwania pokazują sam URL.
4. **Wideo.** Eksport waży ~130 MB.

## Wideo

Maks. 1920 px szerokości, H.264 CRF 23 (`aq-mode=3`, preset slow, Lanczos),
bez ścieżki dźwiękowej, `+faststart`. Razem 73 MB zamiast 130 MB.

Nie schodź niżej z rozdzielczością. Część klipów ma cienkie równoległe linie —
przy 1280 px rozpadają się na plamy i mory, a ekrany 2560 px robią z tego
dwukrotny upscale. CRF 27–29 przy 1280 px, sugerowane w README eksportu,
daje widoczną papkę.

Każdy `<video>` ma `poster` z `assets/stills/` — klatkę wyciętą z tego samego
klipu w sekundzie, od której się zaczyna (`data-start`). Bez tego strona jest
czarna, dopóki wideo się nie zdekoduje.

## Open Graph

`og:image` i `og:url` mają adresy bezwzględne wskazujące na
`nawrockipiotr.github.io/space-economy-conference-2027`. Po przeniesieniu
repozytorium albo podpięciu własnej domeny trzeba je podmienić we wszystkich
15 plikach HTML — inaczej podgląd linku przestanie działać.
