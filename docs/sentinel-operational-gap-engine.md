# Technical Specification: "The Sentinel" Operational Gap Engine

## 1. Objective

To create a pro-active validation layer that cross-references four independent data sources (Invoices/DA, Port Logs/SOF, Vessel Noon Reports, and AIS Satellite Data) to identify financial leakages and operational discrepancies in real-time.

## 2. Data Sources & Normalization

The engine must normalize data from the following entities into a unified `TimelineEvent` object:

- **Source A (Financial):** Extracted line items from Disbursement Accounts (DA).
- **Source B (Operational):** Statement of Facts (SOF) timestamps (Tug fast/off, Pilot on/off).
- **Source C (Vessel):** Noon Reports (Fuel remaining, GPS position, Engine hours).
- **Source D (External):** AIS Satellite Data (Actual berth arrival/departure times).

## 3. Core Logic: The "Triple-Check" Algorithm

The engine should run the following validation rules upon receipt of any new document:

### Rule 1: Temporal Tug/Pilot Audit

- **Input:** `DA_Tug_Hours` vs. `SOF_Tug_Timestamps`.
- **Logic:** If `DA_Invoiced_Hours` > (`SOF_Tug_Off` - `SOF_Tug_Fast`) + 0.5hr buffer.
- **Action:** Flag as **"High Risk: Overcharged Service Hours"**.

### Rule 2: Berthage/Stay Verification

- **Input:** `DA_Berth_Fee_Days` vs. `AIS_Berth_Stay_Duration`.
- **Logic:** Compare invoiced days against actual GPS "at berth" status.
- **Action:** Flag as **"Potential Error: Incorrect Berthage Calculation"**.

### Rule 3: Fuel Consumption Paradox

- **Input:** `Noon_Report_Fuel_Consumption` vs. `SOF_Wait_Time`.
- **Logic:** If vessel reported high fuel consumption while `SOF` shows "Idle at Anchorage" for 12+ hours.
- **Action:** Flag as **"Operational Alert: Unusual Fuel Burn while Idle"**.

## 4. Technical Requirements for Implementation

### 4.1 Backend (FastAPI / Python)

- Create an `AuditEngine` class that inherits from existing worker patterns.
- **Method:** `compare_events(port_call_id)` — Triggered after AI parsing of a new email/file.
- **Output:** An `AuditReport` JSON stored in the `discrepancies` table, linked to the `PortCall`.

### 4.2 Database Schema Addition

- **Table:** `discrepancies`
  - `id`: UUID
  - `tenant_id`: FK
  - `port_call_id`: FK
  - `source_documents`: Array[UUID] (Links to the conflicting emails/files)
  - `severity`: Enum (Low, Medium, High)
  - `estimated_loss`: Decimal (Estimated Euro amount of the overcharge)
  - `description`: String (AI-generated explanation of the gap)
  - `created_at`: datetime

### 4.3 Frontend UI (React + Tailwind)

- **Component:** `SentinelAlert` — A high-visibility card in the Port Call dashboard.
- **Component:** `SideBySideAudit` — A table showing:
  - Column 1: "Vendor Claims" (from Invoice)
  - Column 2: "Operational Reality" (from SOF/AIS)
  - Column 3: "Variance" (Highlighted in red)

## 5. Security & Privacy

- All audits must use the `tenant_id`'s specific LLM keys (BYOAI).
- Each audit result must be logged in the immutable `AuditLog`.

---

**Developer Note:** Focus on the `time_overlap` logic first. The system must be able to tell if two events claimed to happen at the same time actually did. For AIS API use aisstream.io.
