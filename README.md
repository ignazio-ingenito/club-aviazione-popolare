# Club Aviazione Popolare website refactoring

Rigenera il sito https://www.clubaviazionepopolare.org/ mantenendo i contenuti principali ma con un design moderno, responsive e con supporto tema chiaro/scuro.

# Obiettivi

- Layout mobile-first, pulito e accessibile (WCAG AA).
- Tema chiaro/scuro con toggle persistente (localStorage).
- Tipografia leggibile (es. Inter/Roboto/Open Sans).
- Stile: evocare aviazione storica e senso di comunità.

# Architettura pagine

- Home: hero con immagine aerei storici + headline + CTA “Iscriviti” e “Scopri gli eventi”.
- Chi siamo: storia, missione, statuto.
- Eventi: calendario + galleria eventi passati.
- La flotta: schede tecniche e foto aerei.
- News: articoli in lista card.
- Contatti: form validato + indirizzo, telefono, social.
- Area soci: link/login.
- (Opzionale: FAQ, Sostieni il club).

# Componenti UI

- Navbar sticky con logo, menu, toggle tema e CTA.
- Hero full-width con overlay.
- Card responsive per news/eventi/flotta.
- Calendario eventi (lista + griglia).
- Galleria immagini con lightbox.
- Footer con contatti e social.
- Form contatto con validazione inline.

# Design system

- Tema chiaro: sfondo bianco/grigio chiaro, testo grigio scuro, accenti blu aviazione.
- Tema scuro: sfondo blu notte/nero, testo grigio chiaro, accenti oro/rosso avionico.
- CSS variables per colori, radius, spacing, shadow.
- Layout grid/fluid, max-width ~1200px.
- Iconografia lineare con richiami aeronautici.

# Accessibilità & performance

- Navigazione tastiera completa, focus visibile.
- Lazy loading immagini, formati moderni (WebP/AVIF).
- SEO-friendly: heading gerarchici, meta, JSON-LD base.
- Core Web Vitals: LCP <2.5s, CLS <0.1, INP <200ms.

# Tecnologia

- Preferenza: Next.js + TailwindCSS + shadcn/ui.
- Alternativa: HTML/CSS/JS vanilla.
- Componenti modulari e riutilizzabili.

# TODO


## Chi siamo

- [x] Albo storico
- [x] Costruire un aereo
- [x] Le Associazioni Affiliate
- [x] Cosa facciamo
- [x] La Nostra Storia
- [x] Organigramma
- [x] Organigramma

##  Attività

- [x] Corsi
- [x] Trofe Caproni
- [x] Trofe Aldinio
- [x] Trofe Eventi
- [x] Trofe Rotondi
- [x] Efficency Race

## News

- [ ] News
- [ ] Notiziari
- [ ] Raduni - ER -> Migrato in `News`
- [x] Eventi - Attività -> Migrato in `News`
- [x] Corsi di aggiornamento
- [x] Le storire dei soci
- [x] Riviste -> Migrato in `La nostra storia`


## Gallery

- [ ] Gallery

## Contatti

- [ ] Contatti


## Area Soci



# Package updates

```
rm -rf node_modules pnpm-lock.yaml
```

```
pnpm store prune
pnpm cache delete
pnpm update
```

```
pnpm install
```


# Node version 
```
source ~/.bashrc
volta install node@20
volta install pnpm@10
node -v
pnpm run dev
```
