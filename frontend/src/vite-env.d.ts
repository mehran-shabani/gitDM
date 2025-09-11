/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
  readonly VITE_API_WITH_CREDENTIALS?: 'true' | 'false';
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
