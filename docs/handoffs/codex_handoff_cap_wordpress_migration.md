# Handoff Codex — migrazione WordPress → Directus CAP

## Obiettivo

Proseguire autonomamente la migrazione degli articoli e delle gallery mancanti dal WordPress pubblico al nuovo Directus, arrivando almeno a:

1. verifica dell’accesso anonimo read-only a Directus;
2. completamento degli strumenti di inventory mancanti;
3. inventario live WordPress, gallery, route e Directus;
4. baseline immutabile del target;
5. report di riconciliazione degli articoli e delle gallery;
6. documentazione dei risultati e dei gate successivi.

Non eseguire import, upload, modifica schema, modifica permessi o altre scritture in Directus.

## Repository e servizi

- Repository: `ignazio-ingenito/club-avizione-popolare`
- Branch operativo: `develop`
- WordPress sorgente: `https://www.clubaviazionepopolare.org`
- Directus target: `https://cap-cms.skunklabs.uk/`
- Frontend target: `https://cap.skunklabs.uk`

L’utente è l’unico sviluppatore. Non creare pull request. Quando una slice è completa, verificata e non presenta problemi, eseguire commit e push direttamente su `develop` secondo la procedura con worktree pulito descritta sotto.

## Vincolo fondamentale

Ogni articolo, file, cartella, cover, categoria e relazione già presente in Directus è un artefatto di produzione protetto.

È vietato:

- modificare o sovrascrivere feed esistenti;
- modificare, sostituire, rinominare, spostare o eliminare file esistenti;
- modificare cartelle o relazioni esistenti;
- eseguire cleanup, deduplicazione o sincronizzazione;
- usare WordPress per aggiornare contenuti già presenti in Directus;
- usare `parser.yaml` come fonte di verità;
- usare `POST`, `PATCH`, `PUT` o `DELETE` durante questa attività;
- applicare modifiche allo schema o ai permessi;
- committare inventari live, token, corpi completi degli articoli, binari o manifest di produzione.

Directus è autorevole per tutto ciò che esiste già. Le differenze con WordPress sono drift protetto, non update candidate.

## Stato permessi Directus content migration

Aggiornamento 2026-06-23: il `DIRECTUS_ROLE_ID` presente in
`secrets/migration/directus-schema-token.20260622.sops.yaml` è stato verificato
con sole richieste GET e risulta legato al ruolo `Administrator` e alla policy
`Administrator`, con `admin_access` e `app_access` attivi. Questo classifica il
ruolo come `wrong_role_id` per la migrazione WordPress-to-Directus.

Non usare il secret `directus-schema-token` per gate o import content migration.
Serve ancora una identità dedicata `directus-createonly-content-migration`
oppure un export policy redatto dall'operatore con permission rows complete.
Finché questa evidenza manca, la readiness di produzione resta bloccata.

Aggiornamento 2026-06-23: è stato eseguito un dry-run del setup
`directus-createonly-content-migration`. Il flag di apply non era presente,
quindi non sono state fatte mutazioni Directus. La discovery GET-only ha trovato
zero ruoli, zero policy e zero utenti corrispondenti al nome/email pianificati.
Il prossimo passaggio richiede approvazione esplicita al task di
permission-management, poi creazione della identity dedicata, SOPS del nuovo
secret e raccolta GET-only del policy graph con il nuovo token create-only.

Aggiornamento 2026-06-23: il task di permission-management è stato rilanciato
con `APPLY_DIRECTUS_CREATEONLY_IDENTITY=true`. L'apply è parziale: sono stati
creati ruolo, policy e due permission rows per
`directus-createonly-content-migration`, ma la creazione dello user/token è
fallita con HTTP 400 perché Directus ha rifiutato la placeholder email
pianificata. Non esiste ancora il secret SOPS create-only, non esiste policy
graph approved per la identity finale e la readiness produzione resta bloccata.
Il prossimo task deve prima leggere e confrontare le risorse migration-owned già
create, poi creare solo un service user/token valido se il recovery resta nel
perimetro permission-management approvato. Non cancellare e non aggiornare alla
cieca ruolo, policy o permission esistenti.

