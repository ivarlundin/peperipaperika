# Svensk copy för Halv Fjorton

Använd denna skill när du skriver eller omskriver texter i `_src/halfbandnew2026/` (sidor, byggskript, meta, schema där det syns för besökaren).

## Röd tråd per sida

Varje sida ska läsa som en sammanhängande berättelse, inte som lösa block.

1. **Känsla** – vad kvällen eller behovet handlar om, utan tomma superlativ.
2. **Vad vi gör** – konkret: band, ljud, repertoar, tillval.
3. **Hur det går till** – ordning, mingel, vigsel, fest, teknik i grova drag.
4. **Trygghet** – erfarenhet, platser, vad som ingår, vad ni behöver förbereda.
5. **Kontakt** – en tydlig väg vidare (offert, kontakt), utan säljton.

Varje sektion ska knyta an till föregående. Upprepa inte samma mening i nästa rubrik.

## Språk

- Kort, grammatiskt korrekt svenska. Korta meningar. Aktiv form. Konkreta ord.
- Svensk interpunktion. Ingen tankstreck (–, —). Använd punkt eller komma i stället.
- Inga kickers (korta överrubriker ovanför huvudrubriker).
- Undvik anglicismer och svengelska när svenska finns: *evenemang/fest* före *event*, *upplägg* före *setup*, *stämning* före *vibe*, undvik *leverera upplevelse*, *skräddarsydd experience* och liknande.
- Musiktermer som *soul*, *funk*, *live* och ortnamn är ok när de är etablerade.

## Undvik AI-slop

- Inga tomma superlativ: *oförglömlig*, *magisk*, *unik*, *på riktigt*, *världsklass*.
- Inga tretalslistor av slentrian (*kvalitet, service och engagemang*).
- Inga *Oavsett om … eller …*-konstruktioner.
- Inga frågor som rubriker av vana (*Vill ni ha …?*). FAQ-rubriker ska vara påståenden eller ämnen.
- Ingen säljton, inga utrop, inga tomma löften.

## Ton

- Premium och självsäker. Bandet har heltidsjobb och jagar inte bokningar.
- Skriv som musiker som vet vad de gör, inte som en byrå som vill stänga affären.

## Fakta och begränsningar

- **Aldrig** priser, telefonnummer eller personnamn (utom på Om oss).
- Inga beskrivningsrutor eller meta-liknande informationskort i brödtexten; ingress får vara vanlig text under hero.
- Behåll verifierbara fakta (lokaler, tillval, geografier, ljud/ljus, bandstorlek) när du omskriver. Lägg inte till nya fakta utan underlag.

## Bygg och publicering

- Källtext för genererade sidor ligger i `scripts/build.py` (och ibland `*/index.html` för startsidan).
- Efter godkänd copy: uppdatera källan, kör `python3 scripts/build.py`, committa `_src/` och `testing/` tillsammans om sidan publiceras.
- När användaren ber om förslag utan publicering: leverera endast text i chat, committa inte sidändringar.

## Snabbkontroll innan leverans

- [ ] Röd tråd tydlig från första till sista stycke
- [ ] Inga tankstreck, inga förbjudna ord/fraser ovan
- [ ] Inga priser, telefon, namn (utom Om oss)
- [ ] Rubriker är påståenden, inte retoriska frågor
- [ ] Sista sektion eller CTA pekar mot kontakt/offert utan säljtryck
