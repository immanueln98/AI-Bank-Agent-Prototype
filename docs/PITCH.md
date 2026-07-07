# Pitching the AI Voice Agent to Banks — Evidence Pack & Talking Points

*Prepared July 2026. Every external claim below carries a source; labels state whether it is
a primary source (the institution/regulator itself), corroborated (multiple independent
outlets), or vendor-reported (treat as directional). Use this document to build the deck —
the claims are safe to repeat in front of a bank's risk team as long as the label travels
with them.*

---

## 1. The pitch in one paragraph

Banks are drowning in routine calls — balances, lost cards, "was this me?" queries — and
every one of them queues behind a human agent. We put an AI voice agent in front of the
call-centre queue that answers instantly, verifies the caller before it says anything about
an account, resolves the routine 30–50% of calls end-to-end, and hands the rest to a human
consultant *with a summary*, so nobody repeats themselves. It never guesses: every answer is
grounded in a call to the bank's own systems, every action is logged to a PII-masked audit
trail, and the things it must never do (move money, give advice) are impossible by
construction, not by instruction.

## 2. Why now — who has already done this (verified deployments)

The strongest slide in the deck is "this is not experimental." Order these by proximity to
our use case:

| Institution | What they run | Scale / outcome | Label |
|---|---|---|---|
| **Wells Fargo (US)** | "Fargo" — voice + text assistant in the banking app (Google Gemini) | 21.3M interactions in 2023 → **245M in 2024**, 336M+ cumulative; **zero PII sent to the LLM** (local speech-to-text + scrubbing/tokenisation before the model) | Corroborated ([VentureBeat](https://venturebeat.com/ai/wells-fargos-ai-assistant-just-crossed-245-million-interactions-with-zero-humans-in-the-loop-and-zero-pii-to-the-llm), multiple outlets) |
| **Bank of America (US)** | "Erica" virtual assistant (text-first, in-app) | **3 billion+ interactions, ~50M users, 58M interactions/month** (Aug 2025); the first billion took 4 years, the pace keeps accelerating; employee variant cut IT service-desk calls 50% | Primary ([BofA newsroom, Aug 2025](https://newsroom.bankofamerica.com/content/newsroom/press-releases/2025/08/a-decade-of-ai-innovation--bofa-s-virtual-assistant-erica-surpas.html)) |
| **Bank of America** | Erica-family deflection metrics | CashPro Chat: **43% containment**; Erica for Employees: **55% drop** in help-desk calls; leadership: "equivalent work of 11,000 employees" | Reported ([American Banker](https://www.americanbanker.com/news/how-bank-of-americas-erica-does-the-work-of-11000-people)) |
| **NatWest (UK)** | "Cora" / gen-AI "Cora+" (IBM watsonx, RAG) | ~11M queries in 2023 (up from 5M in 2019); Cora+ pilot: **up to 150% improvement in satisfaction** on some question types; auto-summary handed to human agents on transfer | Primary ([NatWest Group press release, Jun 2024](https://www.natwestgroup.com/news-and-insights/news-room/press-releases/data-and-technology/2024/jun/natwest-launches-cora-plus-the-latest-generative-ai-upgrade-to-t.html)) |
| **UK & EU banks (unnamed), via PolyAI** | Customer-facing **voice** assistants on the phone line — the closest match to this POC | A savings bank **resolves 30% of calls** fully in the voice channel; Atos contact centres: workload of **50–95 FTE** at ~50% of FTE cost | Vendor-reported ([PolyAI case studies](https://poly.ai/case-studies/savings-bank/), [Atos](https://poly.ai/customers/atos)) |
| **DBS (Singapore)** | Gen-AI "CSO Assistant" — agent-assist for 500 call-centre staff serving 250k+ customer queries/month | Expected **up to 20% lower handle time**; ~90% of pilot agents reported positive impact | Primary ([DBS newsroom](https://www.dbs.com/newsroom/DBS_empowers_its_Customer_Service_Officers_with_Gen_AI_powered_virtual_assistant_to_reduce_toil_and_enhance_customer_experience)) |

**How to use this honestly:** Erica and Cora are chat-first (they prove *appetite and scale*
in retail banking); Fargo proves *voice + privacy architecture at massive scale*; the PolyAI
deployments prove *containment on the actual phone line*; DBS proves the *human-assist*
variant. Our proposal is the PolyAI-shaped deployment with the Wells-Fargo-shaped privacy
posture.

**South Africa specifically:** the SARB Prudential Authority & FSCA's joint AI report
(Nov 2025, ~2,100-firm survey) found **banks are the sector's leading AI adopters (~52%)**
and chatbot-style customer engagement is among the leading use cases — so a bank hearing
this pitch is likely already running conversational AI in text and knows its limits
([SARB/FSCA joint report, primary](https://www.resbank.co.za/content/dam/sarb/publications/prudential-authority/pa-public-awareness/covid-19-response/2025/artificial-intelligence-in-the-south-african-financial-sector/Artificial%20Intelligence%20in%20the%20South%20African%20Financial%20Sector.pdf),
[ENSafrica summary](https://www.ensafrica.com/news/detail/11119/fsca-and-prudential-authority-publish-landmar)).

## 3. The numbers a COO/CFO cares about

- **Containment (deflection):** the share of calls fully resolved without a human. Voice
  deployments in banking credibly reach **30%+ at launch** (PolyAI savings bank) and vendors
  claim 50%+ at maturity. Pitch conservatively: *"every 10 points of containment on N daily
  calls is X consultant-hours returned to complex work."*
- **Queue absorption, not headcount cuts** (see §6 — the CBA cautionary tale): the agent
  answers **instantly at unlimited concurrency**, so overflow spikes (payday, fraud waves,
  outages) stop producing 40-minute hold times.
- **Handle-time on escalated calls falls too**: the human receives a verified caller plus a
  structured summary (NatWest's Cora+ does exactly this; our escalation tool already sends
  reason + summary + ticket reference).
- **Our POC's Supervisor dashboard measures these same KPIs live** — containment rate,
  average handle time, escalations, security lockouts — so the pilot's success criteria are
  agreed *before* it starts and read off the same dashboard during it.

## 4. Security: what we guarantee and how (the section the risk team reads)

Frame every guarantee as **structural (can't) beats procedural (won't) beats prompt
("please don't")**. Our POC demonstrates each layer working — this is not a slideware
architecture.

1. **Identity before information — structurally.** Before verification the agent literally
   has no account tools; a prompt injection cannot call a tool that does not exist. Three
   failed attempts locks account help for the call (a first-class `security_lockout` audit
   event) and routes to a human. In production, verification plugs into the bank's real
   flows: OTP to the registered device or app-push approval, with **step-up authentication**
   for sensitive actions.
2. **No money movement, structurally.** There is no transfer/payment tool on any agent. The
   demo's guardrail scenario shows the refusal live. Capability expansion is a governance
   decision the bank makes per-tool, with step-up auth — not a model behaviour.
3. **PII never reaches logs, transcripts, or the browser unmasked** — known values (the
   account number the caller just said) are masked exactly, plus regex safety nets for SA
   ID/Omang/account shapes. **Precedent that this posture scales: Wells Fargo runs 245M
   interactions/year with zero PII sent to the LLM** (local transcription + scrubbing before
   the model). Same pattern, same seam.
4. **Grounded answers only.** The agent may only state account facts returned by the bank's
   own API in that call; every tool call is visible live in the activity panel and retained
   in the masked audit trail. This is the direct answer to *Moffatt v Air Canada* (see §6).
5. **Complete, tamper-evident audit trail.** Every session leaves a masked JSONL transcript
   and posts a structured call record — outcome, verification attempts, every tool call with
   masked arguments, escalation reference — queryable per call on the Supervisor view.
   POPIA data-subject requests and QA replay use the same artefact.
6. **Human escalation is a feature, not a failure.** Explicit escalation tool, warm-handoff
   summary, amber banner in the console. The EU AI Act's Article 50 duty (tell people they
   are talking to an AI) is already satisfied by our fixed, deterministic opening disclosure
   — deterministic because it's `session.say()`, not LLM-generated.
7. **Deployment isolation & residency.** POC runs on LiveKit Cloud free tier; production
   options are self-hosted LiveKit + VPC/in-country model inference for strict POPIA
   cross-border postures. Enterprise LLM API terms exclude customer data from model
   training — put the bank's data processing agreement on the table early.
8. **PCI DSS for card data.** Card numbers/CVV must never enter recordings or transcripts:
   the PCI SSC's telephone-payment guidance requires that recordings not retain validation
   codes post-authorisation and endorses DTMF masking ("type your card number on the
   keypad") — LiveKit SIP supports DTMF, so payment capture bypasses the transcript entirely
   ([PCI SSC guidance, primary](https://listings.pcisecuritystandards.org/documents/protecting_telephone-based_payment_card_data.pdf)).
9. **We deliberately do NOT authenticate by voice.** AI voice cloning defeated a major UK
   bank's voice-ID in a 2023 journalist demonstration
   ([Biometric Update](https://www.biometricupdate.com/202302/journalist-uses-ai-voice-to-break-into-own-bank-account)),
   and the SARB/FSCA report flags deepfake audio as a live consumer-protection risk. Saying
   "we treat the voice channel as untrusted and verify with possession factors" *earns
   credibility* — it shows the design assumed the adversary has AI too.

## 5. Regulatory landscape (South Africa first)

- **No AI-specific law blocks this today.** SA regulates AI in finance through existing
  technology-neutral frameworks (FAIS, POPIA, prudential standards). The SARB PA + FSCA
  joint report (24 Nov 2025) is guidance, not new rules; a discussion paper on supervisory
  questions is the stated next step. The national AI policy direction is to strengthen
  existing sectoral laws, with SARB/FSCA as the finance-sector AI authorities — not a
  standalone AI Act ([SARB/FSCA report, primary](https://www.resbank.co.za/content/dam/sarb/publications/prudential-authority/pa-public-awareness/covid-19-response/2025/artificial-intelligence-in-the-south-african-financial-sector/Artificial%20Intelligence%20in%20the%20South%20African%20Financial%20Sector.pdf),
  [Michalsons overview](https://www.michalsons.com/focus-areas/artificial-intelligence-law/south-african-ai-policy-guidance-and-overview)).
- **POPIA is the operative law.** It already governs AI processing of personal data,
  automated decision-making, profiling, and cross-border transfers. **Section 71** restricts
  significant decisions made *solely* by automated processing — our agent executes service
  requests (check balance, block card, open dispute) and makes no credit or adverse
  decisions; anything judgement-shaped goes to a human. Say that sentence verbatim in the
  pitch.
- **Governance expectations from the regulators** (board-level oversight, model risk
  management, explainability, disclosure when AI is involved): our audit trail, eval suite,
  and deterministic disclosure line map onto each expectation — bring the mapping as an
  appendix slide ([ENSafrica summary](https://www.ensafrica.com/news/detail/11119/fsca-and-prudential-authority-publish-landmar)).
- **EU AI Act (if the bank has EU exposure):** customer-service AI is limited-risk;
  Article 50 requires disclosure of AI interaction — already built in
  ([A&O Shearman analysis](https://www.aoshearman.com/en/insights/ao-shearman-on-tech/zooming-in-on-ai-11-eu-ai-act-what-are-the-obligations-for-the-limited-risk-ai-systems)).

## 6. Objections to own before the bank raises them

- **"What if it makes something up?" — *Moffatt v Air Canada* (2024):** a tribunal held Air
  Canada liable for its chatbot's invented bereavement-fare policy; "the AI said it, not us"
  failed as a defence ([Research ICT Africa](https://researchictafrica.net/2024/02/28/misleading-chatbots-corporate-responsibility-and-the-myth-of-unregulated-ai/)).
  Own it: *the bank is liable for what the agent says, which is exactly why answers are
  grounded in system calls, policy questions come from the bank's approved FAQ corpus, and
  everything else escalates.* Then show the activity panel proving where each answer came from.
- **"Will this let us cut staff?" — the CBA cautionary tale (Aug 2025):** Commonwealth Bank
  of Australia declared 45 call-centre roles redundant citing its voice bot, call volumes
  rose instead, and CBA publicly reversed and apologised
  ([ACS Information Age](https://ia.acs.org.au/article/2025/cba-reverses-ai-driven-job-cuts--admits--error-.html)).
  Position accordingly: *this absorbs overflow and growth so your people handle the complex,
  revenue-relevant conversations — headcount decisions come after the containment data, not
  before it.* This framing also defuses union/works-council friction.
- **"Can someone deepfake their way in?"** Voice is treated as untrusted input (see §4.9);
  verification is knowledge/possession-based today and plugs into the bank's OTP/app-push in
  production. The AI answering the phone doesn't weaken caller authentication — it
  standardises it: the agent *never* skips the check, no matter how good the sob story, and
  every attempt is logged.
- **"What about our data training someone's model?"** Enterprise API terms + DPA; no
  training on customer data; in-country/VPC inference available for strict residency. This
  is a contracts conversation, not a research problem.
- **"Languages and accents?"** Multilingual STT/TTS is config, but *don't overclaim*:
  position isiZulu/Afrikaans/Setswana coverage as an evaluation-gated rollout with per-
  language accuracy testing — banks respect a measured answer more than a checkbox.

## 7. What the live POC now demonstrates (map demo beats to buyer concerns)

| Buyer concern | Demo beat |
|---|---|
| "Will it leak account data?" | Ask for a balance before verifying → refusal; activity panel shows zero account calls. Fail verification 3× → red **Security lockout** event, human-only path |
| "Are answers real or hallucinated?" | Every answer's tool call streams into the activity panel with masked args + result |
| "What does my supervisor see?" | **Supervisor view**: containment %, avg handle time, escalations, lockouts; per-call drill-down into the masked audit trail |
| "What happens when it can't help?" | Escalation with ticket ref + handover summary; amber banner; outcome recorded as escalated, not contained |
| "What breaks when your backend is down?" | Kill the mock bank mid-call → agent apologises and offers a human (timeouts/retries/fallback lines are built) |
| "Is the caller told it's an AI?" | Deterministic opening disclosure on every call |

## 8. Suggested 10-minute pitch arc

1. **The queue problem** (their numbers: call volumes, hold times, cost per call) — 1 min.
2. **Live call, happy path** (Thabo: verify → balance → salary) with the activity panel
   visible the whole time — 2 min.
3. **The refusals** (balance before verify; transfer request; 3× failed verify → lockout) —
   this is the security pitch, shown not told — 2 min.
4. **Escalation** (Sipho: advice refusal → human handoff with summary) — 1 min.
5. **Switch to Supervisor view**: "here's the dashboard your ops team gets" — containment,
   AHT, the audit trail of the call we just made — 2 min.
6. **The evidence slide** (§2 table) + security guarantees one-pager (§4) — 1 min.
7. **The ask**: a scoped pilot on one call type (e.g. card blocks) with agreed containment/
   CSAT success criteria read off this same dashboard — 1 min.

## 9. Roadmap items worth mentioning (each maps to a §4 guarantee)

- Real SIP telephony + warm transfer into the existing contact-centre queue (LiveKit native).
- OTP/app-push verification + step-up auth for sensitive actions.
- DTMF capture for anything card-number-shaped (PCI posture, §4.8).
- Language expansion behind per-language STT evaluation gates.
- Eval suite in CI against recorded (masked) conversations; the behavioral tests already run
  LLM-judged assertions on refusals and escalations today.

---

## Appendix: source-verification status

The research sweep extracted claims with sources; an adversarial verification pass could not
complete (rate limits), so claims were spot-checked manually instead. Status:

- **Verified against primary source:** BofA Erica scale (newsroom release); NatWest
  Cora/Cora+ (press release); DBS CSO Assistant (newsroom); SARB/FSCA joint report contents
  (report PDF); PCI SSC telephone guidance (PDF); EU AI Act Art. 50 (law-firm analysis of
  the Act text).
- **Corroborated by multiple independent outlets:** Wells Fargo Fargo 245M/zero-PII
  (VentureBeat original + several secondary reports); Lloyds voice-ID bypass (Vice
  reporting, covered by Biometric Update, IT Brew, others); CBA reversal (ACS Information
  Age and mainstream Australian press).
- **Vendor-reported (use as directional, attribute in-slide):** PolyAI containment figures;
  "50%+ containment at maturity" claims.
- **Single-outlet reported (attribute explicitly):** American Banker's Erica deflection
  figures and "11,000 employees" quote.
