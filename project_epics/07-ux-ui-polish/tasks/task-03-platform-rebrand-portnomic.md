# Task 7.3 — Platform Rebrand: ShipFlow → Portnomic

**Epic:** [07-ux-ui-polish](../epic.md)

---

## Objective

Rebrand the platform from **ShipFlow** to **Portnomic**, including a full name change across the application and a new design system based on **Oxford Blue** (trust) and **Success Green** (environmental focus).

---

## Problem statement

- **Current state:** Platform is branded as "ShipFlow AI" with maritime-themed blue colors (`maritime-*` palette).
- **Goal:** Rebrand to "Portnomic" with a refreshed color palette: Oxford Blue for trust and professionalism, Success Green for environmental/sustainability messaging.

---

## Scope

### 1. Brand name change

Replace all user-facing and configurable references from "ShipFlow" / "shipflow" to "Portnomic" / "portnomic":

| Location | Change |
|----------|--------|
| **Frontend** | |
| `frontend/index.html` | `<title>ShipFlow AI</title>` → `<title>Portnomic</title>` |
| `frontend/src/layout/Sidebar.tsx` | "ShipFlow" → "Portnomic" |
| `frontend/src/layout/AppLayout.tsx` | "ShipFlow" → "Portnomic" |
| `frontend/package.json` | `shipflow-frontend` → `portnomic-frontend` (optional) |
| **Backend** | |
| `backend/app/main.py` | API title "ShipFlow AI API" → "Portnomic API" |
| `backend/app/config.py` | `smtp_from_name: "ShipFlow"` → `"Portnomic"`; `smtp_from_address` domain if applicable |
| `backend/app/services/auth.py` | TOTP issuer "ShipFlow AI" → "Portnomic" |
| `backend/app/services/billing.py` | Stripe customer email domain `@shipflow.ai` → `@portnomic.ai` |
| `backend/app/services/emission_export.py` | "ShipFlow" in report footer → "Portnomic" |
| `backend/app/seed.py` | Tenant name "ShipFlow Demo" → "Portnomic Demo"; admin email domain |
| `backend/pyproject.toml` | `shipflow-backend` → `portnomic-backend` (optional) |
| **Config / env** | |
| `.env.example` | `SMTP_FROM_NAME`, `PLATFORM_ADMIN_EMAILS` domain references |
| **Docs / rules** | |
| `README.md` | Product name, tenant name, admin email |
| `.cursor/rules/business-agent.mdc` | Product context |
| `.agents/AGENTS.md` | Product name |
| **Tests** | |
| `frontend/src/layout/Sidebar.test.tsx` | "ShipFlow" → "Portnomic" in assertions |
| `backend/tests/conftest.py` | Default admin email if hardcoded |

**Note:** Internal identifiers (logger names, Redis key prefixes like `shipflow:parse_jobs`, database names, reserved slugs) can remain for backward compatibility or be migrated in a separate task. Focus on user-facing branding first.

### 2. Design system: new color palette

#### Oxford Blue (trust, primary)

- **Hex:** `#002147`
- **Usage:** Primary brand color, sidebar, headers, buttons, links.
- **Palette:** Define `oxford-blue-50` through `oxford-blue-950` for consistency (or map to existing scale).

| Token | Hex | Use |
|-------|-----|-----|
| oxford-blue-600 (primary) | #002147 | Primary buttons, sidebar bg, nav active |
| oxford-blue-700 | #001a38 | Hover states |
| oxford-blue-800 | #001429 | Darker backgrounds |
| oxford-blue-500 | #003366 | Lighter accents |
| oxford-blue-400 | #004080 | Borders, subtle highlights |

#### Success Green (environmental, accent)

- **Hex:** `#28A745` (Bootstrap success) or `#00b16a` (richer variant)
- **Usage:** Success states, environmental/sustainability indicators, badges, charts, CTAs for "green" features (e.g. emissions).

