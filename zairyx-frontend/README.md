# Blog Subdominio Starter (separado do software)

Este pacote e um ponto de partida para criar o blog em repositorio proprio e conta Vercel separada.

## Objetivo

- Operar o blog em blog.zairyx.com.br sem integrar no app principal.
- Publicar 1 post por dia com politica de rotacao para nao sobrecarregar banco.

## Estrutura sugerida no novo repositorio

- app/
  - (blog)/
    - page.tsx
    - [slug]/page.tsx
  - sitemap.ts
  - robots.ts
- lib/
  - seo/
  - retention/
- content/
  - posts/
- scripts/
  - publish-daily-post.ts
  - rotate-old-posts.ts

## Regras essenciais

- Opt-in explicito para receber mensagens diarias.
- Link de descadastro em todas as mensagens.
- Limite de publicacoes ativas (ex: 365).
- Rotacao com redirecionamento 301 para evitar perda SEO.

## Deploy recomendado

- Conta Vercel separada para o blog.
- Deploy via GitHub Integration (sem Vercel CLI).
- DNS do subdominio apontando para o projeto do blog.

## Status

- Menu e divulgacao leve no site principal ja habilitados.
- Proximo passo: criar repo zairyx-blog e importar na conta Vercel separada.
