# vets-hub Learning Index

## Source
- **Origin**: /Users/switchaphon/_POPs_/vets-hub
- **Type**: Local project (Turborepo monorepo)

## Explorations

### 2026-04-26 1735 (--deep)
- [2026-04-26/1735_ARCHITECTURE](2026-04-26/1735_ARCHITECTURE.md)
- [2026-04-26/1735_CODE-SNIPPETS](2026-04-26/1735_CODE-SNIPPETS.md)
- [2026-04-26/1735_QUICK-REFERENCE](2026-04-26/1735_QUICK-REFERENCE.md)
- [2026-04-26/1735_TESTING](2026-04-26/1735_TESTING.md)
- [2026-04-26/1735_API-SURFACE](2026-04-26/1735_API-SURFACE.md)

**Key insights**:
- Thai government platform for ~3,000 vet clinics to submit annual สสป. animal health reports digitally — replacing Excel workflows
- Turborepo monorepo: Next.js 15 frontend + NestJS 10 backend + `@vets-hub/shared` (Zod schemas/types) + `@vets-hub/db` (Prisma, 22 models, 8 migrations)
- Dual auth: NextAuth v5 Credentials (web sessions) + API key guard (third-party clinic software integrations); 80+ REST endpoints, no active GraphQL despite placeholder
- No automated CI test pipeline yet — only an issue-triage workflow exists; tests run locally via Turbo tasks
