import { defineConfig } from 'orval';

export default defineConfig({
  api: {
    input: './OpenAPI.yaml',
    output: {
      mode: 'split',
      target: 'src/api/generated',
      client: 'react-query',
      prettier: true,
      clean: true,
      override: {
        mutator: {
          path: './src/api/http/axios-instance.ts',
          name: 'createAxiosInstance',
        },
      },
    },
  },
});

