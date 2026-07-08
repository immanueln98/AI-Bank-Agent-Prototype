# Pricing Strategy — AI Voice Agent for Banks in South Africa & Botswana

*Prepared July 2026 from a deep-research sweep (25 sources fetched, 25 claims adversarially
verified 3–0) plus derived modelling. Labels follow PITCH.md's convention — **primary**
(institution/regulator itself), **corroborated** (multiple independent outlets),
**vendor-reported** (directional), **estimate/derived** (our arithmetic or assumption; verify
before quoting to a bank). FX assumptions used throughout: **R18/USD, P13.5/USD, 1 BWP ≈
R1.33** — update before reuse.*

---

## 1. Recommendation in one paragraph

Sell the way the market already buys: **custom-quoted annual contracts with a usage
component**, anchored on the bank's cost per human-handled call. Concretely: a **paid pilot**
(fixed fee, one call type, success criteria read off the Supervisor dashboard), converting to
an **annual platform fee + per-contained-call usage fee** with volume tiers. Price South
Africa and Botswana differently: SA banks have effectively unlimited budget for this
(R5.8–14bn annual IT spend each) but demand onshore hosting and long procurement; Botswana
banks are highly profitable but tiny — their entire annual digital budget is tens of millions
of pula, so they get a lighter, cheaper tier served from South African cloud regions. Unit
economics support this comfortably: our variable cost is **cents (USD) per call-minute**
while a human-handled call costs the bank **rand, an order of magnitude more** — there is
wide room to price well below the human baseline and still hold 40–60% gross margins.

## 2. What the market charges (vendor precedents)

