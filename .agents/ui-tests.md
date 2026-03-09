# UI Tests Agent — ShipFlow AI

Use when writing, maintaining, or debugging UI tests. Applies to component tests (React Testing Library), E2E tests (Playwright), and test setup.

## Scope

- **Component tests:** React components, shadcn/ui, forms, loading/error/empty states.
- **E2E tests:** Critical user flows (login, dashboard, vessel/port call/DA navigation).
- **Test setup:** Vitest, React Testing Library, Playwright, MSW for API mocking.

## Stack

| Type | Tool |
|------|------|
| Unit/component | Vitest + @testing-library/react |
| E2E | Playwright |
| API mocking | MSW |

## Conventions

- **Queries:** Prefer `getByRole`, `getByLabelText`, `getByTestId` (last resort). Avoid `getByText` for dynamic content.
- **Async:** Use `findBy*` or `waitFor` for async UI; avoid arbitrary `setTimeout`.
- **shadcn:** Test accessible behavior (roles, labels); avoid testing internal DOM structure.
- **Router:** Wrap components in `MemoryRouter` or use `createMemoryRouter` + `RouterProvider` for route-dependent tests.
- **Auth/tenant:** Mock API responses with MSW; use test fixtures for JWT/tenant context.

## Key Flows to Cover

- **Auth:** Login form validation, MFA flow (mocked).
- **Dashboard:** KPI cards render, recent lists, empty states, loading skeletons, error alerts.
- **CRUD:** List/detail navigation, form validation, submit handling.
- **DA workflow:** Status badges, approve action (mocked).

## File Layout

```
frontend/
├── src/
│   └── __tests__/           # or *.test.tsx colocated
│       ├── setup.ts
│       └── mocks/
│           └── handlers.ts  # MSW handlers
├── e2e/
│   ├── playwright.config.ts
│   └── *.spec.ts
└── vitest.config.ts
```

## Skills

- Use **react-dev** for component patterns.
- Use **react-router-v7** for loader/action testing.
