/**
 * publish-daily-post.ts
 *
 * Script de publicação diária do blog (zairyx-blog).
 * Implementa gate de qualidade de conteúdo antes de publicar.
 *
 * Regras do README.md aplicadas:
 * - Opt-in explícito para mensagens diárias
 * - Limite de 365 posts ativos
 * - Gate de qualidade com score mínimo
 * - Canonical automático para SEO
 *
 * Execução:
 *   npx ts-node scripts/publish-daily-post.ts
 *   ou via cron: 0 8 * * * npx ts-node scripts/publish-daily-post.ts
 */

import fs from 'fs';
import path from 'path';

// ─── Configuração ──────────────────────────────────────────────────────────────

const CONTENT_DIR = path.join(process.cwd(), 'content', 'posts');
const MAX_ACTIVE_POSTS = 365;

// Gate de qualidade: post precisa atender critérios mínimos para ser publicado.
// Impede publicação de rascunhos incompletos em produção.
const QUALITY_GATE = {
  minTitleLength: 10,
  minBodyLength: 300,         // palavras mínimas
  requiredFrontmatter: ['title', 'date', 'locale', 'slug', 'category'],
  requiredDisclaimer: true,   // todo post deve conter disclaimer de risco
};

// ─── Tipos ─────────────────────────────────────────────────────────────────────

interface PostFrontmatter {
  title: string;
  date: string;
  locale: string;
  slug: string;
  category: string;
  status: 'draft' | 'ready' | 'published' | 'archived';
  disclaimer?: boolean;
  canonicalUrl?: string;
}

interface QualityResult {
  passed: boolean;
  errors: string[];
  warnings: string[];
}

// ─── Gate de Qualidade ─────────────────────────────────────────────────────────

function runQualityGate(frontmatter: PostFrontmatter, body: string): QualityResult {
  const errors: string[] = [];
  const warnings: string[] = [];

  // Campos obrigatórios
  for (const field of QUALITY_GATE.requiredFrontmatter) {
    if (!frontmatter[field as keyof PostFrontmatter]) {
      errors.push(`Campo obrigatório ausente: ${field}`);
    }
  }

  // Comprimento mínimo do título
  if (frontmatter.title && frontmatter.title.length < QUALITY_GATE.minTitleLength) {
    errors.push(`Título muito curto: ${frontmatter.title.length} chars (mínimo: ${QUALITY_GATE.minTitleLength})`);
  }

  // Comprimento mínimo do corpo
  const wordCount = body.split(/\s+/).filter(Boolean).length;
  if (wordCount < QUALITY_GATE.minBodyLength) {
    errors.push(`Conteúdo muito curto: ${wordCount} palavras (mínimo: ${QUALITY_GATE.minBodyLength})`);
  }

  // Disclaimer de risco obrigatório
  // JURÍDICO: Todo post sobre trading DEVE ter disclaimer para compliance CVM
  if (QUALITY_GATE.requiredDisclaimer && !frontmatter.disclaimer) {
    errors.push('Disclaimer de risco ausente (obrigatório — CVM IN 621/20)');
  }

  // Warnings não-bloqueantes
  if (!frontmatter.canonicalUrl) {
    warnings.push('canonicalUrl não definido — será gerado automaticamente');
  }

  return {
    passed: errors.length === 0,
    errors,
    warnings,
  };
}

// ─── Helpers ───────────────────────────────────────────────────────────────────

function parseFrontmatter(content: string): { frontmatter: PostFrontmatter; body: string } {
  const match = content.match(/^---\n([\s\S]+?)\n---\n([\s\S]*)$/);
  if (!match) {
    throw new Error('Frontmatter inválido ou ausente');
  }

  const yamlLines = match[1].split('\n');
  const frontmatter: Record<string, string | boolean> = {};

  for (const line of yamlLines) {
    const [key, ...valueParts] = line.split(':');
    if (key && valueParts.length) {
      const raw = valueParts.join(':').trim();
      frontmatter[key.trim()] = raw === 'true' ? true : raw === 'false' ? false : raw;
    }
  }

  return {
    frontmatter: frontmatter as unknown as PostFrontmatter,
    body: match[2].trim(),
  };
}