Aggiornamento 2026-06-23: il recovery è stato rilanciato con
`APPLY_DIRECTUS_CREATEONLY_IDENTITY=true`. Il confronto live GET-only finale ha
classificato lo stato come `partial_state_matches_expected`: ruolo, policy e
permission rows migration-owned corrispondono al piano approvato e non è stato
trovato uno user esistente per le due email pianificate. Il recovery ha quindi
tentato solo `POST /users`, ma Directus ha rifiutato sia
`directus-createonly-content-migration@cap-migration.local` sia
`directus-createonly-content-migration@example.invalid` con HTTP 400
`FAILED_VALIDATION` sul campo `email`. Nessuno user, token o secret SOPS
create-only è stato creato. Questo tentativo è superato dal recovery con email
valida registrato sotto.

Aggiornamento 2026-06-23: il recovery è stato rilanciato con la email valida
`cap-migration@skunklabs.uk`. Dopo un nuovo confronto live GET-only classificato
`partial_state_matches_expected`, è stato eseguito solo `POST /users`, creando
lo user dedicato e il token statico create-only. Il secret cifrato ora esiste in
`secrets/migration/directus-createonly-content-migration.20260622.sops.yaml`.
La raccolta live del policy graph con il token create-only è stata tentata, ma
si è fermata correttamente su `GET /roles` con HTTP 403. Non sono stati creati
artifact raw/normalized/evaluation. La readiness produzione resta bloccata:
serve una evidenza policy graph redatta con export operator/admin redatto e
sanitizzato, oppure prova equivalente approvata separatamente. Non ampliare il
token di esecuzione per far passare il collector.

Aggiornamento 2026-06-23: è stata generata una evidenza policy graph redatta
con token admin/schema usato solo per richieste GET. L'export ha trovato solo
`feeds.read` e `feeds.create` draft-constrained per
`directus-createonly-content-migration`; nessun update/delete/share/wildcard o
accesso system/admin è stato rilevato. Il normalizer/evaluator locale ha
restituito `approved` ed è stato creato fuori Git:
`/tmp/cap-migration-runs/20260622T110402Z/directus-policy-graph-admin-evidence-20260623T152143Z/permission-evidence-create-only.json`.
Questo è Gate 1 pronto. Non autorizza ancora content `POST`: il prossimo passo
è generare e approvare `fresh-target-absence-before-create.json` come Gate 2.

## Documenti obbligatori

Leggere prima di lavorare:

```text
AGENTS.md
CONTEXT.md
docs/adr/0001-preserve-existing-directus-artifacts-during-wordpress-migration.md
docs/migrations/wordpress-to-directus/README.md
docs/migrations/wordpress-to-directus/specification.md
docs/migrations/wordpress-to-directus/plan.md
docs/migrations/wordpress-to-directus/runbook.md
docs/migrations/wordpress-to-directus/agent-loop.md
docs/migrations/wordpress-to-directus/discovery.md
```

Verificare inoltre quali handoff Task B siano già presenti e quali slice siano realmente confluite in `origin/develop`.

## Stato locale da preservare

Nel worktree originale erano presenti modifiche non committate in:

```text
components/news/infinite-news-list.tsx
lib/news-list.ts
```

Non modificarle, non ripristinarle, non aggiungerle ai commit e non includerle nel push.

Usare un worktree separato e pulito:

```bash
cd /percorso/al/repository/originale
git fetch origin --prune

WORKTREE="../club-avizione-popolare-codex"
BRANCH="codex/wp-migration-inventory"

git worktree add "$WORKTREE" -b "$BRANCH" origin/develop
cd "$WORKTREE"
```

