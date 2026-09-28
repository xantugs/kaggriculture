# Tape-plus opening: mined spec (opening-mine workflow, 28 Sep)

Source: 1,352 recorded seats of Boey, Fourth Quadrant, 吃白饭的大肥鱼, Yizhou, THIRD FARM CLUB (20-26 Sep, replayed exactly) and
96 T7 games in their towns. Data and tools: gold/top10/research/openmine/ (extract.py, elite_days.jsonl, ours_T7_days.jsonl).

## Mined area: LAND AND CASH FLOW, days 0-12. Covers when each team buys NE, SW and SE, the cash on hand at that moment, and where the money comes from. Data: 881 recorded elite seats from 23-26 Sep (Boey 236, Fourth Quadrant 267, 吃白饭的大肥鱼 200, Yizhou 16, THIRD FARM CLUB 162) and T7 in 96 of those towns, paired with the recorded elite of the same game. Stability was checked on the 20-22 Sep seats (TFC 417, CBF 54).

KEY QUESTION: where the $2,000 for SW on day ~8.3 comes from.
It comes from the FIRST MILK DAY. Cows bought on day 0 give 6 milk each on day 8, and the elite buy SW within an hour of selling it:
- FQ: 3.6 day-0 cows, 21 milk ($2.5k) at hour 4, SW at hour 6, carry-in $18;
- TFC: 3 cows, 18 milk, SW at hour 6;
- Boey: 2.9 cows, 16 milk, SW at hour 7 (on day 9 in 25% of seats, because it buys sheep first).
CBF and Yizhou have only 2 day-0 cows. They keep the day-8 milk (12 units) overnight and buy SW on day 9 at hours 3-4 with at least $2k carried in (94% / 81% of seats).

NE follows the same pattern one step earlier. It is bought on day 6 (98-100% of seats, all teams) from the first wool of the day-0 sheep. SE is bought on day 10 from the first melon sale, but only by FQ (99%) and Yizhou (88%).

Cash at each purchase, median:
| Team | NE | SW | SE |
|---|---|---|---|
| Boey | d6.04, $1,342 | d8.33, $2,234 | (1% of seats) |
| FQ | d6.08, $1,307 | d8.25, $2,329 | d10.38, $4,899 |
| CBF | d6.17, $2,069 | d9.17, $2,510 | none |
| Yiz | d6.21, $3,083 | d9.12, $2,590 | d10.54, $5,334 |
| TFC | d6.04, $2,064 | d8.25, $2,510 | none |
| T7 | d6.25, $2,802 | d11.04, $19,210 | 15% of seats, $17.4k |

WHY THEY HAVE IT AND WE DON'T
This is a cumulative cash statement from day 0 to the elite's SW moment, in the same 94 towns (sw_moment.py).
- Cash at that moment: elite $2,640, T7 $1,589, a gap of +$1,051.
- The gap is all income:
  - fertilizer +$1,050: animal-days over days 0-8 are 54-70 for the elite against 49 for T7;
  - wool +$709: CBF/Yiz have 3 day-0 sheep;
  - eggs +$255: Boey/TFC buy 2 geese on day 2;
  - milk +$112.
- The elite do not skip anything:
  - cows and sheep: about the same spend;
  - melons: $68 less;
  - they spend more on geese (+$504), strawberries (+$237), wheat feed (+$611) and hands (+$208).
- The mechanism:
  - they put $2.2-2.6k into 5 animals on day 0 (T7: 4 animals and 12 melons);
  - FQ, Boey and TFC turn every $300-500 of fertilizer cash into an animal at once (FQ starts 97% of days 1-9 below $150; T7 starts 47% of days at $500 or more);
  - CBF and Yiz bank for a day-6 wave of 4-5 cows.

T7 is not actually short of cash. On day 8 it sells the same milk at hour 4 ($2.26k) and at that same hour buys 2 sheep (100% of towns). If the day-8 animal and seed buys waited, T7 would have $2k or more on day 8 in 100% of the 96 towns (median hour 4, peak $2.8-2.9k). The same holds on day 9 (100%, median hour 7). Its SW is late because the tape step is fixed at day 11 hour 1, not because of cash.

Cost of moving SW earlier: defer 2 sheep by about 1 day, and plant 14-18 wheat tiles plus structures in SW immediately with 1-3 extra hands. The payoff shows in wheat: the elite turn net wheat sellers from day 11-12, while T7 buys $2.2k of wheat on days 8-11. Net wheat cash on days 0-16 is FQ +$2.5k and Yiz +$1.5k against T7 -$1.2k.

Do not copy the elite's day-0 melon cut. Melons are a first-seller market, and T7's 12 day-0 melons earn $15.5-16.7k by day 12 against the elite's $9.8-13.4k in the same towns.

WHEAT TRADING
Boey (88% of seats) and FQ (100%) buy and sell the same units in the same hour: 999 and 364 wheat units, plus about 100 fertilizer units, on days 0-12. The profit is +$18 and +$4, because the engine quotes purchases at stock-1. It is churn, not a cash source. Net wheat bought is feed for every team: 47-82 units ($1.5-2.8k), T7 59 units ($2.1k). The gross figures in the first look (Boey sells $24k of wheat) are this churn.

CASH-FLOW STATEMENTS (cashflow.py, daily.py)
Days 0-8, net figures, elite range vs T7:
- fertilizer $4.5-5.4k vs $4.2k;
- wool $2.5-3.6k vs $2.4k;
- milk $2.2-3.6k vs $2.3k;
- eggs $0-0.8k vs 0;
- animals $4.9-6.4k vs $5.2k;
- seeds $3.0-4.0k vs $3.2k;
- wages $0.3-0.44k vs $0.18k;
- land $1-3k vs $1k.
From day 10 T7's melons dominate: $13.9k on day 10 alone. By day 12 T7's cash matches the elite ($18.4k vs $9.7-17.9k), but its land and herd are about 3 days behind (13.8 animals vs 15.6-18.3 on day 10; wheat tiles 5 vs 18-21).

Outcome check within teams:
- SW on day 8 vs day 9 hardly changes results: Boey 68% vs 66% wins, TFC (20-22 Sep) 51% vs 50%, CBF (20-22 Sep) day 9 vs day 11 21% vs 19%.
- So the evidence for "day 8-9 beats day 11" is across teams: T7 against these teams, plus the phase result that their day-16 farm is worth +$3.5k under our controller.
- A tape experiment is the next step: SW on day 8 at hour 4-6 or day 9 at hour 7, sheep after SW, SW filled with wheat. Nothing like it has been measured yet.

SCRIPTS, all in C:/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg/gold/top10/research/openmine/land_cash/. Run from that directory with ../../../../../../.venv/Scripts/python.exe. Nothing was committed and gold/submit was not touched.
- common.py: loader that caches days 0-16 to cache_days.pkl (61 MB, about 8 s to build); pairs() gives the T7 / recorded / repaired seat triples.
- land.py: land timing and cash before each purchase.
- cashflow.py: cumulative statements through days 5, 8 and 12, all teams and paired.
- daily.py: per-day statements.
- sw_funding.py: funding on the NE/SW/SE purchase day, and T7's first-affordable moment.
- sw_moment.py: cumulative statement to the elite's SW moment, elite vs T7.
- trigger.py: first-affordable test, and T7's potential cash on days 8-9.
- herd.py: purchases by day, herd, idle cash, fertilizer.
- shares.py: share of seats buying each item by day.
- day0.py: day-0 profile, land-day shares, outcome by SW day; `old` = 20-22 Sep.
- d8hours.py: hour of milk sale, SW buy and animal buys on days 8-9.
- trade.py: wheat and fertilizer round trips.
- sw_use.py: SW and SE contents and ops after purchase.
- fills_dump.py: hourly fills of one seat.

### Constraints
ENGINE (kaggriculture.py):
- Start with $3,000. Land is bought in a fixed order: NE $1,000, then SW $2,000, then SE $4,000. A BUY_LAND is processed before the per-unit sales that share its order index, so to use same-step cash, put the sells at a lower index.
- COOP and PASTURE are free (a BUILD_* unit action). Animals cost: goose $300, cow $400, sheep $500.
- The care bonus accumulates on every day the animal is fed and cared for. The first production consumes it, capped at max_held. So an animal bought on day X gives:
  - sheep: 6 wool on day X+6;
  - cow: 6 milk on day X+8;
  - goose: 4 eggs on day X+4, then about 2 a day.
- Every placed animal gives 1 fertilizer a day from day X+1, fed or not. Two unfed days in a row and it escapes.
- No shop buys fertilizer, so its price only falls as both farms sell ($100, then $75 by day 9).
- No shop buys melons (the town centre takes 1 a day), and the curve above I0 is quadratic. The melon market is a single dump that rewards selling first.
- A purchase is quoted at stock-1, so same-step round trips net exactly $0.
- The n-th hire of a day costs fib(n): 8 hands cost $54 a day, 9 cost $88, 10 cost $143, 11 cost $232.
- Wheat for feed costs $28-40 on days 0-12; 1 wheat per animal per day.

OUR TAPE (T7, 96 towns):
- Day 0: 2 cows + 2 sheep at hour 1 and 12 melons, about $150 left.
- 1 cow on day 2 and 1 on day 3 (the denial cows); strawberries from day 5.
- NE on day 6 at hour 6.
- 2 cows on day 7, 2 sheep on day 8 at hour 4, 1.5 sheep on day 9.
- SW is a fixed recorded step (265 = day 11 hour 1) in 100% of towns.
- The day-11 SW plan is 12.7 wheat, 10.4 strawberries and 2.6 tomatoes.

Moving SW to day 8 or 9 therefore needs two things:
(a) move the day-8 sheep after SW (or to day 9, after the wool), since the cash is there in 100% of towns;
(b) plant 14-18 wheat tiles and structures in SW right away, with 1-3 more hands on days 8-9 ($35-180 a day).

It does not require cutting the early cows, the strawberry batches, the melons or the herd. The elite have more of each of those by day 8, apart from melons (the same 10-12.5 total, but later).

Constraints carried over, still valid:
- The day 2-3 cows and the strawberry batches are denial assets.
- The 12 day-0 melons are a first-to-market asset (T7 earns +$3-6k in melons by day 12 in the same towns).
- Geese bought on controller days lose.
- Recorded routes do not transplant.

Boey caveat: its repaired tape buys SW late (day 13.9) in the T7 runs. All pairings here use the recorded Boey rows.

