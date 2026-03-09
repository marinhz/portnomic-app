---
name: ui-tests
description: Write and maintain UI tests for React apps using Vitest, React Testing Library, and Playwright. Use when writing component tests, E2E tests, setting up test infrastructure, or when the user mentions UI tests, component tests, E2E, Playwright, Testing Library, or vitest.
---

# UI Tests — React + Vitest + Playwright

## Quick Start

**Component tests:** Vitest + @testing-library/react  
**E2E tests:** Playwright

## Query Priority (Testing Library)

1. `getByRole` — best for accessibility
2. `getByLabelText` — forms
3. `getByPlaceholderText` — fallback for forms
4. `getByText` — non-interactive content
5. `getByTestId` — last resort

```tsx
// ✅ Prefer
screen.getByRole('button', { name: /submit/i });
screen.getByLabelText(/email/i);
screen.getByRole('heading', { level: 1 });

// ❌ Avoid for dynamic content
screen.getByText('Welcome back'); // brittle if copy changes
```

## Async Patterns

```tsx
// findBy* — returns promise, waits for element
const button = await screen.findByRole('button', { name: /save/i });

// waitFor — custom assertions
await waitFor(() => {
  expect(screen.getByText(/success/i)).toBeInTheDocument();
});

// waitForElementToBeRemoved
await waitForElementToBeRemoved(() => screen.getByRole('progressbar'));
```

## Router Setup

```tsx
import { createMemoryRouter, RouterProvider } from 'react-router';
import { render, screen } from '@testing-library/react';

function renderWithRouter(routes: RouteObject[], initialEntries = ['/']) {
  const router = createMemoryRouter(routes, { initialEntries });
  return render(<RouterProvider router={router} />);
}
```

## MSW for API Mocking

```tsx
// mocks/handlers.ts
import { http, HttpResponse } from 'msw';

export const handlers = [
  http.get('/api/vessels', () => HttpResponse.json({ vessels: [] })),
  http.get('/api/dashboard', () => HttpResponse.json({ vesselCount: 5 })),
];

// setup.ts
import { setupServer } from 'msw/node';
import { handlers } from './mocks/handlers';
export const server = setupServer(...handlers);

// vitest.config.ts — setupFiles: ['src/__tests__/setup.ts']
```

## shadcn Component Testing

Test behavior, not implementation:

```tsx
// Card with CardTitle, CardContent
expect(screen.getByRole('heading', { name: /total vessels/i })).toBeInTheDocument();
expect(screen.getByText('5')).toBeInTheDocument();

// Button variants
const submitBtn = screen.getByRole('button', { name: /submit/i });
expect(submitBtn).toBeDisabled(); // or toBeEnabled

// Badge — often has role or aria
screen.getByText(/approved/i);
```

## Playwright E2E

```ts
// e2e/login.spec.ts
import { test, expect } from '@playwright/test';

test('user can log in', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel(/email/i).fill('user@example.com');
  await page.getByLabel(/password/i).fill('password');
  await page.getByRole('button', { name: /log in/i }).click();
  await expect(page).toHaveURL(/dashboard/);
});
```

## Setup Checklist

1. Install: `vitest`, `@testing-library/react`, `@testing-library/jest-dom`, `jsdom`, `msw`
2. Or E2E: `@playwright/test`
3. Add `setupFiles` in vitest.config.ts
4. Extend `@testing-library/jest-dom` in setup for matchers like `toBeInTheDocument`
