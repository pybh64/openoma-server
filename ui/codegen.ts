import type { CodegenConfig } from "@graphql-codegen/cli";

const config: CodegenConfig = {
  schema: "http://localhost:8000/graphql",
  documents: ["src/graphql/**/*.ts", "!src/graphql/generated/**"],
  generates: {
    "./src/graphql/generated/": {
      preset: "client",
      config: {
        documentMode: "string",
      },
    },
  },
  ignoreNoDocuments: true,
};

export default config;
