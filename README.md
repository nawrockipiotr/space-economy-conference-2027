# Space Economy Conference 2027 — strona

Statyczna strona, gotowa pod GitHub Pages. Bez buildu, bez zależności zewnętrznych
poza Google Fonts i jednym klipem NASA (patrz niżej).

## Publikacja na GitHub Pages

1. Wrzuć zawartość tego folderu do korzenia repozytorium (`index.html` musi być w korzeniu).
2. Settings → Pages → Source: `Deploy from a branch`, branch `main`, katalog `/ (root)`.
3. Strona pojawi się pod `https://<użytkownik>.github.io/<repo>/` (pierwszy build ~1 min).

Plik `.nojekyll` wyłącza przetwarzanie Jekyllem — nie usuwaj go.

## Struktura

```
index.html                  strona główna
conference-information.html academic-track.html      professional-track.html
academic-committee.html     themes.html              submission.html
previous-events.html        pdw-aom-2026.html        pdw-aom-2025.html
space-drinks-2026.html      contact-team.html
support.js                  runtime renderujący strony
assets/video/               18 klipów tła (H.264, maks. 1280 px, bez audio)
assets/vendor/              React 18.3.1, ReactDOM, Babel standalone (lokalnie)
assets/committee/ team/ pdw2025/ pdw2026/ space-drinks/
assets/favicon.svg  assets/og-image.jpg  assets/Space-Economy-Conference-2027-one-pager.pdf
```

Stronę można też otworzyć lokalnie — wystarczy kliknąć `index.html`.

## Co wymaga sieci

- **Google Fonts** (Barlow Condensed, Archivo) — bez internetu zadziała fallback systemowy.
- **Klip hero na stronie głównej** pobierany z `images-assets.nasa.gov` (4K, domena publiczna).
  Jeśli ma działać offline i szybciej: pobierz plik, skompresuj tak jak pozostałe
  i podmień `src` w `index.html` na lokalną ścieżkę.

## Open Graph

`og:image` wskazuje na `./assets/og-image.jpg` ścieżką względną. LinkedIn i Facebook
wymagają adresu bezwzględnego — po ustaleniu docelowego URL podmień we wszystkich
plikach HTML na pełny adres, np.
`https://<użytkownik>.github.io/<repo>/assets/og-image.jpg`.

## Wideo

Klipy tła przekodowano: maks. 1280 px szerokości, CRF 29, bez ścieżki dźwiękowej,
`+faststart`. Razem 28 MB zamiast 131 MB. Oryginały zachowaj poza repozytorium —
gdyby trzeba było przekodować inaczej.
