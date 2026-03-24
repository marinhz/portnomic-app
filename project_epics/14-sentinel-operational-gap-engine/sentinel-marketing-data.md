# Sentinel Module — Marketing Data & Copy

**Product:** The Sentinel — Operational Gap Engine  
**Context:** Part of Portnomic maritime agency SaaS. Target: Maritime agencies (B2B), operations managers, finance controllers.

---

## 1. Taglines & Headlines

| Version | Copy |
|---------|------|
| **Primary** | Four sources. One truth. Zero surprises. |
| **Alt 1** | Catch overcharges before they catch you. |
| **Alt 2** | Cross-check invoices against operational reality. |
| **Alt 3** | Your port call watchdog — 24/7. |
| **Short** | Operational truth, automated. |

---

## 2. Value Propositions

| # | Statement |
|---|-----------|
| VP1 | Cross-references four independent data sources (invoices, SOF, noon reports, AIS) to validate every port call. |
| VP2 | Detects overcharged tug hours, incorrect berthage, and unusual fuel consumption before approval. |
| VP3 | Reduces financial leakage and disputes by surfacing discrepancies in real time. |
| VP4 | Satellite-verified berth times — vendor claims vs. AIS truth. |

---

## 3. Key Features (Feature Bullets)

| Feature | Benefit |
|---------|---------|
| **Temporal Tug/Pilot Audit** | Flags when invoiced tug hours exceed actual SOF timestamps (with buffer). Reduces overcharged service hours. |
| **Berthage/Stay Verification** | Compares invoiced berth days to AIS "at berth" duration. Catches rounding-up errors and billing mistakes. |
| **Fuel Paradox Detection** | Alerts when high fuel consumption doesn’t match operational status (e.g. idle at anchorage). |
| **Unified Timeline** | Normalizes DA, SOF, Noon Report, and AIS into one timeline for side-by-side comparison. |
| **Automatic Triggers** | Runs after each relevant document (DA, SOF, noon report) is parsed — no manual audit needed. |
| **Side-by-Side Audit View** | Vendor claims vs. operational reality vs. variance — all in one view. |

---

## 4. Pain Points Addressed

| Pain | How Sentinel Solves It |
|------|-------------------------|
| Overcharged tug hours | Compares DA line items to SOF tug fast/off timestamps; flags overbilling. |
| Berthage overbilling | Compares invoiced days to AIS berth stay and ETA/ETD; catches 2-day vs 3-day rounding. |
| Manual cross-checking | Automates comparison across invoices, SOF, noon reports, and AIS. |
| Disputes after approval | Surfaces discrepancies before DA approval and payment. |
| No independent verification | AIS provides satellite-derived berth times as an external source. |

---

## 5. Use Cases / Scenarios

### Scenario A: Tug Overcharge
> *"A DA invoices 3 hours of tug service. The SOF shows tug fast at 08:30 and cast off at 09:30 — 1 hour actual. Sentinel flags a High Risk alert: ~€1,700 overcharge."*

### Scenario B: Berthage Rounding
> *"The DA claims 3 days berthage. AIS and ETA/ETD show an actual stay of ~1.2 days. Sentinel flags Incorrect Berthage Calculation."*

### Scenario C: Fuel Anomaly
> *"Noon report shows high fuel burn at anchorage while SOF indicates 12+ hours idle. Sentinel raises Operational Alert for review."*

### Scenario D: Clean Match
> *"Pilotage fee matches SOF pilot on/off. No alert — verification complete."*

---

## 6. Proof Points & Statistics (Marketing Use)

| Stat | Copy / Source |
|------|---------------|
| Overcharge range | Typical tug overcharge: €1,000–€3,000 per incident. |
| Time savings | Reduces manual cross-check from minutes per port call to near-zero. |
| Coverage | Four data sources: Financial (DA), Operational (SOF), Vessel (Noon), External (AIS). |
| Severity levels | Low, Medium, High — prioritize what matters. |
| BYOAI | Uses your tenant LLM keys for privacy and control. |

---

## 7. Differentiators

| Vs. | Sentinel Advantage |
|-----|--------------------|
| Manual checking | Automated; runs on every relevant document. |
| Single-source audit | Four-source cross-reference. |
| Invoice-only tools | Invoices + operational truth (SOF, AIS, noon reports). |
| Post-payment review | Pre-approval flagging. |

---

## 8. Social Media Copy

### LinkedIn (Professional)
- *"New: Sentinel cross-checks your port call invoices against SOF, noon reports, and AIS. Catch overcharges before approval. Four sources. One truth."*
- *"Tug billed for 3 hours, SOF says 1. Sentinel sees it. Every time."*

### Twitter/X
- *Four sources. One truth. Zero surprises. Introducing Sentinel — your operational gap engine.*
- *Invoices vs. reality. Side by side. Automated.*

### Short
- *Sentinel = invoice × SOF × noon report × AIS. Operational truth, automated.*

---

## 9. Email Campaign Snippets

**Subject line ideas:**
- *Stop overcharges before they hit your bottom line*
- *Four sources. One truth. Meet Sentinel.*
- *Your port call watchdog is here*

**Body (short):**
> Sentinel cross-references your Disbursement Accounts with Statement of Facts, noon reports, and AIS. It flags overcharged tug hours, incorrect berthage, and unusual fuel consumption — before you approve.

---

## 10. Landing Page Sections

### Hero
- **Headline:** Four sources. One truth. Zero surprises.
- **Subhead:** Sentinel cross-checks invoices, SOF, noon reports, and AIS to catch overcharges and operational gaps before approval.

### How It Works (3 steps)
1. **Ingest** — DA, SOF, noon reports flow into Portnomic as usual.
2. **Compare** — Sentinel normalizes all data into one timeline and runs the Triple-Check rules.
3. **Alert** — Discrepancies appear in the Port Call dashboard with severity and estimated loss.

### Triple-Check Rules (visual)
- Rule 1: Tug/Pilot audit — DA hours vs. SOF timestamps
- Rule 2: Berthage verification — DA days vs. AIS berth stay
- Rule 3: Fuel paradox — consumption vs. operational status

### CTA
- *See Sentinel in action*
- *Request a demo*
- *Add Sentinel to your plan*

---

## 11. Sales Enablement

### Objection Handling
| Objection | Response |
|-----------|----------|
| "We already review invoices" | Sentinel automates cross-check across four sources. You catch what manual review misses. |
| "We don’t have AIS" | Sentinel uses ETA/ETD as fallback when AIS is unavailable. Still validates against SOF and noon reports. |
| "Too many false positives?" | Configurable buffer (e.g. 0.5h tug) and severity levels keep noise low. |

### Demo Talking Points
1. Show a port call with DA + SOF + discrepancy.
2. Highlight side-by-side view: Vendor Claims | Operational Reality | Variance.
3. Show High/Medium severity and estimated loss (€).
4. Explain automatic trigger — no manual "run audit" step.

---

## 12. SEO Keywords

- Operational gap engine, maritime audit, port call verification
- Disbursement account validation, SOF cross-check, AIS berth verification
- Tug overcharge detection, berthage verification, maritime discrepancy detection

---

*Generated for Epic 14 — The Sentinel: Operational Gap Engine*