Se il branch o il worktree esistono già, ispezionarli prima e riutilizzarli soltanto se sono puliti e basati sull’attuale `origin/develop`.

## Modalità agent-loop

Per ogni slice:

1. **Explorer read-only**
   - leggere codice e documenti;
   - verificare lo stato reale di `origin/develop`;
   - indicare `allowed_files`, `forbidden_files`, test e stop condition;
   - non modificare file.
2. **Worker seriale**
   - una sola slice atomica;
   - solo file autorizzati;
   - test sintetici, nessun dato live in Git.
3. **Reviewer indipendente**
   - controllare l’invariante degli artefatti protetti;
   - controllare che non esistano metodi HTTP di scrittura;
   - controllare diff, test, log e documentazione.
4. **Main agent**
   - aggiornare il piano;
   - commit Conventional Commit;
   - rebase su `origin/develop`;
   - push diretto su `develop` quando tutto è verde.

Non fermarsi tra slice che non richiedono decisioni dell’utente.

## Fase 1 — Verifica anonima Directus

Provare prima senza token. Usare esclusivamente `GET` o `HEAD`.

```bash
export DIRECTUS_URL='https://cap-cms.skunklabs.uk'
export RUN_ROOT="$HOME/cap-migration-runs"
export RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)-anonymous-preflight"
export RUN_DIR="$RUN_ROOT/$RUN_ID"
mkdir -p "$RUN_DIR"
```

Eseguire un preflight che salvi soltanto status code, content type, conteggi e metadati non sensibili. Non stampare corpi completi di feed nei log.

Endpoint da provare:

```text
GET /server/info
GET /permissions/me
GET /collections
GET /fields
GET /relations
GET /items/feeds?limit=1&fields=id,status,slug,original_uri,date,category,cover,gallery&meta=filter_count,total_count
GET /items/categories?limit=1&fields=id,slug,title,name&meta=filter_count,total_count
GET /files?limit=1&fields=id,filename_disk,filename_download,title,type,filesize,folder,uploaded_on,modified_on&meta=filter_count,total_count
GET /folders?limit=1&fields=id,name,parent&meta=filter_count,total_count
```

Esempio di probe sicuro:

```bash
probe() {
  path="$1"
  label="$2"
  headers="$RUN_DIR/${label}.headers"
  body="$RUN_DIR/${label}.json"

  curl --fail-with-body --silent --show-error \
    --connect-timeout 10 --max-time 60 \
    -D "$headers" -o "$body" \
    "$DIRECTUS_URL$path"

  status="$(awk 'toupper($1) ~ /^HTTP\// {code=$2} END {print code}' "$headers")"
  content_type="$(awk -F': ' 'tolower($1)=="content-type" {gsub("\\r",""); value=$2} END {print value}' "$headers")"
  printf '%s\t%s\t%s\n' "$label" "$status" "$content_type"
}
```

Non committare `RUN_DIR`.

### Valutazione accesso anonimo

L’accesso anonimo è sufficiente soltanto se permette di provare in modo completo:

- tutte le righe `feeds` rilevanti, incluse bozze e stati non pubblici se esistono;
- categorie e relazioni;
- file e cartelle;
- campi e schema necessari a interpretare i record;
- paginazione completa senza filtri invisibili;
- permessi effettivi read-only.

Se gli endpoint item restituiscono soltanto contenuti pubblicati, oppure schema/relazioni sono nascosti, l’accesso anonimo non è sufficiente per approvare la baseline. In tal caso:

- non tentare bypass;
- non usare credenziali admin;
- registrare esattamente endpoint e permessi mancanti;
- proseguire con le slice di codice e gli inventari WordPress/gallery/route che non richiedono il target;
- fermarsi soltanto al gate della baseline Directus e chiedere un’identità strettamente read-only.

Se l’identità anonima possiede permessi di create/update/delete, fermarsi e segnalarlo come problema di sicurezza. Non testarli con richieste di scrittura.