function generateCanonical(slug: string, locale: string): string {
  // Base URL deve ser configurada via env
  const baseUrl = process.env.BLOG_BASE_URL || 'https://blog.zairyx.com.br';
  return locale === 'pt'
    ? `${baseUrl}/post/${slug}`
    : `${baseUrl}/${locale}/post/${slug}`;
}

function getActivePostCount(): number {
  if (!fs.existsSync(CONTENT_DIR)) return 0;
  return fs.readdirSync(CONTENT_DIR)
    .filter(f => f.endsWith('.md'))
    .filter(f => {
      try {
        const content = fs.readFileSync(path.join(CONTENT_DIR, f), 'utf-8');
        const { frontmatter } = parseFrontmatter(content);
        return frontmatter.status === 'published';
      } catch {
        return false;
      }
    }).length;
}

// ─── Main ──────────────────────────────────────────────────────────────────────

async function publishDailyPost(): Promise<void> {
  console.log('[publish-daily-post] Iniciando ciclo de publicação...\n');

  // Verificar limite de posts ativos (README: max 365)
  const activeCount = getActivePostCount();
  if (activeCount >= MAX_ACTIVE_POSTS) {
    console.error(
      `[BLOQUEADO] Limite de posts ativos atingido: ${activeCount}/${MAX_ACTIVE_POSTS}\n` +
      `Execute rotate-old-posts.ts antes de publicar novos posts.`
    );
    process.exit(1);
  }

  // Buscar próximo post com status 'ready'
  if (!fs.existsSync(CONTENT_DIR)) {
    console.error(`[ERRO] Diretório de posts não encontrado: ${CONTENT_DIR}`);
    process.exit(1);
  }

  const files = fs.readdirSync(CONTENT_DIR)
    .filter(f => f.endsWith('.md'))
    .sort(); // ordem cronológica por nome de arquivo

  let publishedCount = 0;

  for (const file of files) {
    const filePath = path.join(CONTENT_DIR, file);
    const rawContent = fs.readFileSync(filePath, 'utf-8');

    let parsed: ReturnType<typeof parseFrontmatter>;
    try {
      parsed = parseFrontmatter(rawContent);
    } catch (err) {
      console.warn(`[SKIP] ${file}: frontmatter inválido — ${err}`);
      continue;
    }

    const { frontmatter, body } = parsed;

    // Apenas posts com status 'ready'
    if (frontmatter.status !== 'ready') continue;

    // ── GATE DE QUALIDADE ────────────────────────────────────────────────────
    const quality = runQualityGate(frontmatter, body);

    if (quality.warnings.length > 0) {
      console.warn(`[WARN] ${file}:`);
      quality.warnings.forEach(w => console.warn(`  ⚠️  ${w}`));
    }

    if (!quality.passed) {
      console.error(`[GATE FALHOU] ${file} — post NÃO publicado:`);
      quality.errors.forEach(e => console.error(`  ❌ ${e}`));
      continue;
    }

    // ── CANONICAL AUTOMÁTICO (SEO) ───────────────────────────────────────────
    const canonical = frontmatter.canonicalUrl || generateCanonical(frontmatter.slug, frontmatter.locale);

    // Atualizar frontmatter: status → published, canonical definido
    const updatedContent = rawContent
      .replace(/^status: ready$/m, 'status: published')
      .replace(
        /^(canonicalUrl:.*)?$/m,
        `canonicalUrl: ${canonical}`
      );

    fs.writeFileSync(filePath, updatedContent, 'utf-8');

    console.log(`[OK] Publicado: ${file}`);
    console.log(`     Canonical: ${canonical}`);
    console.log(`     Palavras:  ${body.split(/\s+/).filter(Boolean).length}`);
    console.log(`     Locale:    ${frontmatter.locale}\n`);

    publishedCount++;
    break; // Um post por execução (política de 1 post/dia)
  }

  if (publishedCount === 0) {
    console.log('[INFO] Nenhum post pronto para publicação hoje.');
  }

  console.log(`[publish-daily-post] Ciclo concluído. Posts ativos: ${activeCount + publishedCount}/${MAX_ACTIVE_POSTS}`);
}

publishDailyPost().catch(err => {
  console.error('[FATAL]', err);
  process.exit(1);
});