### Rules
- **NE purchase**: trigger: Day 6, the day the day-0 sheep give their first wool (6 units each). Cash before the buy is $1.3k for Boey/FQ, $2.1k for CBF/TFC and $3.1k for Yizhou.. Action: Sell the wool, then BUY_LAND NE in the same hour or the next one. It is the first purchase of the day.. Teams: NE on day 6 at all five teams: Boey 100%, FQ 100%, CBF 100%, Yiz 100%, TFC 98%. Median hour: Boey h1, FQ h2, TFC h1, CBF h4, Yiz h5. Bought within 1 hour of first being affordable: FQ 100%, Boey 88%. (On 20-22 Sep TFC bought NE on day 5 in 69% of seats.). Ours: T7 also buys NE on day 6 (100%), but at hour 6 after selling its wool at hour 6. It holds $2.8k before the buy, about $1.5k more than Boey/FQ, because it bought fewer animals on days 1-5.. Evidence: Every team does the same thing, so this does not open the gap. The only difference is about 5 hours. In every team the cash for NE comes from the first wool sale: $1.2k-2.4k sold that day before the buy.
- **Day-0 split between animals and melons**: trigger: Day 0, hours 0-2, starting cash $3,000.. Action: Buy 5 animals worth $2.2-2.6k: Boey 3 cows + 2 sheep, FQ 4C2S or 3C2S, TFC 3C2S, CBF/Yiz 2C3S. Plant only 5-7 melons on day 0 and the rest (10-12.5 in total by day 8) on days 1-2, paid for by fertilizer sales.. Teams: Boey 3C2S 86% (2C3S 13%), 6.9 melons on day 0, 97% plant <=7. FQ 4C2S 57% / 3C2S 43%, 5.2 melons, 57% plant <=7. TFC 3C2S 98%, 7 melons, 100%. CBF and Yiz 2C3S 100%, 6 melons on day 0 plus 4 on day 1 (100%).. Ours: 2 cows + 2 sheep at hour 1 (100%) and 12 melons on day 0 (100%). About $150 is left, so a 5th animal cannot be bought on day 0 without cutting melons.. Evidence: Engine: every day the animal is fed and cared for adds a care bonus, and the first harvest pays the whole stored bonus, capped at max_held. So a day-0 cow gives 6 milk on day 8 (about $1.0k) plus about 8 fertilizer (about $740), for $400 plus about $240 of wheat. A day-0 sheep gives 6 wool on day 6 (about $1.35k) plus 6 fertilizer, for $500. At the elite's SW moment, the same towns show elite wool +$709 over T7, fertilizer +$1,050 and eggs +$255. DO NOT COPY THE MELON CUT: no shop buys melons, so the melon price is a single dump and the first seller gets the best prices. T7's 12 day-0 melons earn $15.5-16.7k by day 12, against $9.8-13.4k for the elite in the same towns.
- **Spend fertilizer income at once on days 1-5 (FQ, Boey, TFC); bank it for a day-6 wave (CBF, Yiz)**: trigger: Days 1-5. Fertilizer is the only income (about $450-800 a day, 1 unit per animal per day, price $100 falling to $90). The trigger is cash reaching the price of the next item: goose $300, cow $400, sheep $500, strawberry seed $100.. Action: FQ/Boey/TFC buy immediately. Boey buys 2 geese on day 2, TFC 2 geese on day 2, FQ 1 sheep on day 2. Then 1 cow on day 3 or 4, and 1.5-3 strawberry seeds a day from day 1-3. CBF/Yiz put days 2-4 into 10 strawberry seeds (3+5+2), buy no animals, bank $0.5-1.1k on days 4-5, and on day 6 put the wool cash into NE plus 4.3-4.7 cows and 2-3 geese.. Teams: Day-2 geese: Boey 88%, TFC 98%. Day-2 sheep: FQ 99%. Day 3-4 cow: FQ 63%/77%, Boey 71%, TFC 73%. Share of days 1-9 starting below $150: FQ 97%, Boey 80%, TFC 42%, CBF 51%, Yiz 58%. CBF/Yiz strawberries on days 2-3 and the day-6 cow wave: 100%.. Ours: T7 buys 1 cow on day 2 and 1 on day 3 (100%), then banks. Hour-0 cash is $340 on day 3, $741 on day 4 and $846 on day 5, and 47% of days 1-9 start with $500 or more (FQ 2%, Boey 7%). Strawberries start only on day 5 (4 seeds). Animal-days over days 0-8: T7 49 against Boey 70, TFC 67, FQ 63, CBF 54, Yiz 55.. Evidence: Every $300-500 left idle is one animal fewer: about $90 a day of fertilizer, plus eggs ($100 a day per goose from day 4 after purchase) or the 6-unit first harvest. At the elite's SW moment, in the same 94 towns, fertilizer is +$1,050 and eggs +$255 over T7. The elite collect 119-140 fertilizer by day 12 against 107 for T7.
- **SW on milk day (FQ, TFC, Boey)**: trigger: Day 8, when the day-0 cows give their first milk (6 units each). The sale is at hour 3-4: FQ 21 units, TFC 17.9, Boey 16.4. Carry-in cash at hour 0 is only $18 (FQ), $582 (TFC) and $284 (Boey).. Action: Sell the milk (and that hour's fertilizer), then BUY_LAND SW in the first hour cash reaches $2,000. Cash before the buy is $2.3-2.5k. FQ and TFC buy SW at hour 6 before any animal that day. Boey does not hold cash back for it: it buys sheep at hour 5 first, so in 25% of seats SW slips to day 9 hour 1.. Teams: FQ day 8 99% (milk sold before the buy 99%). TFC day 8 100% (milk 100%). Boey day 8 67%, day 9 25%; its 8% with no SW are broken games with a -$87k margin. Bought within 1 hour of first being affordable: FQ 100%, TFC 100%, Boey 98%. On 20-22 Sep TFC was day 8 72% / day 9 27%.. Ours: T7 sells its 12 day-8 milk ($2.26k) at hour 4 too, but spends it at hour 4 on 2 sheep (100%) plus about 3 strawberry seeds. It buys SW on day 11 hour 1 (100%, a fixed tape step) with $19k. At the elite's SW hour T7 holds $1.2-1.6k, and $2k or more in only 0-6% of towns. If T7 held back that day's animal and seed buys, it would have $2k or more on day 8 in 100% of the 96 towns (median hour 4, peak $2.8-2.9k).. Evidence: Cumulative cash from day 0 to the elite's SW moment, same 94 towns: elite $2,640, T7 $1,589, a gap of $1,051. It is not from skipping anything. The elite spend about the same on cows (-$106 vs T7) and sheep, $68 less on melons, and more on geese (+$504), strawberries (+$237), wheat (+$611) and wages (+$208). The gap comes from income: fertilizer +$1,050, wool +$709, eggs +$255, milk +$112. Within teams, day 8 vs day 9 barely changes outcomes: Boey wins 68% vs 66% (+$2.6k vs -$5.0k margin), TFC on 20-22 Sep 51% vs 50%. The value is day 8-9 against day 11, which no elite seat does. The phase study found our controller earns +$3.5k more on their day-16 farm.
- **SW from banked day-8 milk (CBF, Yizhou)**: trigger: Day 9, hours 3-4. Hour-0 cash is already at least $2k (CBF $2,729, Yiz $2,125): they kept the day-8 milk (12 units at hour 1) and bought almost nothing on day 8.. Action: Sell the day-9 wool at hour 3-4, BUY_LAND SW in the same hour, then buy animals at hour 5 (geese, cows).. Teams: SW on day 9: CBF 100%, Yiz 100%. Hour-0 cash of $2k or more: CBF 94%, Yiz 81%. They could already afford it on day 8 but wait a median 15-18 hours. On 20-22 Sep CBF was day 9 61% / day 11 39%, so it is moving earlier.. Ours: On day 9 T7 buys 1.5 sheep at hour 1 (100%) and sells wool at hour 7. Without that day's animal and seed buys it would have $2k or more on day 9 in 100% of towns (median hour 7). Actual day-9 closing cash is $2.2-2.7k and is not spent on land.. Evidence: A simpler route than milk day: same herd as T7 (2 cows + 3 sheep), SW one day later. Wins in the recordings: CBF 32%, Yiz 12% (strong opponents). T7 only wins 6/20 and 7/16 against them, so their day 9-16 farm is worth having.
- **What goes into SW in the first 3 days**: trigger: The SW purchase day and the next 2 days.. Action: Plant 14.6-17.8 wheat tiles as a feed farm and fertilize 2-4 of them. Build 2-5 free structures and place that day's animals in them: Boey 1.9 geese + 1.1 cows + 0.9 sheep, FQ 2.4 cows + 2.4 sheep, CBF 3.2 geese + 1.5 cows, TFC 1.6 geese + 1.1 cows. Add 1-7 strawberries (Yiz: 5.9 tomatoes). Hire 9-11 hands that day (wages $88-232).. Teams: Wheat is 12-15 tiles of SW one day after purchase at all five teams, 100% of teams. Hands on day 8-9: Boey 9.6/10.0, FQ 10.2/10.1, TFC 10.7/10.0, CBF 9/11, Yiz 9/10.1.. Ours: T7 fills SW on day 11: 12.7 wheat, 10.4 strawberries, 2.6 tomatoes, no structures. It hires 8.2 hands on days 8-9. Wheat tiles at hour 0 on day 10: T7 5, elite 18-21.. Evidence: The elite switch to net wheat selling on day 11-12 (+$450-1,200 a day on days 12-16). T7 buys $602, $397, $822 and $373 of wheat on days 8-11 ($2.2k in total) and only sells $190-480 a day from day 12. Net wheat cash, days 0-16: FQ +$2.5k, Yiz +$1.5k, T7 -$1.2k.
- **SE right after the first melon sale (FQ, Yizhou only)**: trigger: Day 10, first melon harvest sale (FQ $7.6k, Yiz $8.1k). Cash before the buy is $4.9k (FQ) and $5.3k (Yiz).. Action: BUY_LAND SE at hour 9 (FQ) or hour 13 (Yiz), then plant 13-19 wheat tiles and 2-5 carrots in it within 2 days.. Teams: FQ day 10 99%, 94% within 1 hour of first being affordable. Yiz day 10 88%. Boey 1%, CBF 0%, TFC 0% (none before day 16).. Ours: T7 buys SE in 15% of seats (day 12 10%, day 16 3%), despite holding $16-20k from day 10.. Evidence: Weak and mixed. FQ is T7's worst matchup (0/20, -$12.3k) and is the only team with SE on day 10 every game. The other three strong teams skip it. This is a controller-day decision (days 10-12), outside the tape.
- **Wheat and fertilizer churn: do NOT copy**: trigger: Any hour on days 0-12, Boey and FQ.. Action: Buy and sell the same wheat and fertilizer units in the same hour at the same price.. Teams: Seats with 20 or more same-hour round-trip units: Boey 88%, FQ 100%, others 0%. Days 0-12: Boey buys 1,388 and sells 1,307 wheat (999 round-tripped in the same hour) and round-trips 97 fertilizer. FQ round-trips 364 wheat and 110 fertilizer.. Ours: T7 8% of seats, 22.6 wheat units. Net wheat bought on days 0-12: T7 59 units ($2.1k), elite 47-82 units ($1.5-2.8k).. Evidence: The engine quotes a purchase at the post-purchase stock level, so a round trip nets exactly $0. The same-hour round-trip profit over days 0-12 is +$18 for Boey, +$4 for FQ and $0.4-2 on fertilizer. Wheat is feed only, not a cash source, and the gross numbers in the earlier first look overstated it.
- **Selling fertilizer**: trigger: Every day, as soon as it is collected (one unit per animal per day, available from the day after placement).. Action: Sell everything collected in the same day. Only 2-23 units per seat are used on crops by day 12 (wheat in SW/SE).. Teams: All teams sell what they collect (net sold 90-118 units by day 12). The price falls from $100 on day 0 to about $75 on day 9 and $66 on day 11, because no shop buys fertilizer and both farms sell it.. Ours: Same policy: 90 net units sold, none used. T7 collects less (107 by day 12 against 119-140) because it has fewer animal-days.. Evidence: Fertilizer is 100% of income on days 1-5 and the largest single source up to day 9. By day 8: Boey $8.9k gross ($5.4k net of churn), FQ $7.6k ($5.2k net), TFC $5.3k, CBF $4.8k, Yiz $4.5k, T7 $4.4k gross / $4.2k net.

## Mined area: HERD: animals by kind and day (buys, placements, coops and pastures), conditional on the buyers known and on land; geese; cows and sheep by days 6/9/12/16; feed source and cost; denial cows; what our T7 tape does in the same towns. Data: 1,352 recorded elite seats (rules use 23-26 Sep: Boey 236, FQ 267, CBF 200, Yiz 16, TFC 162) plus T7 against them (96 seats, same towns).

Short names: FQ = Fourth Quadrant, CBF = 吃白饭的大肥鱼, Yiz = Yizhou, TFC = THIRD FARM CLUB. Seat counts: Boey has 207 current seats; a 29-seat Boey variant from 23-24 Sep (2C3S on day 0, no early geese) won 0 of 29 and is left out of the Boey rules. G/C/S = geese/cows/sheep, 3C2S = 3 cows + 2 sheep, P = the day an animal is placed.

Scripts are in gold/top10/research/openmine/herd/ (compact.py builds compact.jsonl; lib.py is shared).

1. There are two opening types.

- **Herd-first (Boey, FQ, TFC):** 5-6 animals on day 0. They reinvest every hour from day 2 by selling fertilizer and wheat and buying in the same market queue, keeping under $100 idle. Boey and TFC buy 2 geese on day 2 before any shop is known. All three buy 2-4 cows on days 3-5 when the first shop buys milk, and sheep only once a yarn store is known. They own 8.8-10.1 animals at day 6, against T7's 6.
- **Strawberry-first (CBF, Yiz):** 2C3S on day 0, nothing on days 1-5 (the cash goes into 8-10 strawberry tiles), then a wave on day 6 funded by 18 wool: NE, 4-7 cows and 1-3 geese. Then geese on days 9-11.
- **Both converge** on about 20 animals by day 12 and then stop buying. By day 12 the geese are 4-8 depending on egg buyers (FQ has none), against T7's 1.4-2.9.

2. Where the early cash for SW comes from: the herd, not savings.

- Each day-0 cow delivers a batch of 6 milk on day 8, because the care bonus builds up until then.
- FQ, TFC and Boey sell that milk ($2.0-2.5k before the SW hour) and buy SW in the same hour on day 8 (99%, 100% and 76% of seats). SW timing tracks the day-0 cow count: Boey with 3 cows buys by day 8 in 76%, the old 2-cow Boey only 6%.
- CBF and Yiz, with 2 day-0cows, bank the day-8 milk and buy SW on day 9.
- T7 has only 2 day-0 cows and spends its $2.26k of day-8 milk on 2 no-yarn sheep plus wheat and seeds. Even so, it holds $2,000 or more by the end of day 9 in 62% of seats, yet the tape waits until day 11 at hour 1.

3. Denial: the herd-first elite hold as many early cows as our tape or more (4.4-5.3 at day 6 vs 4.0), so our early milk is not unique. CBF and Yiz do not buy early cows (2.0 until day 6).

4. Geese: eggs are the only herd product whose price does not depend on the shops ($42-50 with 0-3 egg buyers). Milk and wool fall to $4-22 after day 16 where no shop buys them. That is why geese are bought before shops appear and in every town. T7's egg revenue trails the elite by $1.5k on days 0-15 and $2.3-4.7k on days 16-29 in the same towns.

5. Sheep: the elite buy sheep only when a yarn store is known (100% of seats with yarn; 8-68% buy any without). T7 buys 3.7 sheep on days 8-9 in 100% of no-yarn towns.

6. Feed is not a constraint for anyone: about half is bought wheat at $28-41 on days 0-11, and SW wheat covers it from day 12. The elite feed cows and sheep only 60-76% of late-game days and let the herd escape in the last week; our late upkeep is already fine.

7. Tape edits suggested by the data, not yet tested, cheapest first:

- **(a) Buy SW as soon as cash stays at $2,000 or more after the day's tape purchases.** That is day 9 end or day 10 hour 0 in 62% of seats, instead of day 11 hour 1. No herd change needed.
- **(b) Spend the idle day-4/5 cash on 1-2 geese.** Build the coops on NW wheat tiles; hour-0 cash is $340-741 on those days. Rough ledger: +$1.0-2.0k each by day 29.
- **(c) Day 0 3C2S with 7 melons; the day-2 cow slot buys the 5 melons instead.** This gives 18 milk on day 8 and makes SW on day 8 affordable.
- **(d) In no-yarn towns, put the day-8 sheep money into SW on day 8.** This differs from the rejected sheep-to-geese swap.

8. Caveats:

- A Boey variant from 23-24 Sep (2C3S, no early geese; 29 seats, 0 wins, margin -$77k) is left out of the Boey rules.
- TFC changed version on 22 Sep: day-2 geese appear from then on.

Scripts are in C:/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg/gold/top10/research/openmine/herd/. compact.py builds the compact per-seat table compact.jsonl (63 MB) and lib.py holds the shared helpers. The analysis scripts are timeline.py, buys.py, seq.py, bydate.py, cond.py, herd_by_shops.py, rival.py, cashrule.py, spend.py, tiles.py, feed.py, fert.py, yieldk.py, px.py, realized.py (per-animal ledger), eggpx.py, paired.py (T7 vs the recorded elite in the same towns), swfund.py, swcows.py, t7cash.py, t7var.py and natexp.py.

Nothing was committed and gold/submit/ was not touched.

### Constraints
ENGINE (kaggriculture.py): goose $300 on a COOP, cow $400 and sheep $500 on a PASTURE, one tile each; building a structure is a free unit action. Base yield continues when an animal is unfed. The care bonus (+1 for each day fed and cared) is paid only on a fed production day and is capped at max_held. So the first batch is 4 eggs at P+4, 6 wool at P+6 and 6 milk at P+8; after that 2 eggs a day, 4 wool every 3 days, 3 milk every 2 days. Every animal gives 1 fertilizer a day, fed or not, from the day after placement. Two unfed days in a row and the animal escapes.

Fertilizer has no shop or town demand, so its price only falls as both farms sell: realized $100 on day 0, $75 on day 9, $43 on day 16, $11 on day 29. Fertilizer is early cash and is worth little late. The egg price barely moves (T=332, log above I0). Milk and wool crash where no shop buys them.

Shops unlock at the start of days 3, 6, 9, 12 and so on: nothing is known on days 0-2, 1 shop on days 3-5, 2 on days 6-8, 3 on days 9-11. The rival's herd barely changes elite buys (FQ buys 4.4 vs 5.7 cows on days 6-9 when the rival has more); the known shops drive everything.

CASH: T7's day 0 is fully spent ($11 left), so a 5th day-0 animal means moving about 5 melon seeds to days 1-2, as the elite do (5-7 melons on day 0, about 10 by day 3). The tape's day-2/3 cows are denial and stay. Day-2 geese need about $600 on day 2, which T7 spends on its day-2 cow. T7's idle cash on days 4-5 ($340-741 at hour 0) fits 1-2 geese, and T7 already holds $2,000 by the end of day 9 in 62% of seats.

TILES: T7's NW at day 1 is 12 melons, 8 wheat, 4 pastures and 1 free tile. The elite turn early-harvested day-0 wheat tiles into coops: TFC's NW is 12.9 wheat and 7 melons at day 1, then 2 geese, 9.9 melons and 8.1 wheat at day 3.

LABOUR: each animal needs 3-4 unit actions a day (FEED, CARE, COLLECT, HARVEST), paid at Fibonacci wages.

KNOWN REJECTIONS still apply: geese bought on controller days (13+); swapping the day-8/9 sheep for geese outside never-yarn towns; dropping the early cows. The ledger values in the rules are rough upper bounds: realized average prices, no price impact of the extra units, no labour or tile cost.

### Rules
- **Day-0 herd size and composition (and how much melon seed on day 0)**: trigger: Day 0, hours 0-2, $3,000 cash, no shops known.. Action: Buy 5 animals ($2,200-2,430) and build one pasture for each that day: Boey and TFC 3C2S; CBF and Yiz 2C3S; FQ 3-4 cows + 2 sheep. Buy only 5-7 melon seeds on day 0 ($410-560). The rest of the ~10 melons are bought on days 1-3 with fertilizer money (Boey buys melon seed on days 1-2, TFC on day 2, FQ on days 1-3).. Teams: 100% of seats in all five teams have at least 5 animals on day 0. Boey (current) 3C2S 99%. FQ 4C2S 57%, 3C2S 43%. CBF and Yiz 2C3S 100%. TFC 3C2S 98%.. Ours: T7 buys 2C2S in 100% of seats ($1,800) plus 12 melon seeds on day 0 ($960), and ends day 0 with $11.. Evidence: The first batch is large because the care bonus builds up until the animal first produces, capped at max_held. A day-0 sheep gives 6 wool on day 6 (about $1.2k at $202). A day-0 cow gives 6 milk on day 8 (about $1.05k at $176). Every animal also gives 1 fertilizer a day from day 1, worth $100 falling to $75 by day 9. In the same towns, CBF and Yiz (3 day-0 sheep) sell $3.4k of wool on days 0-7 against T7's $2.3k. Rough ledger (herd/realized.py; realized prices, no labour, no price impact): a cow bought on day 0 is worth +$2,980 by day 16, one bought on day 2 +$2,258.
- **SW land: when to buy it and what pays for it (the key open question)**: trigger: Day 8, hours 5-7. The day-0 cows' first milk batch is ready (6 per cow). Hour-0 cash is $0-600.. Action: Harvest and sell that milk, plus the day's fertilizer and wheat, and BUY_LAND SW in the same hour before buying any animal. Teams with only 2 day-0 cows (CBF, Yiz) buy no animals on days 1-5 and sell the day-8 milk into savings. They start day 9 with $2.1-2.7k and buy SW at hours 3-4.. Teams: FQ buys SW on day 8 in 99% of seats (17.7-23.9 milk harvested on day 8). TFC 100% on day 8 (18 milk). Boey with 3 day-0 cows: 76% on day 8, 100% by day 9. CBF and Yiz 100% on day 9. Old Boey with 2 cows: 6% by day 8, 35% by day 9. Milk sold before the SW hour: FQ $2,495, TFC $2,290, Boey $1,981. Cash just before SW: $2.35-2.53k. Script: herd/swfund.py, herd/swcows.py.. Ours: T7 sells 12 milk on day 8 ($2,263). It then spends $1,000 on 2 sheep (no yarn store known in 80% of towns) and about $1k on wheat and seeds, and buys SW on day 11 at hour 1 with $19k of melon cash. Yet T7 ends day 9 with at least $2,000 in 62% of seats (median $2,204 at day-10 hour 0) and reaches $2,000 during day 9 in 81%. On day 8, 34% reach it during the day, and nearly all would if the day-8 no-yarn sheep were skipped ($452 + $2,263 milk + $817 fertilizer). Script: herd/t7cash.py.. Evidence: The elite answer to 'where does the $2,000 come from' is the herd: 3-4 day-0 cows produce 18-24 milk on day 8, worth $3.0-4.0k, sold the same morning. It is not idle savings (FQ starts day 8 with $17 on average). T7's 2 day-0 cows give $2.26k, and it spends that on sheep.
- **Geese before any shop is known (day 2)**: trigger: Day 2, no shops known. The wheat tiles planted on day 0 are harvested early, at age 2, which frees NW tiles. Cash after the day's fertilizer and wheat sales is at least $300.. Action: Build a COOP on a freed NW wheat tile and buy a goose each time cash reaches $300. That makes 2 geese: Boey buys at hours 2-7, TFC at hour 8 and hour 15. More geese follow on days 6-9 (see the geese rule below).. Teams: Boey (current) 2 geese on day 2 in 99% of seats, 100% by day 3. TFC 1.95 per seat in 98% (their version since 22 Sep; the 20-21 Sep TFC had none). FQ, CBF and Yiz 0%. Instead, FQ buys 1 sheep on day 2 in 99%.. Ours: No geese before day 6 in 100% of seats. Day-6 geese come only in towns with 2 egg buyers. First geese on days 10-11 in 66%. Geese owned at day 9 in the same towns: T7 0.3 vs Boey 3.6, T7 0.3 vs TFC 3.5.. Evidence: Eggs are the only herd product whose price does not depend on the shops. Realized egg price is $46-50 on days 6-15 and $42-47 on days 16-29, whether the town has 0 or 3 egg buyers. In towns with no buyer, milk sells at $4-22 and wool at $4 after day 16 (herd/eggpx.py). A goose gives 4 eggs on day P+4, then 2 a day, plus 1 fertilizer a day. Rough ledger: a goose bought on day 2 is worth $1,344 by day 16 and $2,404 by day 29; one bought on day 11 is worth $7 and $1,067. Egg revenue in the same towns: days 0-15, T7 $357 vs elite $1,830; days 16-29, T7 $3.5k vs $5.8k (-$2.3k to -$4.7k in Boey, CBF, Yiz and TFC towns). Weak within-team check: against the 10 opponents TFC met with both versions, its margin was +$51 with day-2 geese and -$1,643 without.
- **Idle cash on days 2-9: reinvest every hour (sell, then buy)**: trigger: Any hour of days 2-9 in which the cash seen at the start of the hour, plus that hour's sales (fertilizer, wheat, later wool and milk), covers the next animal ($300, $400 or $500).. Action: In the same market queue, SELL the collected fertilizer and wheat, then BUY_ANIMAL, leaving less than $100. The kind follows the shops known: a goose if none, a cow if a milk buyer is known, a sheep if a yarn store is known. Build the coop or pasture that day.. Teams: Boey sells in the same hour in 94-95% of its animal-buy hours on days 3-5, with a median $65-83 left afterwards. FQ 100%, $15-31 left. TFC 100%, $25-63 left. Share of hours 0-20 on days 2-9 where at least $300 sits unspent and no animal is bought later that day: Boey 9%, FQ 9%, TFC 23%. CBF and Yiz 32-36%, because they save on purpose for day 6. Mean cash held on days 2-9: Boey $179, FQ $143, TFC $338. Script: herd/cashrule.py.. Ours: T7 has 57% such idle hours and holds $814 on average. Hour-0 cash is $340 on day 4, $741 on day 5, $846 on day 6 and $1,099 on day 7. It buys no animals on days 4-5 (only $400 of strawberry seed on day 5) and keeps $130-1,480 after each animal purchase.. Evidence: The herd-first teams own 8.8-10.1 animals at day 6 against T7's 6.0. They collect 78-88 fertilizer by day 9 against 61 (net fertilizer $5.8-6.7k vs $5.2k). All teams sell their fertilizer on days 0-9 and use none on crops until day 10. Net herd revenue in the same towns: days 0-7, elite $7.5k vs T7 $5.8k; days 8-15, $22.7k vs $21.7k; days 16-29, T7 leads, $31.9k vs $29.8k (our late game).
- **Early cows on days 3-5 (the denial question)**: trigger: Days 3-5: the first shop has just appeared. Is it a milk buyer (PIZZA_SHOP, ICE_CREAM_SHOP or SMOOTHIE_SHOP)?. Action: If a milk buyer is known, buy 2-4 cows: Boey 3.6, FQ 3.0, TFC 2.0 per seat. If not, buy about 1 (0.7-1.1). CBF and Yiz buy no cows before day 6, then 4-7 at once.. Teams: With a milk buyer known: Boey 100%, FQ 100%, TFC 97% of seats buy. Without: 74%, 69% and 75% still buy at least 1 cow. CBF and Yiz 0%.. Ours: T7 buys 1 cow on day 2 (hour 17) and 1 on day 3 (hour 16) in 100% of towns, whatever the shops. Cows owned at day 6: T7 4.0. Boey 4.9 (3.8, 5.2 and 6.5 with 0, 1 and 2 milk buyers known), FQ 5.3, TFC 4.4, CBF and Yiz 2.0.. Evidence: Answer on denial: the herd-first elite (Boey, FQ, TFC) own as many early cows as our tape or more (3-4 on day 0, plus 1-4 on days 3-5), so their early milk volume is equal or larger. CBF and Yiz leave the early milk market alone until day 6. Cows grow with milk buyers: owned at day 12 with 2+ buyers, Boey 9.4, FQ 11.4, CBF 10.4, Yiz 11.4, TFC 8.3, T7 8.9. Milk in towns with no milk buyer sells at $94 on days 6-15 and $4 on days 16-29.
- **Sheep only when a yarn store is known**: trigger: YARN_STORE among the known shops (day 3 onward). No yarn store is known on days 6-9 in 70-80% of towns.. Action: Yarn store known: buy 3-5 sheep per two-day window (days 3-5: 2.3-3.0; days 6-7: 2.4-4.3; days 8-9: 3.4-5.1), reaching 10-11 sheep by days 12-16. No yarn store known: keep only the 2-3 day-0 sheep, plus 0.2-1.6 on days 8-9. If a yarn store appears later, buy sheep then (0.8-4.1 per seat on days 10-15).. Teams: Yarn store known: 100% of Boey, FQ, TFC and CBF seats buy sheep on days 6-9. No yarn store known, share buying any sheep on days 8-9: Boey 28%, FQ 68%, TFC 34%, CBF 8%, Yiz 14%. Sheep owned at day 12 without / with yarn: Boey 2.9 / 10.3, FQ 4.6 / 10.2, CBF 3.4 / 9.1, TFC 3.4 / 10.2.. Ours: T7 buys 2 sheep on day 8 in 100% of towns and 1-2 more on day 9, whether or not a yarn store is known. Without yarn, T7 owns 5.6 sheep at days 12-16, against the elite's 2.9-4.6. With yarn, 9.1 against 10.2-10.9.. Evidence: Realized wool price where no yarn store ever appears: $131 on days 6-15, $4 on days 16-29. With one store: $171 and $78. With two: $197 and $139. Known constraint: swapping the day-8/9 sheep for geese pays only in towns that never get a yarn store. The elite put that money into SW on day 8 and into geese instead.
- **Geese on days 6-11, scaled by egg buyers but never zero**: trigger: Days 6-11 (NE bought on day 6, SW on day 8-9). Egg buyers known (BAKERY, BRUNCH_SPOT): 0, 1 or 2+.. Action: Buy geese in every town, about +1.5 per known egg buyer, placed in NE and then SW. Geese owned at day 12 with 0 / 1 / 2+ egg buyers: Boey 5.0 / 5.7 / 7.3, CBF 4.1 / 5.8 / 7.1, Yiz 3.7 / 6.9 / 8.5, TFC 3.8 / 5.2 / 6.8.. Teams: Buy geese on days 6-11: Boey 100%, CBF 99%, Yiz 100%, TFC 100% of seats. FQ never buys a goose (0% of 267 seats); it runs cows and sheep only. Geese bought on days 6-7 with 0 / 1 / 2 egg buyers known: Boey 1.1 / 1.9 / 4.5, CBF 0.9 / 2.0 / 3.0, TFC 0.5 / 1.3 / 2.6. Days 8-9 with no egg buyer known: 1.1-1.9 geese (46-100% of seats).. Ours: T7 on days 6-7: 0 / 0.6 / 2.0 geese (G2 only in egg-rich towns). Days 8-9: 0. Days 10-11: 2-3 geese in 66% of towns. Owned at day 12: 1.4 / 2.6 / 2.9.. Evidence: The egg price does not depend on egg buyers (see the day-2 geese rule). The ledger gives about $165 a day of value lost for each day a goose purchase is delayed, up to day 16. Our controller should keep refusing geese from day 13 on (known result).
- **Strawberry-first archetype: the day-6 wave (CBF, Yiz)**: trigger: Day 6: the 3 day-0 sheep have produced 18 wool (about $3.4k, sold at hours 0-5), $0.8-1.1k was saved on days 4-5, and the cash of days 1-4 went into 8-10 strawberry tiles.. Action: Buy NE, then 4-7 cows at hours 5-8 (4.4 / 5.5 / 7.1 with 0 / 1 / 2 milk buyers known), 1-3 geese depending on egg buyers, and 4 sheep only if a yarn store is known. Then about 2 cows and 2-3 geese on day 9 (after SW), and 2-3 geese on days 10-11.. Teams: CBF 100% and Yiz 100% of seats buy cows on days 6-7 (5.3 and 5.1 per seat).. Ours: T7 on day 6: NE, 2 animals (C2, G2 or S2 by town type) and strawberries. Day 7: 2 cows.. Evidence: Cows owned at day 9 in the same towns: CBF/Yiz 7.6-7.9 vs T7 7.1. Their early herd is small (5 animals until day 6) and pays for itself with 3 wool batches and fertilizer. Against T7 they win on geese (6.2-6.9 at day 12 vs 2.4-2.9) and on eggs.
- **Stop growing the herd at about day 12**: trigger: Day 12 or later, after SW/SE and the melon and strawberry cash have arrived.. Action: Freeze the herd at 17-22 animals. Buy under 1 animal per seat on days 12-15 (except sheep in yarn towns, 1-2.7) and 0.1-1.3 after day 16. Build coops and pastures on the day of each purchase.. Teams: All five teams. Herd at day 16: Boey 20.3, FQ 17.2, CBF 22.0, Yiz 21.6, TFC 20.0.. Ours: T7 has 17.2 at day 16 (2.3 geese, 7.8 cows, 7.1 sheep) and freezes the same way. It builds 5 NE pastures on day 6 that stay empty until days 7-9, and still has 0.8 empty coops at day 12.. Evidence: The composition at day 16, not the size, is the gap: T7 is 3-4 geese short in every town except FQ's, and 1-3 cows short in towns with several milk buyers.
- **Feed source and cost; late-game upkeep**: trigger: Every day, for each placed animal.. Action: Days 0-11: feed and care every animal every day (feed ops 95-127% of the herd counted at hour 0, because animals placed that day are fed too). About half of the feed is net wheat purchases at $28-41 (48-93 units, $1.6-3.2k per seat). The rest comes from the 9-13 wheat tiles planted on day 0 and harvested at age 2-3. From day 12, SW wheat makes every team self-sufficient and a net seller. Days 16-28: feed cows and sheep on only 60-76% of days (base yield needs no feed, and feeding every other day prevents escapes at a smaller care bonus), geese on 82-96%. In days 23-29, let 5.7-8.4 animals escape.. Teams: All five teams. Boey and FQ also buy and resell large amounts of wheat and fertilizer: Boey buys 1,737 and sells 1,701 wheat on days 0-15, and buys $15.9k of fertilizer against $26.4k sold. This turnover is not needed for the herd.. Ours: Same feed sourcing: 66 wheat bought net on days 0-11 ($2.4k). Late, T7 feeds more (cows 83%, geese 99%) and loses 4.0 animals on days 23-29.. Evidence: Feed is about $30-40 per animal-day early, against $170-200 a day of eggs plus fertilizer for a goose, and more for cows and sheep in towns with buyers. It never limits the elite's herd.

## Mined area: LABOUR, days 0-16: hires and wages by day, hands per day, what the hands do, idle turns, tiles and animals per hand, how ~10 hands are run on days 9-10, compared with our tape (T7) in the same towns

DATA. The 23-26 Sep elite seats (FQ 267, Boey 236, TFC 162, 吃白饭 200, Yizhou 16) are compared with T7 on its 96 seats. T7's opponents are the repaired elite in the same towns. On the 96 paired games the elite numbers match the all-seat numbers within ~0.3 hires per day. Hourly replays: 176 elite seats (40 per team) and 60 T7 seats; every recorded replay reproduced its rewards.

1. Labour is not what limits our opening, and the wage never 'blows up' at ~10 hands.
- Hires by day, days 0-10:
  - FQ: 4.1 / 5.2 / 5.6 / 6.5 / 5.9 / 6.0 / 8.5 / 7.7 / 10.2 / 10.1 / 12.2
  - Boey: 4.9 / 2.7 / 5.1 / 5.2 / 5.7 / 5.2 / 9.4 / 6.6 / 9.6 / 10.0 / 11.5
  - TFC: 5.0 / 1.1 / 5 / 5 / 5 / 5 / 9.4 / 7.1 / 10.7 / 10.0 / 11.3
  - 吃白饭 and Yizhou: 4 / 4 / 6 / 6 / 6 / 6 / 8 / 9 / 9 / 11 / 10-11
  - T7: 5 / 3 / 4 / 5 / 4 / 4 / 7.2 / 7.2 / 8.2 / 8.2 / 11.0
- Days 11-16: the elite run 9-12 hands a day, T7 9-10.
- Wages:
  - Days 0-9: elite $445-601 against T7 $245.
  - Days 0-15: elite $1.45-2.7k against T7 $1.1k, which is 1.5-4.3% of sales (T7 2.1%).
- 10 hands cost $143 a day and 12 cost $376. The elite stop at 12: only 0.6-8.5% of seat-days on days 6-16 reach 13+.
- Per-unit productivity is the same for everyone:
  - Median effective actions per unit-day on days 8-10: elite 11.0-11.8 (吃白饭 9.4), T7 11.0.
  - Loads per unit on day 9: elite 4.0-5.2 tiles and 1.25-1.35 animals, T7 4.0 tiles and 1.3 animals.
  - The elite crew model (hires = 3.3 + 0.045 tiles + 0.18 animals + 0.38 animals in shed + 0.13 plantings/builds, clipped to 4-12; 82-97% of seat-days within +-1) predicts T7's own hires within about 1.
- So the elite's extra 8-14 hand-days over days 0-9 simply staff their larger plan: earlier NE/SW, 18-21 NE plantings, 11-18 SW plantings on the purchase day, and a faster herd. Labour does not buy an edge on its own. Their opening is transplantable without a labour redesign as long as crews scale with the plan.

2. How the ~10-hand days are run.
- All hands are hired at hours 0-1 (at least 97% of hires), 8-9 at hour 0 plus the overflow at hour 1. The binding limit is the 10-order hour-0 list, not the wage: FQ, Boey and TFC fill all 10 slots on 95-100% of seat-days on days 8-10.
- Land days are pre-staffed at hour 0, before the land is bought:
  - NE on day 6 at h1.4-2: 8.5-9.4 hands.
  - SW on day 8-9 at h2-7: 10-11 hands.
  - The new quadrant is planted the same afternoon.
- Hands work the whole day: first effective action at hour 2-3, last at 21-23, and only 7-11% of hand-turns come after a hand's last effective action.
- Effective actions on days 8-10 split roughly: animal chores (FEED, CARE, COLLECT, harvest) 35-45%, watering 30-40%, planting and building 10-15%, shed trips about 12%.
- Every animal is fed, cared for and has its fertilizer collected daily: 80-105% coverage (T7 the same).
- Boey and TFC (23-26 Sep) hire 2-4 fewer on the day after a planting day and skip watering that yields nothing (age-1 wheat, melons below age 6). T7 overwaters on days 1, 3, 5 and 7, about 35 actions, which is worth nothing.

3. Link to the cash question.
- FQ and Boey start 46-56% of days 1-10 with about $10-13 and pay the day's wage from same-turn hour-0 sales placed ahead of the hires: FQ $157 (fertilizer $91, wheat $65) and Boey $253 (fertilizer $200) against a $54 wage. Labour needs no cash reserve; all carried-over cash goes to land and animals.
- T7 never does this (1 seat-day in 960): it holds $200-1,450 at hour 0 on days 3-9, and its hour-0 list has spare slots (7.2-9.2 orders on days 6-9).

4. For an elite-style opening in our agent:
- Size crews with the crew model, or equivalently about 11 effective actions per unit on days 6-10 and about 12.5 on days 11-16.
- Cap the crew at 12.
- Order the hour-0 list as sales (fertilizer, wheat), then 8-9 hires, then the rest at hour 1.
- Pre-hire at hour 0 on land days: NE 8.5-9.4, SW 10-11.
- Days 2-5: 5-6 hands only if the herd grows at elite speed.
- The labour cost of adopting their opening is about +$200-350 over days 0-9 and about +$350-1,600 over days 0-15.
- Robustness: on 20-22 Sep, TFC and 吃白饭 hire at the same levels (TFC days 8-10: 11.0 / 10.9 / 12.6) but without the skip-day dips.

FILES. All in C:/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg/gold/top10/research/openmine/labour/. Run from that directory with ../../../../../../.venv/Scripts/python.exe.
- compact.py: builds rows.pkl, the detail rows d<=16 of elite, ours and rep.
- common.py: loaders, verb categories, the labour() split into effective / move / pass / fail / unsent, and plain least squares (the venv has no numpy).
- ana_days.py [T7pair]: day-by-day tables of hires, wages, hire hours, hand-turns, effective / move / idle shares, tiles and animals per hand, m0.
- ana_verbs.py: verbs by day, idle breakdown, watering coverage, hire distribution and cap, hour-0 funding, hour-0 order-slot use.
- ana_land.py: NE and SW land-day crews and same-day plantings.
- ana_totals.py: totals for days 0-9 and 0-15, effective actions per unit-day.
- ana_water.py: watering coverage by crop, animal care coverage, odd/even rhythm.
- ana_fit.py: the crew model per team and pooled, applied to T7.
- ana_rules.py [T7pair]: share of seats following each rule.
- ana_h0.py: hour-0 sales mix funding the wage, crops planted on land days.
- hourly.py: hourly replays (elite N per team, or ours with cand and N per team); outputs hourly_elite.jsonl and hourly_ours.jsonl with logs.
- ana_hourly.py: hour-block utilisation, first and last effective hour per hand, tail idle.

Nothing committed; gold/submit/ untouched.

### Constraints
- Wage: the n-th hire of a day costs fib(n-1): 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377. Day totals: 8 hands $54, 9 $88, 10 $143, 11 $232, 12 $376, 13 $609, 14 $986. Hands vanish at the end of the day and the hire count resets, so hires = hands.
- A HIRE is one market order. At most 10 orders per player per turn; extra orders are dropped silently (maxMarketOrdersPerTurn = 10).
- Orders run index by index. A HIRE fails silently if cash is below its cost at its index. A SELL at a lower index funds a HIRE at a higher index in the same turn, which is how the elite start days with $10 and still hire 8-9.
- A hand hired at hour h acts from h+1 (23 turns if hired at hour 0) and spawns at a shed-access tile. One action per unit per turn.
- Plants: planting day counts as unwatered, so a crop must be watered the day it is planted. It dies after 2 consecutive unwatered days.
- Watering pays only inside the yield window: wheat ages 2-4, carrot 2-3, melon 6-12. Strawberries and tomatoes produce without water; their fertilizer bonus needs water on the production day.
- Animals escape after 2 consecutive unfed days. FEED needs wheat in the unit's own inventory, hence the PICKUP trips.
- Care bonus: +1 unit per fed-and-cared day, paid on the next fed production day. Fertilizer is collectable every day.
- The shed holds 100 items.
- Our tape (days 0-15) is fixed. The controller takes over from day 16 (day 12 in strawberry-rich towns, day 20 against copies).
- Known from earlier research: geese bought on controller days lose to wages and $40 wheat.

### Rules
- **How many hands to hire each day, days 2-16 (the crew-size rule)**: trigger: Hour 0 of each day. Inputs visible then: crop tiles, placed animals, animals waiting in the shed, and the plantings and builds planned for today.. Action: hires = clip(round(3.3 + 0.045*tiles + 0.18*animals + 0.38*animals in shed + 0.13*(plantings+builds today)), 4, 12). This is an OLS fit pooled over FQ, Boey and TFC, days 2-16. Put another way, each unit (farmer plus hands) is planned at about 11 effective actions a day on days 8-10 and 12.5 on days 11-15. A hand makes about 11 effective actions and about 10 moves in its 23 turns. Per unit on day 9 that means 4.0-5.2 crop tiles and 1.25-1.35 animals. Of the effective actions on days 8-10, about 35-45% are animal chores (FEED, CARE, COLLECT_FERTILIZER, HARVEST), 30-40% watering, 10-15% planting and building, and about 12% shed trips (PICKUP wheat for FEED, DROP).. Teams: Fits per team over days 2-16: R^2 0.77-0.93. Share of seat-days predicted within +-1 hire: FQ 97%, Boey 91%, TFC 82%, 吃白饭 93%, Yizhou 97%. Median effective actions per unit-day on days 8-10 (p10-p90): FQ 11.2 (10.3-12.4), Boey 11.5 (9.7-12.7), TFC 11.0 (9.5-12.8), Yizhou 11.8, 吃白饭 9.4 (it carries spare hands).. Ours: T7 follows the same ratio: median 11.0 (9.6-11.8) on days 8-10. On T7's own day-8/9 farm the elite model predicts 7.4-7.6 hires, and T7 hires 8.2. On days 2-5 it predicts 5.3-5.7 and T7 hires 4-5. The labour gap is farm size, not the crew rule. T7 hires 55.8 hand-days on days 0-9 against the elite's 63-70. On day 9 T7 works 37 tiles and 12 animals; the elite work 44-57 tiles and 14-15 animals.. Evidence: Wages are 1.5-4.3% of sales over days 0-15 (T7 2.1%). Elite wages on days 0-9 are $445-601, T7's $245, so the elite's larger crew costs only about $200-350 more over days 0-9. What a marginal hand's 11 actions buy is priced by the engine rules: FEED+CARE on a cow adds 1 milk per day (about $160-185 at day-8 prices), COLLECT_FERTILIZER adds 1 fertilizer ($80-100), and an in-window wheat watering adds 1 wheat ($25-35). The 10th, 11th and 12th hands cost $55, $89 and $144.
- **NE land day: hire before the land exists and fill NE that same day**: trigger: Day 6, when the day's plan buys NE at hour 1-2. Cash before the purchase is $1.3-2.1k: FQ $1,316 at h2.0, Boey $1,514 at h1.5, TFC $1,955 at h1.4.. Action: Hire 8.5-9.4 hands at hour 0, which is +3.3-4.4 over day 5 (FQ 8.5, Boey 9.4, TFC 9.3). No hires come after the land purchase. Plant 18-21 NE tiles the same day (about 13-14 strawberries and 3-5 wheat) and build 2-4 structures (pastures, 1 coop). Day 7 drops back to 6.6-7.7 hands.. Teams: Day-6 hires at least day 5 + 3: Boey 100%, TFC 98%, FQ 48%, 吃白饭 and Yizhou 0% (a flat 8). At least 15 NE plantings the same day: FQ 99%, 吃白饭 98%, Boey 87%, TFC 86%, Yizhou 20%.. Ours: T7 buys NE on day 6 at h6 with $2,964. It hires 7.2 (+3.2) and plants only 13 NE tiles (8 strawberries, 4.9 wheat), spending 7 actions on builds (6.5 pastures). 0% of T7 seats reach 15 NE plantings.. Evidence: Labour is not what limits this: the elite pay $72-131 in wages on day 6 against T7's $37. The 5-8 extra strawberry tiles and the earlier start are what count. Prior phase research found a ~$9k farm-value gap at day 16 against these teams.
- **SW land day: pre-hire 10-11 at hours 0-1 and plant SW the same day**: trigger: Day 8-9, once the morning sales push cash to $2,000. Land hour and cash before: FQ day 8.0 h5.6 $2,476; Boey day 8.3 h6.2 $2,347; TFC day 8.0 h6.6 $2,530; 吃白饭 day 9 h2.3 $2,539; Yizhou day 9 h3.3 $2,523.. Action: Hire 10-11 hands at hours 0-1, before the land exists: FQ 10.2, Boey 10.1, TFC 10.7, 吃白饭 11.0, Yizhou 10.0, against 7.0-9.0 the day before. Plant 11-18 SW tiles the same afternoon (9-13 wheat plus 2-4 strawberries): FQ 18.1, Boey 15.7, TFC 11.3, 吃白饭 13.4, Yizhou 17.7. The next day adds 2-9 more plantings plus builds and placements (Boey and TFC build and place about 2.7).. Teams: SW by day 9: FQ 100%, Boey 91%, TFC 100%, 吃白饭 100%, Yizhou 100%. At least 10 hires, all before the land hour: FQ 72%, Boey 84%, TFC 96%, 吃白饭 54%, Yizhou 100%. At least 10 SW plantings the same day: FQ 96%, Boey 87%, TFC 70%, 吃白饭 87%, Yizhou 100%.. Ours: T7 buys SW on day 11 at h1, holding $19.1k from the melon sales. It runs 10.2 hands and plants 24 SW tiles (10.9 wheat, 10.4 strawberries, 2.6 tomatoes). It hires 8.2 on days 8 and 9: 0% of seats reach 10, and 0% have SW by day 9.. Evidence: The SW-day crew costs $120-250 in wages. What it buys is 2-3 days of earlier SW production: wheat planted on day 8 is harvestable from day 10.
- **Hour-0 market list: sales that fund the wage first, then the hires; overflow at hour 1**: trigger: Hour 0 each day, when cash m0 is below the Fibonacci wage of the planned hour-0 hires. FQ and Boey start days 1-10 with about $10-13. Or when the day needs more than 10 orders (hires, sales, seeds and animals together).. Action: Put SELL FERTILIZER (and WHEAT) at the lowest indices. They clear before the HIRE orders in the same turn: hour-0 sales average $157 (FQ, mostly fertilizer $91 and wheat $65) and $253 (Boey, fertilizer $200) against an hour-0 wage of $54. Then HIRE x8-9 at hour 0, which leaves 1-2 slots for sales and buys. Hands above the 10-order cap are hired at hour 1 (FQ 3.0, Boey 2.5, TFC 2.3 at hour 1 on day 10). At least 97% of hires land by hour 1 on days 3-16. Late hires (hour 2+) occur only on FQ days 1-2 (15-25%), when even the hour-0 sales cannot cover them.. Teams: Hour-0 wage above m0 on at least 3 of days 3-9: FQ 99%, Boey 79%, TFC 1%, 吃白饭 0%, Yizhou 7%. As seat-days: FQ 1,458 and Boey 1,088 of days 1-10. All 10 hour-0 slots used on days 8-10: FQ, Boey and TFC 95-100% of seat-days, 吃白饭 0-52%, Yizhou 0-100%. At least 8 hour-0 hires on 3+ of days 6-10: 98-100% of seats for every team.. Ours: T7 never needs this: 1 seat-day in 960. The tape holds $200-1,450 at hour 0 on days 3-9. Its hour-0 list is not full on days 6-9 (7.2-9.2 orders, 0-22% of seat-days at 10), and it hires 6.6-8.0 at hour 0. On day 0 it hires at hour 1 (the elite at hour 0), which loses 5 hand-turns.. Evidence: This rule is the mechanism that lets the elite keep no idle cash. The day's wage is paid from same-turn fertilizer sales, so labour needs no reserve. That feeds the cash question: every dollar held over from the day before goes to land and animals.
- **Wage cap: at most 12 hands**: trigger: Any day on which the crew rule asks for more than 12. Action: Stop at 12. The day's wage for n hires is 8: $54, 9: $88, 10: $143, 11: $232, 12: $376, 13: $609, 14: $986. With ~10 hands on days 9-10 the elite pay $140-430 a day, 1.5-9% of that day's sales. The wage 'blows up' only from the 13th hand ($233) and the 14th ($377).. Teams: Seat-days (days 6-16) with 13+ hires: FQ 8.5%, Boey 2.2%, TFC 1.2%, 吃白饭 1.0%, Yizhou 0.6%. Seats never above 12 over days 0-16: FQ 51%, Boey 88%, TFC 90%, 吃白饭 91%, Yizhou 93%. Most common range: FQ and Yizhou 11-12 (60% of days 6-16); Boey, TFC and 吃白饭 9-10 (46-54%).. Ours: T7 has 13+ hires on 0.2% of seat-days and stays at 12 or below on 98% of seats. Its days 6-16 are mostly 9-10 (51%) or 8 and below (35%).. Evidence: Engine Fibonacci wage (engine: _hire_cost). The FQ/Boey wage share of sales (2.9% / 1.5%) shows the cap is not binding up to 12.
- **Early crew, days 2-5**: trigger: Days 2-5, on an NW-only farm of 16-20 tiles with 5-9 animals and more animals arriving (the elite herd grows from 5 to 8.3-9.4 by day 5-6). Action: Hire 5-6 hands daily: FQ 5.6-6.5, Boey 5.1-5.7, TFC 5.0, 吃白饭 and Yizhou 6. Wage is $12-26 a day.. Teams: At least 5 hires on every day 2-5: FQ 93%, Boey 100%, TFC 98%, 吃白饭 100%, Yizhou 47%.. Ours: T7 hires 4, 5, 4, 4 on days 2-5 (0% of seats meet the rule), with 4-6 animals. Its hands already sit idle on 14-24% of unit-turns on days 2-5, so extra hands only pay if the herd grows at elite speed.. Evidence: Costs about $8-15 a day. It supports the elite's +2-3 animals by days 4-6.
- **Skip-day rhythm (Boey and TFC only)**: trigger: The day after a big planting day: day 1 after day 0, day 7 after the NE day, day 11 after day 10. Crops watered yesterday need no water today: wheat at age 1 and melons below age 6 yield nothing from it, and a crop dies only after 2 unwatered days. Ongoing strawberries and tomatoes produce without water.. Action: Hire 2-4 fewer hands: Boey day 1 2.7 vs 4.9, day 7 6.6 vs 9.4/9.6; TFC day 1 1.1 vs 5.0, day 7 7.1 vs 9.4/10.7. Water wheat only at age 0 and ages 2-4 (day-1 wheat coverage 3-10%, day 7 7-10%). Water melons every other day until age 6 (coverage 97/24/92/25/94% on days 2-6).. Teams: Day 1 below day 0: Boey 87%, TFC 98%, FQ, 吃白饭 and Yizhou 0%. Day-7 dip: Boey 87%, TFC 94%, FQ 59%, others 0%. Day-1 wheat at most 20% watered: TFC 98%, Boey 87%, 吃白饭 and Yizhou 100%, FQ 0% (FQ waters 84%). TFC's 20-22 Sep version did not do this (day 1 3.4, day 7 8.9).. Ours: T7 dips on day 1 (3 vs 5) but not on day 7 (7.2 = 7.2). It waters age-1 wheat at 100% on days 1 and 7, and out-of-window melons at 100% on days 3 and 5 (Boey/TFC 5-25%). That is about 35 wasted actions, about 3 hand-days, over days 1-7.. Evidence: Negligible, a few dollars of wage a day. The rule is a byproduct of the engine's watering rules, not a lever. It matters only for planning crews for a denser elite-style farm.
- **Full daily animal care**: trigger: Every placed animal, every day. Wheat is picked up from the shed for each FEED.. Action: FEED + CARE + COLLECT_FERTILIZER on every animal daily. The care bonus turns a cow's 1 milk per 2 days into 3, a sheep's 1 wool per 3 days into 4, and a goose's 1 egg a day into 2. Fertilizer can be collected every day whether or not the animal is fed.. Teams: FEED / CARE / COLLECT per placed animal, days 6-16: Boey geese 103/104/99%, cows 91/94/99%, sheep 103/105/100%. TFC 88-103 / 85-102 / 99-100%. Yizhou 84-97%. 吃白饭 80-89%. FQ cows 79/78/100%, sheep 92/90/99% (no geese).. Ours: T7 does the same: FEED 93-111%, CARE 102-109%, COLLECT 94-100%.. Evidence: Engine care-bonus rule. This is the highest-value use of a hand-turn.
- **Hands work the whole day; idle policy**: trigger: All hours. Action: A hand makes its first effective action at hour 2-3 and its last at hour 21-23. Only 7-11% of hand-turns on days 6-10 fall after a hand's last effective action. Effective actions per unit-turn run 39-55% in every hour block, and the rest are moves. FQ never passes (idle hands walk); the others pass on 2-10% of turns from day 8.. Teams: Hourly replays, 40 seats per team (Yizhou 16), days 6-10. Tail idle after the last effective action: FQ 7.6%, Boey 10.9%, TFC 9.9%, 吃白饭 8.6%, Yizhou 9.8%. Pass/no-op share on days 0-5: FQ 0%, Boey 7-17%, TFC 8-31%, 吃白饭 30-54%, Yizhou 27-46%.. Ours: T7 has 7.3% tail idle on days 6-10, and its effective share per hour block is 40-50%. It passes on 26-41% of unit-turns on days 0-1 and 14-24% on days 2-5, and on 4-13% on days 6-16 (comparable).. Evidence: Per-unit productivity is the same for elite and T7, so there is no labour-efficiency edge to copy. The elite advantage is in how big a plan the crew is sized for.

## Mined area: CROPS AND TILES, days 0-15: what the opening winners plant, in which quadrant, when, and how each crop's count depends on the shops known. Data: 881 recorded elite seats from 23-26 Sep (Boey 236, FQ 267, 吃白饭的大肥鱼 (CBF) 200, THIRD FARM CLUB (TFC) 162, Yizhou (Yiz) 16) against T7 (our tape plus controller) on 96 seats in the same towns. A new tile-level replay (crops/tiles.py) logs every planting's tile, day, waters, fertilizer, each harvest's units and how the planting ended. All 881 elite seats reproduce their recorded rewards; the 96 T7 games reproduce the extract.py 'ours' rewards exactly.

1. **The main crop gap is on days 2-4 in NW, and it is in placement, not volume.** All five teams replant the NW tiles freed by the early day-0 wheat harvest (age 2.3-2.9) with fertilized strawberries the same day: CBF and Yiz 10 (100% of seats), FQ 6.4, Boey 4.4, TFC 4.2 (87-100% of seats plant 3 or more). They grow almost no second NW wheat and buy feed instead. T7 replants 88% of those tiles with wheat (10 plantings harvested at age 2 for 2 units) and plants its first 4 strawberries on day 5. The elite's early strawberries are harvested on days 12-18, when the price is at its game high of about $190. They net $1,000-1,240 a tile against about $400 for continuous NW wheat over the same days. Rough estimate: +$3-4k a game for 6-7 tiles, before market effects. T7 can pay for about 3-4 of these tiles on days 3-4 out of the cash it holds; more needs spending moved from day 0.

2. **The NE strawberry count on day 6 depends on shops; ours is fixed.** Boey, FQ and TFC plant about 7 + 7 strawberries per strawberry buyer known on day 6 (6-8 / 14-16.5 / 19-22 for 0 / 1 / 2 buyers; R2 0.75-0.81) and fill the rest with wheat. CBF always plants 10. T7 always plants 11 and 7 wheat. In 1-2 buyer towns (74% of games) T7 puts its extra strawberries into the day-11 SW batch instead. That batch nets $639 a tile against $1,071 for T7's own day-6 batch, because its harvest falls on days 21-27 into a $65-106 price. Total strawberries by town type are about equal to the elite's (T7 30.3 tiles on days 0-15, elite 27-35); only the timing differs.

3. **The SW wheat pattern is the same in both; the purchase day is not.** On the day SW is bought, everyone plants 12-16 wheat (85-99% of seats, T7 included). The elite buy on day 8-9 and hold 17.6-20.8 wheat tiles at day 10; T7 buys on day 11 and holds 5. That gap is the land/cash question, not a crop choice. CBF, TFC and Yiz then feed their herds from their own wheat.

4. **No gap in these areas.**
   - Melon count (about 10 for the elite by day 3, split 6-7 on day 0 and 3-4 on days 1-2; T7 12 on day 0). T7's melons earn more ($17.6k against $13-16k), so keep them.
   - Wheat harvest ages (2-4 for everyone).
   - Strawberry fertilization (T7 100%) and yield (7-8 units a tile).
   - Strawberry totals by town type.

5. **Smaller, team-specific habits.**
   - CBF and TFC replant 3-4 melons on days 10-12 (about 80% of seats; about +$10-20 a tile-day over wheat).
   - CBF, TFC and Yiz grow tomatoes on days 9-15 (worth about the same as wheat).
   - FQ scales carrots with carrot buyers (+27 tiles per buyer; below wheat in value).
   - Boey, CBF, TFC and Yiz fertilize about 60% of wheat from day 10 (+$5-20 per fertilizer, so marginal); FQ does not.
   - CBF adds a 7-10 strawberry batch on day 13, which falls in controller days for T7.

6. **Tile budget by quadrant.**

| Day | Quadrant | Elite | T7 |
|---|---|---|---|
| 6 | NW | 10 melons + 4-10 strawberries + 5-9 animals | 12 melons + 4 strawberries + 3 wheat + 6 animals |
| 8 | NE | 10-15 strawberries + 5-9 wheat + animals | 11 strawberries + 7 wheat + 3 empty structures |
| 10 | SW | 12-15 wheat + 1-6 strawberries + 2-5 animals | not owned (bought day 11: 11 wheat + 10 strawberries + 3 tomatoes) |

   FQ also buys SE on day 10 (100% of seats) and puts 19 wheat and 4 carrots there; Yiz buys SE by day 10 in 88% of seats.

7. **Suggested tape layers to gate, in order of value.**
   - A. On days 2-4, replant harvested day-0 NW wheat tiles with strawberries instead of wheat, up to what cash allows (at least move the day-5 batch of 4 to day 4 and add 3-4 more). Buy the feed wheat instead.
   - B. Size the day-6 NE strawberries at about 7 + 7 x (strawberry buyers known), take wheat for the rest, and reduce the day-11 SW strawberries by the same number.
   - C. Replant 3-4 melons on the NW melon tiles on days 10-11.

FILES (all under C:/Users/khant/OneDrive/Documents/ChatGPT/2027/kaggriculture_review/kg/gold/top10/research/openmine/crops/):
- tiles.py: tile-lifecycle replay, modes elite / ours / one.
- tiles_elite.jsonl (881 seats) and tiles_T7.jsonl (96 games, both farms).
- load.py, which builds days.pkl.
- Analysis scripts, each with a matching .txt output:
  - a1_plant: plantings by day
  - a2_quad: by quadrant and tile budget
  - a3_shops: conditional on shops
  - a4_revenue
  - a5_tiles: cohorts, harvest ages, replant transitions
  - a6_px: prices
  - a7_wheat: wheat and fertilizer balance
  - a8_rules: compliance percentages
  - a9_seedcash
  - a10_strawday
  - a11_fit: shop regressions
  - a12_value: per-tile economics
  - a13_townsplit

Nothing was committed and gold/submit/ was not touched.

### Constraints
ENGINE (kaggriculture.py):
- Wheat: $10 seed. It must be watered on the planting day or it becomes a weed. It starts at 1 unit and gains +1 per watered day at ages 2-4 (+2 if fertilized), capped at 6. It decays from day p+5, so harvest by age 4. Unfertilized, it gives 2/3/4 units at age 2/3/4.
- Strawberry: $100 seed. Production days p+10, p+12, p+14, p+16 at 1 unit each (2 if watered and fertilized that day). Two dry days in a row turn it to a weed. It rots the day after the 4th production.
- Melon: $80 seed. +1 per watered day at ages 6-12, so 6 units at age 10; harvest by age 12.
- Tomato: $50 seed. Produces daily at ages 8-11.
- Carrot: $20 seed. Best at age 3 (3 units, 4 fertilized).
- One fertilizer covers the day it is applied and the next 2 days.
- Shops unlock at the end of days 2, 5, 8, 11, 14 (known from days 3, 6, 9, 12, 15), drawn with replacement from 8 types: 4 buy strawberries, 2 tomatoes, 2 carrots, 5 wheat, none melons. Each strawberry buyer absorbs about 6 units a day; the town centre takes 1 unit of every crop a day and is the only melon buyer.

MARKET (shared by both farms):
- The strawberry price rises from $120 to $190-196 by days 13-15 because nobody sells before day 12. It then falls as both farms sell, to $65-140 on days 22-29.
- Each extra strawberry sold at once lowers the price by about $1.9 until the shops absorb it.
- Melon prices collapse after the day-10 harvest (day 12: $136 in T7 games, $163-192 in the elite's games).
- Fertilizer falls from $100 to about $72 by day 10 and $45-50 by day 16.

CASH:
- The elite end every day 1-8 with $0-100 (lowest cash of the day) and buy early seeds out of same-day sales: strawberry seed on days 2-4 is 4-10 x $100, second-batch melons 3-4 x $80 on days 1-2.
- T7's lowest daily cash on days 2-9 is $99, $129, $340, $576, $709, $499, $450 and $963. T7 can therefore afford about 3-4 extra day 3-4 strawberries without other changes. Moving the day-5 batch of 4 to day 4 is also affordable. More than that needs cash moved from day 0 (T7 spends $1,040 on seeds on day 0 against the elite's $500-690).

LABOUR:
- A strawberry tile takes about 12-17 actions over 16 days.
- Wheat takes about 5 actions per 2-3.5-day cycle, about 3 times the actions per tile-day.
- So replacing NW wheat with strawberries also frees hands on days 2-8.

DO-NOT-RELEARN (from the brief):
- Keep the tape's day 2-3 cows and its strawberry volume (denial of about $10k). The changes above are timing and placement of the same volume.
- Copying another team's recorded route into a different town loses. Implement these as adaptive tape layers keyed on the same triggers (freed day-0 wheat tiles, strawberry buyers known on the NE/SW buy day).
- Most of the SW wheat gap is the purchase day (land/cash area); the crop rule for SW is already in the tape.
- The value figures are partial-equilibrium, per tile, at each team's own daily sale price. They ignore the rival's reaction and the price impact on both farms, so each change needs a gate run (elite / goldg / top10g).

### Rules
- **Day-0 NW opening (wheat and melons)**: trigger: Day 0, $3,000, no shops known yet.. Action: Plant 9-13 wheat and 6-7 melons in NW, then 3-4 more melons on day 1 or 2 (about 10 melons by day 3). Harvest the day-0 wheat early, at a mean age of 2.3-2.9 days (2.3-2.9 units a tile), so the tiles free up.. Teams: All five teams, fixed. Boey plants 13 wheat and 7 melons (72% of seats) and adds melons on day 2 (100%). CBF plants 10 wheat and 6 melons, then 4 melons on day 1 (100%). TFC plants 13 wheat and 7 melons, then about 3 melons on day 2 (98-100%). Yiz plants 9 wheat and 6 melons, then 4 melons on day 1 (100%). FQ plants 9 wheat with either 3 melons (57%) or 8 (43%), and 74% add 2 or more on days 1-3 (8-11 in total).. Ours: 8 wheat and 12 melons, all on day 0 (100%). No second melon batch. Day-0 seed spend is $1,040 against the elite's $500-690.. Evidence: Day-0 melons net $1,364-1,435 a tile for the elite and $1,309 for T7. The day 1-3 melon batch nets $969-1,127. Melon revenue in the T7 games: T7 $17.6k against $13.2-16.4k for the recorded elite. Keep our 12 day-0 melons. This is context for the next rule: the elite's second melon batch and first strawberries go on tiles and cash that T7 spends on day-0 melons and a second wheat cycle.
- **NW tiles freed by the day-0 wheat go to strawberries, not wheat**: trigger: Days 2-4. A day-0 NW wheat tile is harvested (mostly at age 2-3). Does not depend on the first shop (known from day 3).. Action: Replant the harvested tile with a strawberry the same day (median gap 0.0-0.2 days) and fertilize it (92-100% of these tiles are fertilized, about 2 applications a tile). Plant almost no second wheat in NW (0-2 tiles). Animal feed for days 4-8 comes from the market instead.. Teams: Strawberries planted in NW on days 1-4, per seat: CBF 10 (100% of seats; every day-0 wheat tile becomes a strawberry), Yiz 10 (100%, likewise), FQ 6.4 (100% plant 3 or more; FQ starts on day 1 in 43% of seats), Boey 4.4 (87%), TFC 4.2 (88%). The rest of the freed tiles become melons and animal structures. Share of seats replanting 2 or fewer NW wheat tiles on days 1-5: CBF and Yiz 100%, Boey 92%, TFC 80%, FQ 9% (FQ replants about 4 wheat). With 0 against 1 strawberry buyer known on day 3: Boey 4.1 against 4.9, FQ 3.0 against 5.1, CBF and Yiz fixed.. Ours: 0 NW strawberries on days 1-4 (100% of seats). 88% of the day-0 wheat tiles are replanted with wheat (10 wheat plantings on days 2-5, harvested at age 2 for 2.0 units). The first 4 NW strawberries go in on day 5. NW strawberry tiles at day 4: T7 0, elite 1.6-9.9.. Evidence: The days 0-5 strawberry batch nets $1,000-1,240 a tile after seed, at the team's own sale price on each harvest day (weighted harvest day 15.6-16.6; strawberries sell for $173-203 on days 13-16 because no one sells before day 12 and the price climbs from $120). T7's own 4 day-5 NW strawberries net $1,265 a tile. NW wheat replanted on days 1-5 nets $49-63 per 2-day cycle ($24-28 a tile-day), about $400 over days 2-18 and with roughly twice the labour. Moving 6-7 of T7's NW wheat replants to day 2-4 strawberries is worth roughly +$450-650 a tile, or about +$3-4k a game before the price effect on both farms. Each extra unit sold lowers the price by about $1.9 until shops absorb it (about 6 units a day per strawberry buyer). It costs about 20 wheat units bought for feed (about $600) and about $600-700 of seed on days 2-4 (see constraints).
- **Strawberry and wheat split on NE, the day NE is bought (day 6)**: trigger: NE bought (all teams and T7 on day 6). b6 = the number of strawberry buyers (BRUNCH_SPOT, ICE_CREAM_SHOP, SMOOTHIE_SHOP, FARMERS_MARKET) among the 2 shops known on day 6.. Action: Plant NE strawberries of about 7 + 7*b6 on the buy day and the next, and wheat of about 10 - 5*b6. Boey/FQ/TFC also add 1-2 melons. The remaining NE tiles hold animals (geese coops, pasture). The rival's strawberry tiles and own cash add nothing to the fit.. Teams: Mean strawberries at b6 = 0/1/2: Boey 7.8/13.9/19.2 (least-squares fit 10.1 + 5.7*b6, R2 0.75), FQ 6.0/16.5/22.0 (+8.1 per buyer, R2 0.77), TFC 7.9/15.6/21.8 (+7.1, R2 0.81), Yiz 0.3/7.6/14.3 (+7.4, R2 0.84). NE wheat: -4.3 to -5.8 per buyer (R2 0.63-0.72). Share of seats within 3 of 7+7*b6: Boey 86%, TFC 84%, FQ 68%. CBF ignores shops: 10 strawberries and 5-6 wheat in 100% of seats.. Ours: Fixed 11 NE strawberries (8 on day 6, 3-4 on day 7) and 7 wheat in every town (100%; fit coefficient 0.0 on b6). In b6=2 towns T7 plants 8-11 fewer NE strawberries than Boey/FQ/TFC. It makes up the difference with a larger day-11 SW batch (next rule), so its total strawberries match the elite by town type (b6=2: 35.5 tiles against 38.4 for the recorded elite in the same games). In b6=0 towns T7 plants 3-5 more than Boey/FQ/TFC.. Evidence: T7's own day 6-7 strawberry batch nets $1,071 a tile (weighted harvest day 19.3); its day 8-11 SW batch nets $639 (weighted harvest day 23.3; strawberries sell for $65-106 on days 22-25 in T7 games). Moving a strawberry from the day-11 SW batch to NE on day 6 is worth about +$430 a tile. That is about +$3.4k in b6=2 towns (19% of T7 games) and +$1.3-2.2k in b6=1 towns (55%). In b12=0 towns T7 sells strawberries for $40 on average against $60 for the recorded elite ($4.3k against $6.1k per seat).
- **SW on the day it is bought: dense wheat plus shop-conditional strawberries**: trigger: SW bought: Boey 8.3, FQ 8.0, TFC 8.0, CBF 9.0, Yiz 9.0 (land/cash area). bsw = strawberry buyers known on the SW buy day.. Action: Same day or next: plant 13-16 wheat on SW (the elite's biggest wheat planting). Within 3 days: strawberries of about 3-6 + 5.4-7.7*bsw - 0.25-0.53*(NE strawberries). The rest of SW goes to geese coops. Wheat tiles at day 10: 17.6-20.8 in total (SW 12-15, NE 3-9, NW 0).. Teams: Seats planting 10 or more SW wheat on the buy day or next: Boey 93%, TFC 91%, CBF 90%, Yiz 94%, FQ 85%. SW strawberries in towns with 2 or more buyers: Boey/FQ/TFC/Yiz 95-100% plant 4 or more; with 0 buyers, 2 or fewer: Boey 72%, CBF 95%, FQ and TFC about 45%. CBF plants about 1-2 regardless. 14 or more wheat tiles at day 10: Boey 73%, FQ 73%, TFC 76%, CBF 91%, Yiz 100%.. Ours: The same wheat rule, 3 days later: SW bought on day 11, 11.8 wheat on the buy day or next (99%), plus 10.4 strawberries (fit 3.8 + 4.5*b, not reduced by the NE count) and 2.6 tomatoes. Wheat tiles at day 10: 5 (0% of seats reach 14). By day 12 T7 holds 20 wheat tiles, against Boey 24, CBF 26, FQ 42, Yiz 34.5 and TFC 17.. Evidence: The elite's day 6-9 wheat nets $126-150 a tile per 3-day cycle ($40-45 a tile-day). Wheat harvested on days 10-13: elite 43-111 units (TFC 63) against T7 32. CBF/TFC/Yiz feed themselves (they buy 2-45 wheat per 2 days on days 8-15); T7 buys 35-47 per 2 days while also selling. The crop rule is already in the tape. The gain comes from the earlier SW purchase (land/cash area), then planting the SW wheat on the buy day.
- **Wheat handling everywhere (age, replant, fertilizer)**: trigger: Any wheat tile, days 0-15. Fertilizer on wheat starts from day 8-10, when the fertilizer price has fallen to $72-80 (from $100).. Action: Water on the planting day. Harvest at age 2-4, never older: 18-45% at age 2 (about 2 units), 26-44% at age 3 (3-4 units), 29-42% at age 4 (4-5 units); under 3% die. Replant wheat on the same tile the same day (42-85% of tiles after the day 6-11 wheat). From day 8-10, fertilize about 0.5-0.7 of new wheat tiles; the day 10-15 wheat then yields 4.1-4.7 units a tile.. Teams: Harvest ages: all teams the same. Seats fertilizing 40% or more of their day 10-15 wheat: Boey 87%, CBF 96%, TFC 86%, Yiz 100%, FQ 4% (FQ fertilizes 0.14 a tile and sells its fertilizer).. Ours: Same age mix (35% at age 2, 30% at 3, 36% at 4). The tape's day 10-11 wheat is 1% fertilized (3.1 units a tile); 8% of seats meet the 40% bar. The controller raises it later (86% for days 14-15).. Evidence: Fertilized day 10-15 wheat yields 4.1-4.7 units a tile (Boey/CBF/TFC/Yiz) against 3.36 for FQ; about +1.1-1.3 units for about 0.6 fertilizer. That is about $75 of wheat at $40 per fertilizer, against a sale price of $61-74 for fertilizer on days 10-12: only +$5-20 per fertilizer. Low priority; FQ, the strongest team, skips it.
- **NW melon tiles after the day 10-12 melon harvest**: trigger: Days 10-13, melon tiles harvested (6 units each; 98-100% reach 6).. Action: Replant with wheat the same day (61-87% of tiles). CBF and TFC also plant 3-4 new melons on days 10-12 (on SW, NE and NW). FQ puts 17% of these tiles into carrots.. Teams: Melon tile to wheat: Boey 87%, TFC 80%, FQ 78%, CBF 67%, Yiz 61%. New melons (2 or more) on days 10-15: CBF 82%, TFC 80%, Boey 5%, FQ 0%, Yiz 0%.. Ours: 66% of melon tiles go to wheat and 33% get no crop by day 16 (they hold structures and animals). New melons: 4% of seats.. Evidence: The day 10-15 melon batch nets $552-661 a tile ($55-66 a tile-day; sold on about days 21-22 for $115-140), against $44-51 a tile-day for day 10-15 wheat. About +$0.3-0.5k a game for 3-4 tiles. The town centre is the only melon buyer (1 unit a day), so both farms' melon volume sets the price. In T7 games the day-12 melon price is $136, against $163-192 in the elite's games.
- **Tomatoes on days 9-15**: trigger: Day 9 onward. tb9 = tomato buyers (PIZZA_SHOP, FARMERS_MARKET) known on day 9.. Action: CBF and TFC plant 5-6 tomatoes over days 10-15 whatever the shops (fit on tb9 R2 0.04-0.15), mostly on SW. Yiz plants 6.8 + 7.2*tb9 + 5.0 per new buyer by day 12 (R2 0.77), starting day 9 on SW. All fertilized (98-100% of tiles, 7.3-7.9 units a tile).. Teams: 3 or more tomatoes on days 9-15: Yiz 100%, TFC 84%, CBF 76% (73-75% even with 0 buyers), Boey 4%, FQ 0%.. Ours: 3.9 tomato tiles (1 on day 8 in 26% of seats, 2.6 on day 11 in 36%). 3 or more: 40% of seats (14% with 0 buyers, 56% with 1 or more).. Evidence: The day 8-15 tomato batch nets $428-504 a tile ($39-46 a tile-day), about the same as wheat. Whole-game tomato revenue: CBF $6.5k, TFC $4.8k, Yiz $8.7k, T7 $4.9k (T7 $2.1k against Yiz's $8.7k in the same games). Low-to-mid priority; the controller's strawberry-to-tomato switch already covers part of it.
- **Carrots, conditional on carrot buyers (FQ)**: trigger: Days 8-15. cb9 = carrot buyers (PET_CAFE, FARMERS_MARKET) known on day 9, plus new ones by day 12.. Action: FQ: carrots on days 8-15 of about 1 + 26.7*cb9 + 16.5 per new buyer by day 12 (R2 0.62), on SW/SE and the NW melon tiles. Means at cb9 = 0/1/2: 5.6/29.7/62.5 tiles. Boey: +6.7 per buyer.. Teams: 10 or more carrots with 1+ buyer on day 9: FQ 88%, Yiz 75% (n=4), Boey 30%, TFC 28%, CBF 18%. With 0 buyers: FQ 21%, others 1-12%.. Ours: About 0 carrots before day 16 (0.5 tiles; 4% of seats in towns with a buyer).. Evidence: Carrots net $90-121 a tile per 2.6-3 day cycle ($33-40 a tile-day), below day 10-15 wheat ($44-51). Whole-game carrot revenue is similar for every team ($5.1-7.2k; T7 $5.7k). FQ-specific; low priority.
- **Late strawberry batch on days 12-15**: trigger: Day 12-13, depending on the strawberry buyers known on day 12 (b12).. Action: Plant another strawberry batch that scales with b12. Means at b12 = 0/1/2+: CBF 4.4/5.0/11.6 (mostly day 13, 96% of seats), FQ 1.7/4.2/6.3, Boey 1.7/3.3/3.7.. Teams: Per seat: CBF 9.6, FQ 5.5, Yiz 4.9, Boey 3.4, TFC 2.4 tiles.. Ours: 0.9 tiles (controller days).. Evidence: Nets $365-786 a tile (weighted harvest day 26-27). This is controller territory for T7 (day 12 in strawberry-rich towns, otherwise day 16). Low priority for the tape.
- **Strawberry care (no gap)**: trigger: Every strawberry tile.. Action: Water every 1-2 days (a tile left dry for 2 days turns to weed); fertilize about 1.8-2.2 times a tile (each application covers 3 days, so 1-2 of the four 2-day productions); dig or abandon after the 4th production.. Teams: 90%+ of tiles fertilized, 6.1-7.8 units a tile, all teams (87-96% of seats).. Ours: 100% fertilized, 7.5-8.0 units a tile. No change needed.. Evidence: A fertilized production gives 2 units instead of 1, about +$150-190 per application on days 13-19, against a fertilizer sale price of $44-80.

## Synthesis

**Kill check:** fundable_keeping_denial

Yes, it is fundable without touching the denial moves, but only for the parts of the elite opening that fit the tape's tiles and the cash it already leaves idle.

Where the SW money comes from: the day-0 cows' first milk. Each day-0 cow gives 6 milk on day 8. FQ, TFC and Boey sell it at hour 4 and buy SW within the hour, holding $2.3-2.5k. CBF and Yizhou keep it overnight and buy SW on day 9 at hours 3-4. The elite skip nothing. Their extra $1,051 at the SW moment is all income: fertilizer +$1,050, wool +$709, eggs +$255.

We already have the cash. On day 8, hour 4 (step 196), T7 sells 12 milk ($2.26k) and spends it in the same step on 2 sheep, plus 4 strawberry seeds at hours 9-16. Without those buys it holds at least $2k on day 8 in 100% of the 96 towns (peak $2.8-2.9k). It holds $2k or more by the end of day 9 in 62%. Its SW is late only because the tape step is fixed at 265 (day 11, hour 1).

Idle slack that funds the early layers: lowest daily cash is $340 on day 4, $576 on day 5, $709 on day 6, $499 on day 7 and $450 on day 8.

Denial moves are untouched:
- day 0: 2 cows + 2 sheep and 12 melons;
- the denial cows on day 2 hour 17 (step 65) and day 3 hour 16 (step 88);
- every strawberry batch keeps its volume or gains: the day-5, day-7 and day-8 batches are pulled earlier onto the same tiles, and the day-11 SW batch is not touched.

Non-denial costs, quantified:
- 2-3 NW/NE feed-wheat tiles are displaced, so about $250-800 more feed wheat is bought over days 4-16;
- 3 SW day-11 wheat tiles become coops (about $150 of tape wheat by day 16);
- keeper wages of about $500 over days 8/9-15;
- in the optional day-8 mode, the day-8 sheep slip about 1 day (about $100-150 each).

NOT fundable without giving up a denial or melon edge (left out of the design):
- a 5th animal on day 0: needs about 5 melons moved off day 0, about -$3-6k of first-seller melon revenue against about +$3k for the cow;
- geese on day 2: need $600 on day 2, when T7's lowest cash is $99, which would bounce the day-2 denial cow;
- 10 NW strawberries on days 2-4: day-3 lowest cash is $129, before the day-3 denial cow;
- dense SW wheat on days 8-11: T7 plants all 25 SW tiles on day 11, and layer labour on days 10-11 would be the 12th-14th hands at $144-377 a day.

So this captures part of the roughly $9k day-16 farm gap, not all of it.

### Schedule
Notation: step = day*24 + hour. Tile coordinates are (x, y); NW = x 0-4, y 0-4; NE = x 5-9, y 0-4; SW = x 0-4, y 5-9. The shed-access tiles are (4,4), (5,4), (4,5) and (5,5). Every guard uses R(s) = the tape's remaining buy orders today after step s (products at price+5, seeds, animals, the Fibonacci sum of its remaining hires) - 0.7 x the tape's planned SELLs today at current prices + the next morning's hour-0/1 hire wages + a $100 buffer. The tape's orders always keep priority; a layer order only goes in if money after this step's sells - cost >= R(s).

DAY 0-3: tape unchanged.
- Day 1: 2 cows + 2 sheep, 12 melons and 7 wheat seeds (5 hands hired at hour 1).
- Denial cows at steps 65 and 88. Hires 5 / 3 / 4 / 5.
- Nothing is injected. There is no slack: lowest cash is $99 on day 2 and $129 on day 3.

DAY 4 (L3 tp_nw4):
- The tape replants wheat on the NW feed tiles (1,0) at hour 11, (0,1) at hour 10 and (0,0) at hour 15. These tiles are watered on days 4-6 and harvested at age 2 on day 6.
- At step 105 (day 4, hour 9), add BUY_SEED STRAWBERRY k, with k <= 3 set by the guard. Priority: (1,0) first (the tape's own day-7 strawberry tile, so volume is unchanged), then (0,1), then (0,0) (added volume).
- When a tape unit standing on one of these tiles issues ['PLANT','WHEAT'] and a strawberry seed is in hand, rewrite it to ['PLANT','STRAWBERRY']. The tape's next WATER on that tile gives the planting-day water.
- After that, the tape's wheat cycle keeps visiting and watering these tiles (never 2 dry days) until handover. Its HARVEST and PLANT actions there become no-ops.
- Fallback: no seed or guard fails, so the tile stays wheat.

DAY 5: tape unchanged (4 NW strawberries on (0,2), (0,3), (1,1) and (2,0); 4 hires).

DAY 6 (L1 tp_ne6):
- NE is bought at step 150 (hour 6), as in the tape. The route is picked at step 144.
- b6 = number of strawberry buyers among the first 2 shops (BRUNCH_SPOT, ICE_CREAM_SHOP, SMOOTHIE_SHOP, FARMERS_MARKET).
- If b6 >= 1 and the rival is not flagged as a copy: from step 151, buy strawberry seeds with the guard. Rewrite the tape's day-6 ['PLANT','WHEAT'] on NE (5,0), (6,0), (7,0) and (7,1) (hours 16-22) to STRAWBERRY.
- These are exactly the tiles of the tape's own day-8 strawberry batch. Seed buys shift from day 8 to day 6, and the tape's watering on days 6-8 covers them.
- If b6 = 2 and the knob ne6_extra is on: also convert the continuous NE feed wheat on (8,0), (9,0) and (9,1) (planted day 6 hour 22, day 7 hour 22 and day 7 hour 19). This adds 3 tiles of volume.
- s2t cannot clash: it converts only in towns with 0 strawberry shops.
- Fallback per tile: keep the wheat.

DAY 7:
- Strip 1 unit from the tape's day-7 BUY_SEED STRAWBERRY if (1,0) was pulled on day 4.
- 2 cows as in the tape. They are not touched.

DAY 8:
- Strip the tape's day-8 BUY_SEED STRAWBERRY orders (steps 201-208 in route 106), one per NE tile pulled on day 6. This frees up to +$400 on day 8.
- Default mode tp_sw='d9': no land on day 8.
- Optional mode tp_sw='d8' (L2d):
  - At step 196, put [SELL MILK 12, the fertilizer sells] before ['BUY_LAND'] in the same list, and remove BUY_ANIMAL SHEEP 2 into the deferred queue.
  - Condition: money + milk value - 2000 >= R(196).
  - Record the tiles where the tape's PLACE SHEEP fails (steps 201 and 213). The keeper places the sheep there once they are bought on day 9 after the wool.

DAY 9 (L2 tp_sw):
- From step 224 (hour 8, after the wool SELLs at hours 7-8), buy SW at the first step s where money after sells - 2000 >= R(s).
- R already reserves the tape's hour-10 sheep (step 226) and the day-10 morning hires.
- Put the land order after that step's SELLs.
- Hire the keeper (L2y) after the tape's last HIRE of the day. It builds COOPs on SW (0,5), (0,6) and (0,7); these are tape wheat tiles planted on day 11 at hours 16-23. Buy geese (up to 3 at $300 each) at the same or a later step as the guard allows.
- The keeper then does PICKUP GOOSE, PLACE, PICKUP WHEAT, FEED and CARE the same day.
- Fallback: if no step on day 9 qualifies, go to day 10.

DAY 10:
- If SW is owned but cash is short at hour 1, move the tape's day-10 hour-1 GOOSE 2 order (step 241) to the first SELL MELON step (hour 9, step 249). The tape builds those coops at hours 14-19 and places the geese at hours 19-20, so the delay is harmless.
- If SW is not owned yet: BUY_LAND at the first melon-sale step that passes the guard (hour 9-10; melons bring about $13.9k). Then buy the yard geese and build the coops with the keeper.
- Flush the deferred queue: every remaining deferred sheep or goose is bought by the hour-10 melon step.
- Keeper hire: the tape hires 9 at hour 0 plus 2 at hour 1, so the keeper is the 12th hand at hour 1 ($144).

DAY 11:
- Once SW is owned, drop the tape's BUY_LAND at step 265. It would otherwise buy SE for $4,000 (assert that this never happens).
- Generic rule: drop any tape BUY_LAND whose target quadrant is already owned.
- The tape plants its 13 SW strawberries and 12 wheat as recorded. PLANT on the 3 yard tiles becomes a no-op; strip 3 wheat seeds from the day-11 tape buys.
- The keeper is the 11th hand ($89). It feeds, cares for and collects from the geese and drops the eggs. The layer SELLs EGG and FERTILIZER in the same step as the DROP, at the lowest index.

DAYS 12-15 (non-rich towns): keeper only, as the 10th hand ($55): daily feed, care, egg harvest and fertilizer collection on the yard. Tape unchanged.

HANDOVER: see the handover field. Nothing from the layers is pending at handover; the shed holds no animals after the day-10 flush.

### Layers
- **L0 tp_core (infrastructure)** (knob GC_P['tp']=None | {...}; tp_div_only (skip L1/L2 when ADAPT flags a copy by step 143), ~4h): A new wrapper inserted right before `_GC_PARENT = agent` (full_T7.py ~line 11779; source gold/top10/full/ctl_top3.py), so it runs only while the dispatcher still calls the tape chain (before handover). Knobs: GC_P['tp'] = None (default) or a dict of sub-knobs. It provides five things. (1) R(s): the tape's remaining same-day buys minus 0.7 x its planned sells, plus next-morning wages and $100. Read from _IMPL.chassis.routes[route] and chassis.future_sells. (2) A tile-rewrite hook: rewrite a tape unit's op when that unit stands on a target tile. (3) A strip/defer queue for tape market orders, with earliest and latest steps. (4) A keeper framework copied from _v219_request/_v219_worker and _v233_request (full_T7.py 1313-1445, 2022-2100): hire only after the tape's last HIRE of the day, check len(farm.hands) + parent_hires == expected, and give keepers indices > the tape's count. (5) Market-list assembly: SELLs, then tape HIREs, then layer HIREs, then BUY_LAND, then tape buys, then layer buys, never above 10 orders (layer orders are dropped first and retried next step). It also adds per-player state and telemetry counters: fired, bounced tape orders, stray land, order-cap drops, keeper wages, yard escapes. With tp=None it must be bit-identical to T7. Touches: None by itself. It only filters the final market list (index order, 10-order cap).
- **L3 tp_nw4 (early NW strawberries on the feed-wheat tiles)** (knob tp.nw4 = 0..3 (tiles); tp.nw4_order = [(1,0),(0,1),(0,0)], ~2h): Day 4: buy up to 3 strawberry seeds at step 105 (guard; T7's lowest cash on day 4 is $340). Rewrite the tape's day-4 PLANT WHEAT on NW (1,0) (hour 11), (0,1) (hour 10) and (0,0) (hour 15) into PLANT STRAWBERRY, in that priority. (1,0) is the tape's own day-7 strawberry tile, so it is pulled 3 days earlier with no volume change (strip 1 day-7 seed). (0,0) and (0,1) add 2 tiles harvested on days 14-20, near the price peak. The tape's continuing wheat cycle on these tiles waters them at intervals of 2 days or less until handover. Tape HARVESTs there (day 15) collect any strawberry units; the layer sells surplus shed STRAWBERRY. The lost feed wheat is covered by the existing feed-reserve layers buying wheat. Touches: Day-4 PLANT WHEAT on (1,0), (0,1), (0,0) become PLANT STRAWBERRY. Injects BUY_SEED STRAWBERRY at step 105. Strips 1 unit of the day-7 BUY_SEED STRAWBERRY and up to 3 day-4 wheat seeds. Later tape HARVEST/PLANT on those tiles become no-ops; its WATERs keep working.
- **L1 tp_ne6 (NE strawberries sized by strawberry buyers)** (knob tp.ne6 = True/False; tp.ne6_extra = True/False; b6 >= 1 gate, ~2h): Day 6, only when b6 >= 1 and the rival is not a copy. Buy strawberry seeds from step 151 under the guard (lowest day-6 cash is $709). Rewrite the tape's day-6 PLANT WHEAT on NE (5,0), (6,0), (7,0) and (7,1) (hours 16-22), which are the tiles of the tape's own day-8 strawberry batch, into strawberries 2 days earlier. Then strip the matching day-8 strawberry seed buys (steps about 201-208): +$400 of day-8 cash, which helps SW. With b6 = 2 and ne6_extra on, also convert (8,0), (9,0) and (9,1) (continuous NE feed wheat): +3 tiles, matching the elite's +7 strawberries per buyer. The tape waters on days 6-8 and then adopts the tiles as its day-8 strawberries. The first production is day 16 (handover in non-copy games), so no layer fertilizing is needed. Touches: Day-6 PLANT WHEAT on 4 (+3) NE tiles become PLANT STRAWBERRY. Injects BUY_SEED STRAWBERRY on day 6. Strips day-8 BUY_SEED STRAWBERRY (up to 4 units) and 4-7 wheat seeds. The tape's day-8 HARVEST/PLANT on those tiles become no-ops.
- **L2 tp_sw (SW land earlier)** (knob tp.sw = None | 'd9' | 'd10' | 'd8', ~2h): Buy SW at the first qualifying step: day 9, hours 8-23, after the wool sale and after reserving the tape's hour-10 sheep and the day-10 morning buys. Otherwise at the first day-10 melon-sale step (hours 9-10, always affordable). Put BUY_LAND after that step's SELLs (the engine runs atomic orders at index i before the per-unit sells at index i, so the sells go at lower indices). Drop the tape's BUY_LAND at step 265 and any later tape BUY_LAND whose quadrant is already owned. Move the tape's day-10 hour-1 GOOSE 2 order to the melon step if cash is short at hour 1. Touches: Removes BUY_LAND at step 265. Injects BUY_LAND on day 9 or 10. May move BUY_ANIMAL GOOSE 2 from step 241 to step 249.
- **L2y tp_yard (geese yard on SW with a keeper)** (knob tp.yard = 0..3 geese; tp.yard_tiles = [(0,5),(0,6),(0,7)], ~5h): On the SW day, the keeper builds COOPs on SW (0,5), (0,6) and (0,7). These are tape wheat tiles, first planted on day 11 at hours 16-23, 4-6 moves from the shed. Buy up to 3 geese under the guard (latest the day-10 melon step) and place them the same day. A daily keeper tour: PICKUP n wheat (bought by the layer the step before if the shed is short), then FEED, CARE, HARVEST eggs and COLLECT_FERTILIZER per coop, then DROP. SELL EGG and FERTILIZER in the same step as the DROP. The keeper is the tape's count + 1 (9th hand on day 9 $34, 12th on day 10 $144, 11th on day 11 $89, 10th on days 12-15 $55), hired until handover-1. Three geese is the capacity of one keeper (about 24-26 turns). Two fixes are needed. First, patch _hd2_decide (full_T7.py 5413), which skips its goose-to-cow/sheep swap when any COOP exists: it must ignore yard tiles, or it changes T7's day-10 decision. Second, if the _v233 sheep layer also commits extra hands (towns with 2 yarn stores), identify keepers by spawn index or skip the yard. Touches: Injects BUILD_COOP, geese buys, keeper HIRE, wheat buys and EGG/FERT sells. Strips 3 day-11 wheat seeds. The tape's day-11+ PLANT/WATER on yard tiles become no-ops; its HARVEST there collects eggs (sold by the layer). _hd2 coop check patched.
- **L2d tp_sw='d8' (SW on milk day, sheep deferred)** (knob tp.sw = 'd8', ~3h): Optional second-round variant. At step 196, SELL MILK 12 plus fertilizer, then BUY_LAND. BUY_ANIMAL SHEEP 2 goes to the deferred queue, bought at the first step where the guard passes (day 9 after the wool at hours 7-8, at the latest the day-10 melon step). Record the tiles where the tape's PLACE SHEEP fails (steps 201 and 213). The keeper PICKUPs the deferred sheep and PLACEs them there; the tape's own FEED/CARE on those pastures then serve them. Yard geese can then start on day 8 (first eggs day 12). Touches: Removes BUY_ANIMAL SHEEP 2 at step 196 (re-injected later). Tape PLACE SHEEP at steps 201/213 fail until the keeper places the sheep. Injects BUY_LAND at step 196.
- **L2b tp_bridge (optional SW wheat bridge)** (knob tp.bridge = True/False, ~3h): Only with 'd8' mode. Plant wheat on the tape's other 9 SW wheat tiles on day 8. Water on day 10 and harvest on day 11 at hours 1-8, at age 3 (3 units), before the tape's PLANT at hours 16-23. About +27 wheat (about $0.9k) against $120 of seed and pricey day-10/11 keeper turns. Build last; drop it if the gate is flat. Touches: None of the tape's own actions change: the tiles are empty again before the tape's day-11 PLANT.

### Handover
Handover days are unchanged:
- controller from day 16 (step 384) against own-plan / divergent rivals;
- day 12 (step 288, rich_start) in strawberry-rich towns;
- day 20 (step 480) against copies.
Earlier takeovers lost before: day 15 -$341, days 12/14 -$957/-$376 against flagged rivals. The controller-run opening lost $18-27k.

Layers act only while the GoldCtl dispatcher still calls the tape chain, because the wrapper sits under `_GC_PARENT`:
- L3 on day 4 and L1 on day 6 finish before any handover;
- L2 finishes by day 10 (deferred queue flushed at the melon step, stray land stripped on day 11);
- the keeper is hired up to handover-1: day 11 in rich towns, day 15 otherwise;
- with tp_div_only (the default for L1/L2), copy games play pure T7 from day 6 and keep the day-20 takeover.

Controller settings are unchanged (the T7 / ctl_top3 knob set). On the handover day the controller inherits:
- 3 extra geese on SW coops;
- 2-3 extra NW strawberries and 4-7 earlier NE strawberries;
- no pending purchases and no animals in the shed.

Its herd buying (herd_kinds COW/SHEEP) never buys geese, but it must tend the yard geese. Verify with a counter: yard escapes on days 16-20 must be 0. Also check that the rich-town classification at step 288 is not flipped by our extra strawberries; log rich_eval both ways on the fire set.

### Expected gain
These are partial-equilibrium upper bounds; about 50-60% usually survives.

Per layer (per seat):
- L1: about +$135-200 a tile for 2 days earlier on 4 tiles in b6 >= 1 towns (74%), plus about +$430-600 a tile for 3 added tiles in b6 = 2 towns (19%). Average about +$0.4-0.7k.
- L3: (1,0) pulled 3 days earlier, about +$250; 2 added strawberries at about +$300-450 each net of feed wheat. About +$0.5-1.0k.
- L2 + L2y: 3 geese bought on days 9-10, worth about $1.2-1.4k each by day 29 (ledger), minus keeper about $0.5k, displaced coop-tile wheat about $0.45k and feed. About +$0.5-1.5k.
- L2d / L2b: each about +$0.2-0.6k more, uncertain.

Totals:
- Against the opening winners (Boey, FQ, CBF, Yizhou, TFC): about +$1.3-3.0k upper bound, so +$1-2k expected. The loss-margin curve (+$1k is about +5 pp, +$3k about +15 pp) puts T7's roughly 38% win rate at about 43-48%. The phase ceiling, if we fully matched their day-16 farm, is +$3.5k.
- Against other own-plan 2600+ agents: the triggers are generic (own cash, shops), so about +$0.8-1.5k and +3-6 pp.
- Against copies: about 0, because L1/L2 are off under tp_div_only. L3 fires before the copy flag and must not lose on live copy games.

These numbers do not close the full $9k day-16 gap. The rest sits behind the melon and denial trade-offs listed in the kill reason.

### Risks
1. **Tape desync.** A rewritten tile must never be one where the tape later BUILDs a structure or PLACEs an animal before handover; otherwise an animal stays in a hand or the shed and escapes. The target tiles were checked against 96 T7 games: NW (0,0)/(0,1)/(1,0) and NE (5,0)/(6,0)/(7,0)/(7,1)/(8,0)/(9,0)/(9,1) only ever hold wheat or strawberries before day 16. Also assert at runtime that the acting unit's tile is in the target set and empty.
2. **Bounced tape orders.** Denial cows, the day-6 NE purchase, the day-7 cows and feed wheat must not fail. L3 and L1 compete for the same days 4-6 slack (lowest $340/$709). The guard must reserve the tape's full remaining day plus next-morning wages. Counter: tape buy failures per day equal T7's.
3. **Stray SE purchase.** The step-265 BUY_LAND with SW already owned would buy SE for $4,000. It must be stripped; also check layers that price land from tape orders (_r97_budget, _y cash, _hd2 at 4000).
4. **10-order cap.** Day 10 hour 0 already has 10 tape orders and day 11 hour 1 has 9. Layer orders go last and retry; counter for dropped orders.
5. **Hand-index collisions.** The _v233 layer hires 2 extra hands on days 11-12 in towns with 2 yarn stores, so both layers can hire in the same step. _hd2 skips its swap when any coop exists, so the yard would change T7's day-10 goose decision. Both need the patches listed in L2y.
6. **Feed.** 3 geese plus 2-3 displaced feed-wheat tiles means about 4-6 extra wheat a day bought at $30-40. If the feed-reserve layers do not see the keeper's need, geese escape. Counter: escapes on days 0-16 must not exceed T7's.
7. **Unsold layer goods.** Eggs, and strawberries the tape harvests on converted tiles, reach the shed with no tape SELL. The layer must sell the surplus or the 100-unit shed overflows.
8. **Market effects.** Earlier and extra strawberries lower both farms' days 14-22 prices (about $1.9 a unit until shops absorb it). The per-tile values assume no price impact, so the gate decides.
9. **Controller interplay.** The controller must tend non-tape geese after handover. Extra strawberries could flip rich_eval at step 288 (straw_our_w 0.9) and move handover to day 12 in some towns.
10. **Copies.** L3 fires before the copy flag (step 143), so it has to be checked on live copy games replayed from day 0-4.
11. **Pinned-rival gates are open loop.** Rivals do not react to our earlier strawberries or eggs, so the closed-loop gate is needed too.
12. **Time.** About 2.5 days remain (deadline 30 Sep 23:59 UTC). If nothing passes by 30 Sep 16:00 UTC, keep the T7/T5 pair.

### Test plan
Work in gold/top10/full/ctl_top3.py (copy it to ctl_tp.py). Put the wrapper right before `_GC_PARENT = agent` with GC_P['tp'] = None. Build with bm5.py using the T7 knob set plus {"tp": {...}}. Name candidates cands/full_T7tp_<variant>.py. Do not touch gold/submit and do not commit.

**0. Identity (30 min).**
- tp=None must be bit-identical to T7 on the ident set (gates/ids_t6c.txt pattern).
- The 96 T7 elite pairings (research/openmine/extract.py, mode ours) must reproduce their rewards exactly.
- Decode the routes with the scratchpad route decoder to confirm the step numbers used here (196, 201-208, 224-226, 241, 249, 265) for every route id the router can pick (0-12, 100-128). Key off the tape's action and unit position, not hard-coded steps, wherever routes differ.

**1. Smoke and diagnostics, per layer (20 elite towns plus 20 goldg seats).** Log per game:
- tiles converted and their day;
- seeds stripped against seeds added (must net to zero on pulled tiles);
- SW day and hour, and cash before and after;
- SE purchases (must be 0);
- tape buy bounces by day (must equal T7);
- dropped layer orders;
- keeper hires and wages;
- geese placed, eggs sold, yard escapes (0);
- escapes on days 0-16 (no more than T7);
- no-op count of tape unit actions on non-target tiles (must equal T7);
- day-16 farm snapshot against T7: strawberries, geese, wheat tiles;
- whether rich_eval flipped.

**2. Gates, paired against T7 on the same games, Kaggle bit-identical, NPROC <= 14 locally.**
- goldg (111 seats; CBF, TFC and Yizhou are here) and top10g (270; Boey and FQ are here). Also report the opening-winner subset split from the gate rows' team field.
- elite gate on the 20 Sep games (210 seats).
- Order of runs: L3, then L1, then L3+L1 (28 Sep evening); L2 'd9'+yard, then all (29 Sep); L2d/L2b only if time.

**3. Live, replayed from day 0-4.**
- pinned4.py on gates/live0927.json and gates/live191.json with start 96, or 0 if a 5-game identity check shows the recorded day 0-3 differ from T7.
- Split with livecmp.py into copy / own / annex and <2600 / 2600+.

**4. Closed loop.** batch4.py against omw_v15a and pub_metav4v13, 200 games each, compared with paired.py. This is where the rival reacts to our earlier strawberries and eggs.

**Acceptance per layer and for the combination:**
- pooled goldg+top10g+elite Δmargin > 0 with z >= 2, and Δwins >= 0;
- opening-winner subset Δmargin > 0;
- live from day 4: Δmargin >= -$150 and copy wins not down by more than 2;
- closed loop not worse than -$150;
- zero regressions on SE, bounces, escapes and the order cap.

**Decision.** Submit the best accepted combination on 30 Sep by about 20:00 UTC as one of the final two, paired with T7 (or T5 if T7's own gates disappoint), so the pair spans tape-plus and pure tape. If only L3+L1 pass, submit that; L2 is not required.