## Fase 2 — Ricognizione stato GitHub

L’attività precedente potrebbe aver lasciato branch o PR storiche. Non fidarsi dei numeri riportati nelle conversazioni.

```bash
git fetch origin --prune
git log --oneline --decorate --graph -n 30 origin/develop
git branch -r
```

Con GitHub CLI, se disponibile:

```bash
gh pr list --state open --limit 50
gh pr list --state merged --limit 20
```

Regole:

- `origin/develop` è la sola fonte di verità per il codice già integrato;
- non unire branch o PR precedenti automaticamente;
- recuperare codice da branch storici solo dopo review file-per-file e test;
- evitare implementazioni parallele o duplicate dello stesso client;
- da questo momento non creare nuove PR.

## Fase 3 — Completare Task B

Ispezionare il piano e completare soltanto le slice ancora mancanti.

Ordine raccomandato:

1. client WordPress fresh-by-default e GET/HEAD-only;
2. discovery gallery via REST con fallback HTML ordinato;
3. client Directus anonimo/read-only;
4. inventario route Next.js;
5. CLI read-only e writer atomico dei manifest;
6. test end-to-end sintetici.

### Requisiti comuni

- TLS verificato;
- niente cache implicita;
- paginazione completa e conteggi verificati;
- errori espliciti, mai omissioni silenziose;
- metodi consentiti: `GET`, `HEAD`;
- nessun import del client Directus mutabile legacy;
- fixture completamente sintetiche;
- output live fuori Git;
- JSONL deterministico e SHA-256;
- scrittura atomica tramite file temporaneo e rename;
- permessi file restrittivi quando possibile.

### Test minimi

```bash
cd cms/utils/wordpress
uv sync --locked
uv run python -m unittest discover -s tests -p 'test_*.py' -v
uv run python -m compileall -q inventory tests
uv run python -m inventory --help
```

## Fase 4 — Inventari live read-only

Creare una nuova directory run fuori Git:

```bash
export RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)-inventory"
export RUN_DIR="$HOME/cap-migration-runs/$RUN_ID"
mkdir -p "$RUN_DIR"
chmod 700 "$RUN_DIR"
```

Eseguire i comandi realmente disponibili nella CLI. L’intento è produrre:

```text
wordpress.jsonl
wordpress.jsonl.sha256
gallery.jsonl
gallery.jsonl.sha256
routes.jsonl
routes.jsonl.sha256
directus-baseline.jsonl
directus-baseline.jsonl.sha256
```

WordPress deve comprendere:

- tipi REST;
- categorie complete;
- tutti i post `publish`, inventariati una sola volta con tutte le categorie;
- featured media;
- riferimenti media inline e allegati;
- media metadata;
- data, modified, slug, link, contenuto renderizzato e hash.

Gallery deve comprendere:

- album in ordine archivio;
- slug, titolo, URL e cover;
- immagini in ordine DOM;
- URL originale, thumbnail, alt, titolo e caption disponibili;
- errori espliciti per album o immagini non leggibili.

Directus deve comprendere, se l’accesso anonimo è sufficiente:

- tutti i feed in tutti gli stati visibili e rilevanti;
- categorie;
- file;
- cartelle;
- relazioni necessarie;
- runtime/versione quando disponibile;
- schema e field metadata quando disponibile;
- conteggi e paginazione completa;
- fingerprint deterministici.

Route deve comprendere route statiche e dinamiche sotto `app/`, necessarie al collision check.

## Fase 5 — Verifica baseline

Prima di riconciliare:

- verificare checksum dei file manifest;
- controllare che `directus-baseline` non contenga soltanto un sottoinsieme pubblico;
- controllare che non esistano errori fatal;
- controllare che conteggi API e record normalizzati siano spiegabili;
- registrare l’hash del commit del codice usato;
- generare un report sintetico, senza corpi completi degli articoli.

