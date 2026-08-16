# Mission: $0 → 1 USDC

Start: **0 USD, 0 USDC, 0 kredit.**
Mål: **1 USDC** in på en kontrollerbar plånbok, **verifierad**.

## Varför just 1 USDC

1 USDC är litet nog att vara möjligt utan kapital, och hårt nog att kräva en riktig ekonomisk loop: någon annan måste vilja ge värde, och värdet måste gå att bevisa.

USD Coin är måttenheten för att resultatet ska vara:

- stabilt (inte "jag tjänade 1 meme-coin")
- publikt verifierbart
- jämförbart över tid

## Vad som räknas

Räknas:

- Betalning i USDC (eller motsvarande som konverterats till USDC) som `verify_revenue` godkänt med bevis.

Räknas inte:

- Löften, likes, stars, "någon sa att de ska betala"
- Operatorns egna överföringar
- Fabricerade kvitton
- Intäkt på ett konto du inte kontrollerar
- Allt som kräver att operatorn lägger ut pengar

## Begränsningar

- Inget startkapital.
- Inga betalda annonser, inga betalda API:er, inga inköp.
- Inget brott, inget bedrägeri. Se `AGENTS.md`.
- Tid är tillåten. Pengar från operatorn är det inte.

## Strategi (första hypotesen)

Okänt. Agenten ska *hitta* en väg, inte anta en.

Tillåtna riktningar i grova drag:

- Skapa något någon vill ha och ta betalt i USDC
- Utföra arbete mot USDC på gratisyta
- Publicera och sälja digitalt värde utan insats

Otillåtna riktningar: allt som bryter lagen i `AGENTS.md`.

## Definition of done

```
verified_usdc >= 1.00
pending räknas inte
operator-funded räknas inte
```

När det är sant: logga lärdomen, kör `publish`, stoppa uppdraget.
