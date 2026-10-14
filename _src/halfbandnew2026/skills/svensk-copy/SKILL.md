# Svensk copy för Halv Fjorton

Använd denna skill när du skriver eller omskriver texter i `_src/halfbandnew2026/` (sidor, byggskript, meta, schema som besökaren ser).

## Röst

Premium och självsäker, aldrig säljig. Skriv som en erfaren musiker som pratar med brudpar eller festansvarig: lugnt, konkret, glimt i ögat. Inga superlativ om oss. Visa med fakta: platser, låtar, hur kvällen går till. Bandet har heltidsjobb och jagar inte bokningar.

## Röd tråd

1. Formulera sidans **enda budskap** i en mening (internt eller i ingress).
2. Ordning i copy: **läsarens situation** → **vad vi gör** → **hur det går till** → **bevis** → **kontakt**.
3. Varje stycke svarar på en verklig fråga. Annars stryk det.
4. Mellanrubriker ska vara **konkreta**, aldrig generiska (*Om oss på festen*, *Ljud och ljus*, *Första dansen* är ok; *Hela bandet på er fest*, *Upplev magin* är inte ok).

## Språk

- Meningar **8–15 ord**, variera längd. Aktiv form, **vi** och **ni**.
- Inga substantivsjukor. Skriv **är** och **har**, inte *fungerar som*, *erbjuder*, *står för*, *bjuder på* (om det bara är utfyllnad).
- Korrekt svenska: ingen särskrivning, kongruens, **kör** (sång) inte *kö*.
- Föredra: **e-post**, **mejla**, **passar**, **upplägg**, **låtlista**, **stämning**, **fest** / **evenemang**, **anpassa**. Undvik *mail*, *funkar*, *setlist*, *event*, *vibe*.
- Översätt **aldrig** ord för ord från engelska. Musiktermer som *soul*, *funk*, *live* och ortnamn är ok när de är etablerade.
- Svensk interpunktion. **Inga tankstreck** (–, —). Inga kickers. Inga utropstecken.

### Blås och bandstorlek

Nämn **trumpet och saxofon** (och **kör** om det behövs) i vanlig prosa när det tillför fakta. Undvik marknadsfrasen *egen blåssektion* och rubriker som bara säger *Blåssektion*.

### Geografi

Bandet **utgår från Växjö**. Orter för SEO vävs in i meningar om var ni **spelat** eller **brukar åka**, i **meta** och **schema** (`areaServed`), aldrig som fri kommauppräkning (*Hemmaplan är …*, *Kärnregion:*, *Vi spelar i A, B, C, D*). Längre ortlistor hör i strukturerad data, inte som slogans i synlig copy.

## Format

- Inga priser, telefonnummer eller personnamn (utom Om oss).
- Ingen **fetstil** i brödtext. Inga emojis.
- Inga reflex-trelistor, inga punktlistor där löptext räcker (undantag: t.ex. venue-namn i befintlig layout om design kräver det).
- Ingress under hero är vanlig text, inte infobox.

## Förbjudet och uttjatat

**Svenska fraser och mönster (stryk eller omformulera):**

- *egen blåssektion*, *hela bandet på er fest*, *minnen för livet*, *oförglömlig*, *magisk stämning*, *nya höjder*, *nästa nivå*, *utöver det vanliga*, *i världsklass*, *skräddarsydd upplevelse*, *helhetsupplevelse*, *från första ton till sista dans*, *guldkant*, *dansgolvet kokar*, *vi brinner för*, *passion för musik*, *med hjärtat*
- *oavsett om … eller …*, *det är inte bara … det är …*, *i en värld där*
- Fyllnadsord: *helt enkelt*, *faktiskt*, *verkligen*, *självklart*, *givetvis*, *unik*, *gedigen*
- Byråverb: *leverera* (musik), *upplevelse* (utfyllnad), *resa* (om kvällen), *hemmaplan*
- CTA-slop: *boka nu*, *missa inte*, *säkra ert datum*
- Säljband: *helband* (som marknadsord), *färdigt band*, *komplett liveband*, *fullt liveband*, *åttamannaband* (som USP), *full bandbredd*, *liveupplevelse*, *musikunderhållning*, *dynamisk blåssektion*
- Dramatik: *inte X utan Y*, sentenser som avslutar stycken, retoriska frågor som rubriker, fragmentrader (*Lugnt. Tryggt. Live.*), påståenden utan fakta

**Svengelska:** *event*, *vibe*, *setlist*, *mail*, *funkar*, *feeling*, *show*, *level*, *perfekt match*, *implementera*, *setup* (använd *upplägg*).

**Engelsk slop (översätt/inte använd):** *delve*, *elevate*, *seamless*, *unforgettable*, *vibrant*, *curated*, *bespoke*, *journey*, *next level*, *not just X it's Y*.

| Undvik | Skriv hellre |
|--------|----------------|
| egen blåssektion | trumpet och saxofon när det behövs |
| levererar musik / sväng | spelar; håller igång dansen |
| Vi är åtta musiker … med trumpet och saxofon i bandet (mallfras) | utgår från Växjö; blås nämns där det tillför fakta |
| hela bandet till ceremonin (säljton) | alla åtta till vigseln om det passar |

## Självgranskning (kör före leverans)

1. Ett budskap i en mening?
2. Läs högt: skulle en bandmedlem säga så?
3. Noll förbjudna fraser, tankstreck, priser, telefon.
4. Inga onödiga engelska ord i svensk copy.
5. Varje adjektiv tillför fakta?
6. Stryk onödiga meningar.
7. Vad låter fortfarande AI? Åtgärda, kör igen.
8. Stavning, särskrivning, kongruens.
9. **Ivarts ok** före publicering.

## Bygg och publicering

- Källtext: `scripts/build.py`, ibland `home/index.html`, `assets/schema/organization.json`.
- Efter godkänd copy: uppdatera källan, `python3 scripts/build.py`, committa `_src/` och `testing/` tillsammans.
- Förslag utan publicering: endast i chat, committa inte sidändringar (skill-filer får committas när användaren ber om det).

## Källor

- [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)
- [blader/humanizer](https://github.com/blader/humanizer)
- [milock/humanizer](https://github.com/milock/humanizer)
- [brandonwise/humanizer](https://github.com/brandonwise/humanizer)
- [coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills)
- Isof: *Engelska ord på svenska*
- Isof Klarspråk: *Se upp med jargong*
- Språkbruk: *Hur ska vi hantera engelskan*