| Vendor | Model | Price points | Label |
|---|---|---|---|
| **PolyAI** (closest archetype: voice AI for banks) | Per-minute, all-in (maintenance + improvements + 24/7 support bundled); custom-quoted, no published tiers | ~$0.90–1.00/min reported; entry ACV ~$150k/yr (third-party estimates) | Primary for the model ([poly.ai/pricing](https://poly.ai/pricing), fetched 2026-07-08); vendor-reported/blog for the price points |
| **Sierra AI** | Outcome-based (per resolved conversation); negotiated definitions — can bill even on transfer to human | ~$150k/yr entry; year-one $200–350k incl. $50–200k implementation; enterprise $400–700k+ | Blog/third-party (Quiq, Retell analyses) — unverified, directional |
| **Kore.ai** | Session-based billing + enterprise licence | Enterprise deals ~$300k/yr | Blog/third-party |
| **Decagon** | Platform fee (~$50k) + per-conversation usage | Year-one $70–100k (pilot) to $95–591k (enterprise) | Blog/third-party |
| **Intercom Fin / Salesforce Agentforce** (chat-first reference points) | Per-resolution $0.99 (Fin); per-conversation $2 (Agentforce) | Public list prices | Corroborated |
| **Replicant** | Usage-based voice automation | Six-figure annual contracts typical | Blog/third-party |

What survives adversarial verification: **PolyAI's per-minute, bundled, quote-only model**
(3–0, live fetch of their pricing page) and the fact that **no enterprise voice-AI vendor
publishes prices** — custom quoting is the norm, which means we are free to price per market.

**Takeaways for us:**

- Per-minute or per-outcome are both proven; **per-contained-call is the better story for a
  bank COO** because it bills only on success and maps 1:1 to the savings calculation
  (Sierra's trick of billing on escalations too is exactly what buyers complain about).
- A **platform fee + usage** structure (Decagon's shape) protects us from low-volume pilots
  bleeding us dry and gives the bank cost predictability — cap the usage component or offer
  committed-volume tiers, since "per-conversation exposes you to volume spikes" is a known
  buyer objection.
- US/UK entry ACVs (~$150k ≈ R2.7m) calibrate the ceiling, not the target — SA pricing should
  land below that per bank at pilot stage, and Botswana far below.

## 3. What banks spend today — the savings baseline

### South Africa

- **Human agent base salary:** R74k–94k/yr (Indeed: R6,174/mo across ~1,800 self-reported
  salaries, Jun 2026; PayScale: R94,129/yr, 301 profiles; entry-level R61k). *Corroborated,
  but self-reported aggregators, not bank-specific — bank in-house agents likely earn more,
  making this a conservative floor.* Fully loaded (benefits, management, facilities,
  telephony, typically 1.5–2.0×): **R110k–190k/yr ≈ R9k–16k/month**. *Loading multiplier is
  an estimate — no SA-specific benchmark survived verification.*
- **Cost per human-handled call (derived):** at ~7 min of agent time per call (5 min AHT +
  wrap) and ~70% occupancy, one agent handles ~900–1,100 calls/month → **≈ R10–18 per call**;
  global outsourced benchmarks of $0.50–1.50/call (≈ R9–27) bracket the same range.
  *Derived + blog benchmark; the 5-min AHT is an assumption — no verified banking AHT claim
  survived.* Use **R12–25/call** in front of a bank and invite them to substitute their own
  number — the pitch is stronger with their data.
- **Ability to pay:** the six major banks earned R152.5bn combined headline earnings in
  FY2025 at a 51% cost-to-income ratio, with PwC reporting management explicitly prioritising
  "reinvention of operational models, not just incremental efficiency" and naming automation
  and AI-enabled productivity as focus areas (*primary — PwC Major Banks Analysis, Mar
  2026*). Individual bank IT budgets: FirstRand R12.4bn, Standard Bank R14.1bn
  "cloud, software and technology" in FY2025 (+8.7% YoY), Nedbank R6.6bn ex-staff, Absa
  R5.8bn ex-staff, Capitec ~R1bn (*secondary — TechCentral from annual reports; Capitec is an
  order of magnitude smaller — expect lower willingness to pay despite 24.1M customers*).
- **The savings pitch (derived):** a bank handling 200k calls/month at R15/call spends
  ~R36m/yr on those calls. 40% containment returns **~R14m/yr** — an AI contract at R6–10m/yr
  is a clear win on paper, and a rounding error inside a R6–14bn IT budget.

### Botswana

- **Market size:** 9 commercial banks, P144bn total assets, P4.1bn aggregate net profit
  (+31.7%), sector RoE 27.3% — but total industry employment is only **5,293 people**
  (*primary — Bank of Botswana Banking Supervision Annual Report 2024*). The displaceable
  contact-centre headcount is a small fraction of that.
- **Staff cost ceiling:** industry average P553.5k/employee/yr (~P46k/month) across all roles
  including management (*primary — BoB, Table 2.10*); FNB Botswana P942m for 1,628 employees
  (~P579k avg, includes a one-off P42m separation cost) (*primary — FNBB IAR FY2025*).
  Contact-centre agents earn well below these all-roles averages — treat P15k–25k/month
  loaded as the working range (*estimate*).
- **Anchor prospects:** FNB Botswana — largest bank (753k+ clients, P1.884bn PBT, RoE 33.5%,
  CIR 47.5%), and **explicitly scaling its 24/7 toll-free Contact Centre** to pull traffic out
  of branches, including a legacy-telephony replacement in FY2025 (*primary — FNBB IAR*).
  That is a funded strategic priority we ride on, not a budget line we must create. Absa
  Botswana: P1.06bn PBT, CIR 49.7% — but disclosed **digital spend of just BWP 43m in 2024
  (BWP 100m planned 2025)** (*primary — BSE filing; management infographic figure*).
- **The hard constraint:** a Botswana bank's entire annual digital budget is tens of millions
  of pula. A voice-agent contract must fit inside it — realistically **BWP 300k–1.5m/yr ACV**
  (~R0.4–2m), an order of magnitude below SA deal sizes. Botswana is a real but *second*
  tier: high margins, low absolute revenue, and a lighthouse-reference play for the SADC
  region.

## 4. Regulation shapes the architecture, and the architecture shapes the price

- **In force (SA):** SARB Prudential Authority Directive D3/2018 — banks *may* use cloud and
  offshore data under a risk-based governance regime (board-approved policy, due diligence,
  notification of material arrangements). No blanket residency mandate today. But
  "offshoring" is defined as *any* storage or processing outside SA — a vendor running STT or
  LLM inference on US/EU endpoints drags the bank into the full D3/2018 compliance workload
  (*primary — SARB directive; still operative per FSCA/PA Joint Communication 2 of 2025*).
- **Proposed (SA, not yet final):** SARB's March 2025 NPS consultation proposes **prior SARB
  approval** for cloud use by payment institutions and **in-country hosting for critical
  payment data** (*primary — SARB consultation paper; contested by industry; whether
  customer-service call data is "critical payment data" is arguable*). Direction of travel is
  clear even if the final rule softens.
- **Botswana:** Data Protection Act 18 of 2024 permits cross-border transfer to adequate
  jurisdictions or under contractual safeguards — hosting Botswana bank workloads in SA cloud
  regions (there is no in-country hyperscaler) is legally feasible (*secondary — legal
  analyses; no verified claim on banking-specific rules — confirm with local counsel*).
- **Pricing consequence:** SA deployments should be **quoted assuming onshore single-tenant
  hosting** (AWS af-south-1 / Azure South Africa North / Teraco colo) and a 6–12 month
  procurement cycle — that's a premium tier, not an option. Botswana deployments can share
  SA-hosted infrastructure — that's what makes a cheap Botswana tier economically possible.
  Offering both proves the "Wells-Fargo-shaped privacy posture" story from the pitch deck.

## 5. Our production cost model

### Variable cost per AI call-minute (managed-API stack, list prices)

| Component | Rate | Per call-minute | Label |
|---|---|---|---|
| STT — Deepgram Nova-3 streaming | $0.0048/min ($0.0042 Growth tier) | $0.0048 | Primary (deepgram.com/pricing, fetched 2026-07-08) |
| TTS — Cartesia Sonic 3 | $0.035/1k chars (~300 agent-spoken chars per call-min) | ~$0.011 | Secondary (softcery.com tracker) + derived speaking-rate assumption |
| LLM — Claude Haiku 4.5 | $1 in / $5 out per MTok; ~50k in + 1.5k out per 5-min call, before caching | ~$0.012 | Primary (Anthropic pricing) + derived token assumption; prompt caching cuts the input side up to ~90% |
| LiveKit compute — self-hosted on k8s | 4-core/8GB agent server handles 10–25 concurrent calls (primary — LiveKit docs) | <$0.005 | Derived; excludes SFU/TURN sizing (no verified claim — model separately) |
| Bandwidth/egress | ~0.75MB/min voice; AWS egress $0.05–0.09/GB US-rate floor (af-south-1 prices higher, unverified) | <$0.001 | Blog + derived |
| SIP telephony (SA) | SA VoIP market rates ~R0.27–0.40/min fixed, R0.45–0.80/min mobile; Telviva/Wanatel are quote-only | $0.015–0.044 (R0.27–0.80) | Secondary; **often the largest single line — get real quotes** |
| **Total variable** | | **≈ $0.05–0.08/min ≈ R0.90–1.50/min** | Derived |

Cross-check: Deepgram's fully-managed Voice Agent API benchmark is **$0.065–0.163/min**
all-in (*primary*), and an independent 2026 tracker puts production voice-agent stacks at
$0.05–0.10/min for cost-effective builds (*blog*) — our BYO-stack estimate sits exactly in
that corridor. **Per 5-minute contained call: ≈ R4.50–7.50 (~$0.25–0.42).**

Strict-residency variant (self-hosted open models on GPUs in af-south-1/Teraco for banks that
demand zero external inference): no cost claims survived verification — price this tier
cost-plus after a real GPU quote, and expect it to be a premium (*gap flagged in research*).

### Fixed costs (startup side, per year — all estimates, no verified claims)

| Line | Estimate (ZAR/yr) |
|---|---|
| Onshore cloud per single-tenant SA bank deployment (HA, staging + prod) | R300k–700k |
| Shared multi-tenant cluster serving Botswana tier | R150–300k total |
| Security & compliance: annual pen test, ISO 27001 path over ~2 yrs, POPIA/DPA counsel | R500k–1.2m |
| Lean team (3–5 engineers incl. on-call) | R3–6m |
| **Break-even revenue (derived)** | **≈ R5–9m/yr** — one mid-volume SA bank contract, or one SA pilot-to-production plus 2–3 Botswana banks |

## 6. Recommended pricing

### South Africa (onshore, single-tenant)

| Stage | Price | Rationale |
|---|---|---|
| **Pilot** (10–12 weeks, one call type e.g. card blocks, success criteria on the Supervisor dashboard) | **R250k–450k fixed** (~$14–25k) | Matches global pilot norms (Decagon $70–100k Y1 is the ceiling); enough to be taken seriously in bank procurement, small enough to sign without board approval |
| **Platform fee** | **R1.2m–2.4m/yr** (~$65–130k) | Covers single-tenant onshore hosting, compliance artefacts, support — below PolyAI's ~$150k US entry, defensible for African market |
| **Usage** | **R8–12 per contained call** (≈ R1.60–2.40/min at 5-min AHT), volume-tiered down to ~R6 | Bills only on success; sits at 40–70% of the R12–25 human cost per call, so every contained call is visibly cheaper than the status quo; 40–65% gross margin over R4.50–7.50 COGS |
| Escalated calls | Free or nominal (R1) | The warm-handoff summary still saves handle time, but not charging for escalations kills the Sierra objection |

**Scenario table (derived; 5-min AHT, R10/contained call blended, tiering to R7 at high
volume; COGS per call falls with volume — list rates → Deepgram Growth tier, prompt caching,
negotiated telephony):**

| Contained calls/mo | Our revenue/yr (usage + R1.8m platform) | COGS/call assumed | Our gross margin | Bank's avoided human cost/yr (@R18/call) | Bank's net saving |
|---|---|---|---|---|---|
| 25,000 | R4.8m | R6.00 | ~62% (≈52% after dedicated hosting) | R5.4m | ~11% + queue absorption |
| 100,000 | R13.8m | R5.00 | ~57% | R21.6m | ~36% |
| 500,000 (tiered to R7/call) | R43.8m | R4.00 | ~45% | R108m | ~59% |

*Margin sensitivity: if COGS stays at the R6/call list-price level, the 500k tier collapses
to ~18% gross margin — the volume tiers are only viable with enterprise rates locked in
first. Sequence the Deepgram/Anthropic/telephony enterprise negotiations before offering the
R7 tier.*

The savings story strengthens with scale — lead the pitch with the 100k+ scenario, price the
pilot to prove containment on one call type first. (At low volumes the saving is mostly
*queue absorption*, not net cost — say that honestly; it defuses the CBA-style headcount
objection from PITCH.md §6.)

### Botswana (shared SA-hosted infrastructure, lighter tier)

| Stage | Price | Rationale |
|---|---|---|
| **Pilot** | **BWP 120k–250k fixed** (~$9–19k) | Fits inside a BWP 43–100m digital budget without board escalation |
| **Platform fee** | **BWP 250k–600k/yr** (~$19–45k) | Shared infra makes this margin-positive despite small size |
| **Usage** | **BWP 5–8 per contained call** (≈ R6.65–10.65) | Same per-call logic against a P8–15 human cost per call (*estimate from P15–25k/mo loaded agent cost*) |
| Realistic ACV | **BWP 0.5–1.5m/yr** per bank | FNBB at ~20k contained calls/mo lands ~BWP 1.5–2m — cap it there |

Botswana margins are high (same shared COGS, BWP pricing ≈ SA pricing per call) but absolute
revenue is capped by market size — value it as reference logos and SADC expansion proof, with
FNB Botswana the anchor target given its stated contact-centre strategy.

### Structural rules (both markets)

1. **Never publish prices** — the entire competitive set is quote-only; publishing removes
   negotiating room and anchors Botswana against SA.
2. **Bill on containment, not on attempts** — it maps to the dashboard the bank already
   agreed to judge the pilot on.
3. **Commit-and-tier** — annual committed volume with tiered overage, so the bank gets
   predictability and we get revenue floor.
4. **Charge separately for the strict-residency GPU tier** — cost-plus after real quotes;
   don't fold an unpriced GPU commitment into standard tiers.
5. **Telephony at cost + margin as a pass-through line** — rates are quote-only (Telviva,
   Wanatel) and per-second billed; don't let an unknown eat the margin.

## 7. Gaps and open questions (be honest about these in any board pack)

- **No verified SA bank call volumes or seat counts** — the savings model has solid salary
  inputs but assumed volumes; get the bank's own numbers in the first meeting (the pitch is
  designed to ask for them — PITCH.md §8 step 1).
- **AHT of 5 minutes is an assumption**; billing is per-second/per-minute sensitive to it.
- **PolyAI's ~$0.95/min and all competitor ACVs are third-party estimates**, not vendor
  filings.
- **No verified af-south-1/Teraco/GPU/ISO-27001 cost claims** — fixed-cost table is
  estimates; replace with quotes before committing margins to investors.
- **SARB NPS localisation proposal is not final** — re-check before hard-committing the
  onshore-only architecture premium.
- FX rates and the Deepgram/Anthropic list prices are point-in-time (July 2026); enterprise
  and data-residency rates are negotiated separately.

---

## Appendix: primary sources

- PolyAI pricing page — https://poly.ai/pricing (fetched live 2026-07-08)
- PwC Major Banks Analysis (Mar 2026, FY25) — https://www.pwc.co.za/en/publications/major-banks-analysis.html
- SARB PA Directive D3/2018 — https://www.resbank.co.za/en/home/publications/publication-detail-pages/prudential-authority/pa-deposit-takers/banks-directives/2018/8749
- SARB Cloud & Data Offshoring consultation (Mar 2025) — resbank.co.za (doc-for-comments-2025)
- Bank of Botswana Banking Supervision Annual Report 2024 — bankofbotswana.bw
- FNB Botswana Integrated Annual Report FY2025 — fnbbotswana.co.bw
- Absa Bank Botswana Integrated Report 2024 — BSE filing 5774
- LiveKit self-hosted deployment docs — https://docs.livekit.io/deploy/custom/deployments/
- Deepgram pricing — https://deepgram.com/pricing (fetched live 2026-07-08)
- TechCentral SA bank IT spend series; PayScale/Indeed SA salary data; softcery.com voice-agent cost tracker (secondary)