Se il target anonimo è incompleto, non chiamarlo baseline approvabile. Denominarlo `public-view-inventory` e fermare la riconciliazione target-autorevole.

## Fase 6 — Riconciliazione read-only

Quando la baseline Directus è completa, generare:

```text
articles-reconciliation.json
articles-reconciliation.json.sha256
gallery-reconciliation.json
gallery-reconciliation.json.sha256
```

Stati minimi:

```text
ledger_match
exact_existing
validated_historical_mapping
protected_existing_drift
manual_review_candidate
create_candidate
conflict
excluded
source_error
target_only_protected
```

Regole:

- `parser.yaml` è solo evidenza opzionale da rivalidare;
- exact `original_uri` unico è evidenza forte;
- slug da solo non autorizza alcuna creazione;
- drift di un target esistente è sempre protetto;
- collisioni route o slug bloccano `create_candidate`;
- solo `create_candidate` potrà entrare in un futuro write manifest;
- non generare ancora write manifest approvato né eseguire import.

## Stato Gate 2 fresh target absence - 2026-06-23

Il Gate 1 `permission-evidence-create-only.json` è approvato, ma il Gate 2
fresh target absence generato il 2026-06-23 è respinto.

Artifact:

```text
/tmp/cap-migration-runs/20260622T110402Z/fresh-target-absence-before-create-20260623T155104Z/fresh-target-absence-before-create.json
```

SHA-256:

```text
addfd2adca5deb073e8aa4689acb76f704d0dafafd340223c9a7701c69e198e9
```

Sintesi:

- 35 operazioni controllate;
- 71 richieste live, tutte `GET`;
- nessun `POST`, `PATCH`, `PUT` o `DELETE`;
- nessun token scritto negli artifact;
- 0 route collision;
- 0 collisioni su `original_uri`;
- 0 check saltati;
- 14 collisioni slug, cioè 7 slug unici già presenti sia nel baseline target
  sia nella vista live Directus.

Conseguenza operativa:

- non eseguire `create_manifest_executor.py --execute` con questo manifest;
- rigenerare o restringere il create manifest escludendo gli slug già presenti;
- poi rigenerare un Gate 2 `approved` prima di qualsiasi prova della barriera
  `--execute`.

## Stato manifest ristretto - 2026-06-23

Il manifest è stato ristretto fuori Git rimuovendo le 7 operazioni articolo con
slug già presenti nel target:

```text
/tmp/cap-migration-runs/20260622T110402Z/create-manifest-narrowed-after-gate2-20260623T162618Z
```

Conteggi:

```text
operazioni rimosse: 7
create_feed_draft rimanenti: 21
create_gallery_draft rimanenti: 7
operazioni totali rimanenti: 28
```

Hash principali:

```text
migration-approval-narrowed.json: 6b4093177cf4156084292add1bb1e7adac802d9f8c60e1633b5fc68621d98994
create-manifest-draft-only-narrowed.json: 9dd3289b2db550dc329032e7e825e74a48449a07ff69547ee455c3f4d9dbc0f9
fresh-target-absence-before-create-narrowed.json: bbf399f35c138396dc3240c5198c05ef8d45f7d7f95296f087bc377ab39a8a55
```

Il Gate 2 ristretto è `approved`: 57 richieste live, tutte `GET`, tutte HTTP
200, nessuna collisione residua e nessun check saltato.

## Stato executor dry-run ristretto - 2026-06-23

L'executor è stato cablato con profili artefatto approvati. Il profilo
predefinito resta il manifest originale da 35 operazioni; il profilo
`narrowed_after_gate2_20260623T162618Z` vincola:

- `migration-approval-narrowed.json`;
- `create-manifest-draft-only-narrowed.json`;
- `fresh-target-absence-before-create-narrowed.json`;
- conteggi `21` articoli, `7` gallerie, `28` operazioni totali.

Dry-run generato fuori Git:

```text
/tmp/cap-migration-runs/20260622T110402Z/create-manifest-narrowed-after-gate2-20260623T162618Z/executor-dry-run-narrowed-20260623T192241Z
```

Risultato:

```text
execute_requested: false
operation_count: 28
planned_methods: POST
planned_endpoints: /items/feeds
non_read_requests_sent: 0
post_requests_sent: 0
```

Hash report:

```text
validation_report.json: 8a4da7728548d04674f562dcd1f3a7eac40036239d2409085890336e03ad570e
request_plan.json: 3c2deb0be7855514c0aa80d1c22efaaeb3706c2809f60569798efb9a85307f50
dry_run_report.json: 31bc535a8fa405ae3e1f288e749dca5837e82825345a4f1563b35a353d308d07
stop_condition_report.json: 8d2d799fdfd21f0c92e5facdfbf985f78496973517193b1e270add593975f282
```

Non è stato eseguito `create_manifest_executor.py --execute`. Non è stato
emesso alcun `POST /items/feeds`. Il prossimo task è una review indipendente
dei report narrowed dry-run e, se accettati, un prompt separato di final
execution-readiness.

## Stato final execution-readiness - 2026-06-23

La review finale locale ha validato:

- Gate 1 permission evidence: `approved`;
- Gate 2 ristretto: `approved`;
- dry-run ristretto: `approved`;
- chiavi richieste del secret SOPS create-only: presenti;
- piano teorico: 28 `POST /items/feeds` draft;
- richieste Directus inviate dal dry-run: 0;
- `--execute`: non eseguito;
- mutazioni Directus: nessuna.

Directory readiness fuori Git:

```text
/tmp/cap-migration-runs/20260622T110402Z/create-manifest-narrowed-after-gate2-20260623T162618Z/final-execution-readiness-20260623T195141Z
```

Hash principali:

```text
artifact-contract-validation.json: c949b2ad813347ea3a65e58959ce1b03bea39cf0a866bd2538afec1b99e50a83
createonly-secret-key-names.txt: fddb84f8d48b8d52bf059912d538af54b75a3f2c90018ed0e7200c4b4fef3ff7
createonly-secret-key-validation.json: 4a98e27a4365a8a736bb0b4b4c1c23a05045f4e3e2c62fb7fc05f805fb10a492
final-execution-readiness-report.json: 1b17bfac4f3703fdabb9086593cd16042044c228058aee054c734025f38f3b76
```

Status: `ready_for_explicit_execution_approval`.

Questo non autorizza ancora l'esecuzione. Il prossimo passo è preparare un
prompt separato di produzione che autorizzi esplicitamente `--execute` e
`POST /items/feeds`, se l'operatore decide di procedere.

Produrre anche un report umano contenente soltanto:

- conteggi per stato;
- identità, slug, titolo sintetico e URL dei casi ambigui;
- categorie sorgente;
- motivo della classificazione;
- errori e conflitti;
- stima numero e dimensione media da importare, senza download binario se non necessario.

## Commit e push senza PR

Dopo ogni slice o gruppo coerente:

```bash
git status --short
git diff --check
git diff --stat
git diff --name-only
```

Verificare che non siano presenti:

```text
components/news/infinite-news-list.tsx
lib/news-list.ts
parser.yaml
inventari live
token
.env
media binari
__pycache__
*.pyc
```

Commit Conventional Commit, per esempio:

```bash
git add <solo-file-autorizzati>
git commit -m "feat(inventory): add anonymous Directus baseline client"
```

Prima del push:

```bash
git fetch origin
git rebase origin/develop
uv run python -m unittest discover -s tests -p 'test_*.py' -v
uv run python -m compileall -q inventory tests
git diff --check origin/develop..HEAD
git status --short
```

Push diretto fast-forward:

```bash
git push origin HEAD:develop
```

Se il push non è fast-forward, non forzare. Fare fetch, review del nuovo commit, rebase e ripetere i test.

Dopo il push aggiornare il worktree:

```bash
git fetch origin
git rev-parse HEAD
git rev-parse origin/develop
```

I due SHA devono coincidere.

## Stop condition che richiedono decisione dell’utente

Fermarsi e chiedere soltanto in uno di questi casi:

1. accesso anonimo Directus non permette una baseline completa e serve creare un’identità read-only;
2. una scelta modifica lo schema Directus;
3. una scelta modifica permessi, ruoli o token;
4. bisogna eseguire una scrittura in staging o produzione;
5. mapping categorie non determinabile senza decisione editoriale;
6. casi ambigui di riconciliazione richiedono approvazione umana;
7. il push richiede force o sovrascrivere lavoro altrui;
8. i test non possono essere fatti passare senza allargare il perimetro o violare ADR 0001.

Non fermarsi per normali decisioni implementative risolvibili tramite best practice, documentazione del repository o test sintetici.

## Output finale richiesto

Restituire:

```yaml
summary: ""
branch_or_commit: ""
pushed_to_develop: true|false
anonymous_directus_access:
  sufficient_for_baseline: true|false
  readable_endpoints: []
  blocked_or_filtered_endpoints: []
  write_permissions_observed: false|unknown
files_changed: []
tests: []
live_artifacts:
  directory: ""
  files_and_sha256: {}
reconciliation_counts: {}
production_artifact_impact: none
risks: []
open_decisions: []
next_action: ""
```

La risposta finale deve dichiarare esplicitamente che nessun artefatto preesistente di Directus è stato modificato o eliminato.

## 2026-06-25 - Create-manifest serial writer implemented

State:

- branch: `develop`
- production execution: not performed
- Directus mutation: none
- protected production artifact impact: none

The create-manifest executor now has a gated serial writer for the narrowed
public create migration. The writer remains behind the existing execution
gates and requires `--execute`, `DIRECTUS_TOKEN`, approved permission evidence,
approved fresh target absence evidence, approved manifest/profile artifacts,
and an explicit operator approval prompt before any production write.

Implemented behavior:

- validates the request plan before transport use;
- posts only to `/items/feeds`;
- sends only draft payloads;
- writes serially;
- stops on the first HTTP or validation error;
- rejects `PATCH`, `PUT`, and `DELETE` before transport use;
- writes `execution_events.jsonl` incrementally after each successful create;
- writes `execution_report.json` only after a fully successful run;
- supports `--fresh-target-absence-sha256` so the production prompt can bind
  execution to the same-moment Gate 2 refresh artifact.

Validation performed:

```text
UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests -p 'test_pre_create_gates.py' -v
UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests -p 'test_create_manifest_executor.py' -v
UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover -s tests -p 'test_directus_policy_*.py' -v
UV_CACHE_DIR=/tmp/uv-cache uv run python -m compileall -q .
```

Result:

```text
test_pre_create_gates.py: Ran 21 tests, OK
Ran 23 tests, OK
test_directus_policy_*.py: Ran 72 tests, OK
compileall: exit 0
```

Next action:

```text
Commit the writer/docs update, then use the production prompt only after the
operator supplies the exact production approval sentence.
```

## 2026-06-25 - Narrowed artifacts recovered before production

State:

- branch: `develop`
- production execution: not performed
- Directus mutation: none
- protected production artifact impact: none

The old narrowed artifact directory referenced under `/tmp` was no longer
available. The original 35-operation artifacts were still present under:

```text
/home/iingenito/cap-migration-runs/20260622T110402Z
```

A new recovered narrowed artifact set was generated outside Git by removing the
same 7 documented slug-colliding article operations.

Recovered directory:

```text
/home/iingenito/cap-migration-runs/20260622T110402Z/create-manifest-narrowed-recovered-20260625T164519Z
```

Recovered artifact hashes:

```text
migration-approval-narrowed-recovered.json: ad4568ff085c6364afb6e91c74a068dbf1d9065f86cf7dbb252895ba69dcbd88
create-manifest-draft-only-narrowed-recovered.json: 787aab1c088f148c8231fbe3de94ff538e2bb7a989a535387ecf61a011d8597f
narrowing-recovery-report.json: 223b612db95df8a96715db7eaf2c6d9d19f5d243afdcd30ea0b63ccfda5c530a
```

Recovered dry-run:

```text
report_dir: /home/iingenito/cap-migration-runs/20260622T110402Z/create-manifest-narrowed-recovered-20260625T164519Z/executor-dry-run-recovered
request_plan.json: bb9744e03971e99fd935a6f26e7d0944aeaea22275200c8d63e0a633eb50bd77
validation_report.json: a5d10657c330719691e35bc9f2f348911ab63d52224edbece6778471b966b44b
dry_run_report.json: d3cbc41a12464013c3418766d55f1d44209fe91ff01fee9948b9f2fccd9bc02e
stop_condition_report.json: 76210e5303e4300d54e4c6ef8a1cf6b548785f8e40ee63509389516a12b0c658
```

Executor profile:

```text
narrowed_recovered_20260625T164519Z
```

Counts:

```text
create_feed_draft: 21
create_gallery_draft: 7
total_operations: 28
```

Validation:

- local manifest/approval validation accepted the recovered artifacts;
- dry-run planned only `POST /items/feeds`;
- dry-run sent `0` POST requests and `0` non-read requests;
- no Directus request was sent.

Important:

```text
The old narrowed Gate 2/readiness artifacts were not recovered. Before any
production POST, run a same-moment GET-only fresh target absence refresh and
pass its hash through --fresh-target-absence-sha256.
```

## 2026-06-26 - Gate1 derived from admin GET-only policy graph

State:

- branch: `develop`
- production execution: not performed
- Directus mutation: none
- protected production artifact impact: none

The create-only execution token cannot read `/roles/<role_id>`, so it cannot
regenerate the full policy graph itself. The safe path is a split-evidence
model:

- use a broader admin/schema token only as a GET-only evidence reader;
- export the create-only role policy graph outside Git;
- evaluate the graph locally;
- derive the canonical `permission-evidence-create-only.json` consumed by the
  existing pre-create gate;
- keep the create-only token reserved for fresh target absence and execution.

Code updates:

- `directus_policy_collector.py` now requests `fields=id,name,roles.role.*`
  for `/policies`, avoiding Directus access-junction IDs being mistaken for
  role IDs.
- `directus_policy_evidence.py` can write
  `--permission-evidence-output <path>` from approved policy graph evidence.
- `pre_create_gates.py` remains unchanged and remains the final Gate1
  validator.

Run directory:

```text
/home/iingenito/cap-migration-runs/20260622T110402Z/gate1-admin-export-20260626T062824Z
```

Artifact hashes:

```text
directus-createonly-policy-graph.raw.json: 8c0d5287fb77c33512e71404a4404b44db83a1c15a3c1a8164b6d055377432e7
directus-createonly-policy-graph.normalized.json: 1747cf1f48b578e9664a9f4b71feeb4931261f3515500b563ad7861106e4f18a
directus-createonly-policy-graph.evaluation.json: 794246ab503bc950327c83b4b0336dbc3a474909c66db309309cee2996dcf43c
permission-evidence-create-only.json: 63a115f7921dad9e36556aceb0cc722b246edec768dd25bf5c76b00e9352de2c
```

Validation:

- policy graph evaluation status: `approved`;
- derived `permission-evidence-create-only.json` passed
  `validate_permission_evidence_report`;
- no token found in the run artifacts;
- no `POST`, `PATCH`, `PUT`, or `DELETE` was sent.

Next action:

```text
Use the new Gate1 artifact for the production prompt, then run same-moment
fresh target absence validation for the 28 recovered narrowed operations. Do
not run --execute until the exact production approval sentence is present.
```