| Token | Hex | Use |
|-------|-----|-----|
| success-green-600 | #28A745 | Success badges, environmental highlights |
| success-green-500 | #34c759 | Hover |
| success-green-700 | #218838 | Darker variant |
| success-green-100 | #d4edda | Light backgrounds for success cards |

### 3. CSS / Tailwind updates

- **`frontend/src/index.css`:** Replace `maritime` palette with `oxford-blue`; add `success-green` palette.
- **shadcn theme:** Map `--primary` to Oxford Blue; add `--success` or use `success-green` for success variants.
- **Component usage:** Replace `maritime-*` classes with `oxford-blue-*` (or `primary`) across:
  - `Sidebar.tsx`, `AppLayout.tsx`
  - Dashboard cards, badges
  - Buttons, links, nav active states
- **Success green:** Apply to success badges, emissions-related UI, environmental KPIs.

### 4. Favicon and assets (optional)

- Update favicon if it contains "ShipFlow" or maritime-specific imagery.
- Consider a Portnomic logo asset for sidebar/header.

---

## Acceptance criteria

- [ ] All user-facing "ShipFlow" text replaced with "Portnomic" (frontend, backend API title, emails, reports, seed data).
- [ ] Page title shows "Portnomic" in browser tab.
- [ ] Sidebar and app layout display "Portnomic" branding.
- [ ] Oxford Blue (`#002147`) used as primary color; `oxford-blue` palette defined in CSS.
- [ ] Success Green used for success states and environmental/sustainability UI elements.
- [ ] No remaining `maritime-*` references in key UI components (or mapped to new palette).
- [ ] Tests updated for new branding.
- [ ] README and agent rules reflect "Portnomic".

---

## Implementation notes

### Color palette (index.css)

```css
@theme {
  /* Oxford Blue - trust, primary */
  --color-oxford-blue-50: #e6ecf2;
  --color-oxford-blue-100: #b3c4d9;
  --color-oxford-blue-200: #809bbf;
  --color-oxford-blue-300: #4d72a6;
  --color-oxford-blue-400: #1a498c;
  --color-oxford-blue-500: #003366;
  --color-oxford-blue-600: #002147;  /* Primary */
  --color-oxford-blue-700: #001a38;
  --color-oxford-blue-800: #001429;
  --color-oxford-blue-900: #000d1a;
  --color-oxford-blue-950: #00060d;

  /* Success Green - environmental */
  --color-success-green-50: #e8f5e9;
  --color-success-green-100: #d4edda;
  --color-success-green-200: #a3d9a5;
  --color-success-green-300: #72c275;
  --color-success-green-400: #4caf50;
  --color-success-green-500: #34c759;
  --color-success-green-600: #28a745;  /* Primary success */
  --color-success-green-700: #218838;
  --color-success-green-800: #1e7e34;
  --color-success-green-900: #1b5e20;
  --color-success-green-950: #0d3310;
}

:root {
  /* Primary = Oxford Blue */
  --primary: #002147;
  --primary-foreground: #ffffff;
  /* Success = Success Green for badges, environmental UI */
}
```

### Search-and-replace checklist

Use project-wide search for: `ShipFlow`, `Shipflow`, `shipflow.ai`, `shipflow` (in display strings).

---

## Dependencies

- None (can run in parallel with other UX tasks).

---

## Out of scope (for now)

- Domain change (`shipflow.ai` → `portnomic.ai`) — requires DNS, email, infra.
- Redis key prefix migration (`shipflow:*` → `portnomic:*`) — backward compatibility.
- Reserved slug `shipflow` in tenant schema — low priority.
- Database/Postgres naming — internal only.

---

## Related code

- `frontend/src/index.css` — color tokens
- `frontend/src/layout/Sidebar.tsx`, `AppLayout.tsx` — branding
- `frontend/index.html` — page title
- `backend/app/config.py`, `main.py` — API and email config
- `backend/app/services/auth.py`, `billing.py`, `emission_export.py` — user-facing strings
