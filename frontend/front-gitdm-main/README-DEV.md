# React API Client: Generated from OpenAPI

This app was scaffolded with Vite (React + TypeScript) and configured to generate a fully typed API client from the root `OpenAPI.yml` using Orval. It exposes axios-based services and is ready to layer React Query hooks and UI screens.

## Structure

- `orval.config.ts`: Orval configuration reading `../OpenAPI.yml` and generating to `src/api/generated` using an axios mutator.
- `src/api/http/axios-instance.ts`: Central axios client and Orval-compatible mutator (`createAxiosInstance<T>`).
- `src/api/generated/`: Auto-generated services and types (do not edit).
- `src/main.tsx`: App entry with `QueryClientProvider` and React Query Devtools.
- `.env.example`: Declare `VITE_API_BASE_URL` for axios base URL.

### Scripts

- `npm run api:generate`: Generate the client from `OpenAPI.yml`.
- `npm run api:watch`: Watch and regenerate on changes.
- `npm run dev`: Start Vite dev server.
- `npm run build`: Type-check and build for production.

### Environment

Copy `.env.example` to `.env` and set your API base URL:

```dotenv
VITE_API_BASE_URL=http://localhost:3000
VITE_API_WITH_CREDENTIALS=false
```

### Using the generated client

The generator created axios-powered functions and React Query hooks in `src/api/generated/gitdmApi.ts`. The mutator unwraps `AxiosResponse` so functions return data directly.

```tsx
import { useQuery } from '@tanstack/react-query';
import { getGitdmApi } from './api/generated/gitdmApi';

export function Example() {
  const api = getGitdmApi();
  const { data, isLoading, error } = useQuery({
    queryKey: ['ai-summaries'],
    queryFn: () => api.apiAiSummariesList(),
  });

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error</div>;
  return <pre>{JSON.stringify(data, null, 2)}</pre>;
}
```

Note: If you prefer Orval to emit only services (no hooks), change `client` back to `'axios'` in `orval.config.ts`. The axios mutator will still work.

### Conventions & next steps

- Co-locate feature-level API calls under `src/features/<feature>/api.ts` that wrap the generated endpoints for domain clarity.
- Use React Query for caching, pagination, and mutations. Define query keys in a central `src/api/queryKeys.ts`.
- Add error boundaries and toasts for mutation errors.
- Introduce a lightweight UI library (e.g., Mantine, MUI, or Tailwind) and build minimal resource screens:
  - List + detail for each top-level resource found in `OpenAPI.yml` (e.g., AI summaries, patients, encounters, etc.).
  - CRUD forms driven by generated types.
- Add auth token retrieval in `axios-instance.ts` by wiring an interceptor based on your auth flow.

### Troubleshooting

- If types fail with `verbatimModuleSyntax`, ensure type-only imports are used where needed.
- If Orval warns about `import.meta`, it is safe to ignore.
- If peer dependency warnings appear for React Query on React 19, use `--legacy-peer-deps` temporarily.

### Regeneration notes

Do not edit files under `src/api/generated`. Regenerate after any change to `OpenAPI.yml`:

```bash
npm run api:generate
```
