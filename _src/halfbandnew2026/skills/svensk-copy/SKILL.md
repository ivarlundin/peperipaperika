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
- Skriv **kör** (sång), inte *kö*.
- Skriv **e-post** / *mejla* i löptext om kontakt; undvik *mail* som substantiv (*i mail*, *per mail*).
- Skriv **passar** / *fungerar*; undvik *funkar*.

### Blås och bandstorlek

Nämn trumpet och saxofon (och kör om det är relevant) i vanlig prosa. Undvik marknadsfrasen *egen blåssektion* och rubriker som bara säger *Blåssektion* eller *Egen blåssektion*.

### Förbjudna och uttjatade fraser (ersätt eller stryk)

Använd inte dessa som säljargument eller utfyllnad. Om fakta kräver bandstorlek: *åtta musiker*, *trumpet och saxofon*, *hela bandet på scen*.

| Undvik | Skriv hellre (exempel) |
|--------|-------------------------|
| egen blåssektion | trumpet och saxofon i bandet; blås på scen |
| helband / hela helbandet (som säljord) | hela bandet; alla åtta på scen |
| färdigt band / komplett liveband / fullt liveband | vi kommer som åtta musiker; bandet spelar live |
| åttamannaband (som rubrik eller USP) | åtta musiker; bandet är åtta personer |
| full bandbredd / komplett sättning | (stryk, eller beskriv vad som händer) |
| liveupplevelse / musikunderhållning (byråspråk) | livemusik; band på scen |
| levererar (musik, sväng, upplevelse) | spelar; håller igång dansgolvet |
| dynamisk blåssektion | (stryk) |
| partymusik (upprepat i varje stycke) | festmusik; dansmusik; (variera) |
| Band och … med egen blåssektion | kort fakta om ljud eller repertoar |
| Hemmaplan är … / Kärnregion: (kommauppräkning av orter) | Vi utgår från Växjö; ort i en mening om var vi spelar |

### Geografi och orter

Bandet **utgår från Växjö**. Det är utgångspunkten i löptext, inte en ort i en lång lista.

- **Undvik** stela uppräkningar i brödtext: *Hemmaplan är Växjö, Kalmar, Älmhult och Jönköping*, *Vi spelar i Växjö, Kalmar, Älmhult, Jönköping, Lund, Malmö…* som egen mening eller punktlista bara för SEO.
- **Skriv hellre** orter inbakade i meningar om erfarenhet eller resor: var ni **spelat**, **brukar spela**, eller att ni **åker från Växjö** till bröllop i Småland och Skåne, med ett eller två exempel i samma mening.
- **Meta och schema** (`areaServed`, tjänstebeskrivningar): ortnamn för sök är ok, men formulera som naturlig svenska (*bröllopsband från Växjö, spelningar i Småland och Skåne*), inte som ren keyword-rad.
- Längre ortlistor hör hemma i strukturerad data, inte som slogans i synlig copy.

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
- [ ] Geografi: utgår från Växjö; inga fria ortuppräkningar i brödtext
