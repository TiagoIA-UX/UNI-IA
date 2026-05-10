/**
 * rotate-old-posts.ts
 *
 * Script de rotação de posts antigos do blog (zairyx-blog).
 * Arquiva posts além do limite de 365 e gera redirecionamentos 301
 * para preservar link equity de SEO.
 *
 * Regras do README.md aplicadas:
 * - Limite de publicações ativas: 365
 * - Rotação com redirecionamento 301 para evitar perda de SEO
 * - Canonical preservado no arquivo de redirects
 *
 * IMPORTANTE — SEO:
 * Posts arquivados são redirecionados para a página de categoria ou para
 * o post mais recente do mesmo assunto, preservando o page rank acumulado.
 * Duplicate content é evitado via canonical no frontmatter.
 *
 * Execução:
 *   npx ts-node scripts/rotate-old-posts.ts [--dry-run]
 */

import fs from 'fs';
import path from 'path';

// ─── Configuração ──────────────────────────────────────────────────────────────

const CONTENT_DIR = path.join(process.cwd(), 'content', 'posts');
const REDIRECTS_FILE = path.join(process.cwd(), 'redirects.json');
const MAX_ACTIVE_POSTS = 365;
const DRY_RUN = process.argv.includes('--dry-run');

// Destino de redirect por categoria (ajuste conforme suas categorias)
// P0 SEO: redirect para categoria evita 404 e preserva link equity
const CATEGORY_REDIRECT_MAP: Record<string, string> = {
  'analise-tecnica': '/categoria/analise-tecnica',
  'gestao-de-risco': '/categoria/gestao-de-risco',
  'mercado': '/categoria/mercado',
  'plataforma': '/categoria/plataforma',
  default: '/blog',
};

// ─── Tipos ─────────────────────────────────────────────────────────────────────

interface PostMeta {
  file: string;
  slug: string;
  date: string;
  category: string;
  canonicalUrl: string;
  publishedAt: Date;
}

interface RedirectEntry {
  source: string;
  destination: string;
  permanent: true;
  archivedAt: string;
  originalCanonical: string;
}

// ─── Helpers ───────────────────────────────────────────────────────────────────

function getPublishedPosts(): PostMeta[] {
  if (!fs.existsSync(CONTENT_DIR)) return [];

  const posts: PostMeta[] = [];

  for (const file of fs.readdirSync(CONTENT_DIR)) {
    if (!file.endsWith('.md')) continue;

    try {
      const content = fs.readFileSync(path.join(CONTENT_DIR, file), 'utf-8');
      const match = content.match(/^---\n([\s\S]+?)\n---/);
      if (!match) continue;

      const fm: Record<string, string> = {};
      for (const line of match[1].split('\n')) {
        const [k, ...v] = line.split(':');
        if (k) fm[k.trim()] = v.join(':').trim();
      }

      if (fm['status'] !== 'published') continue;

      posts.push({
        file,
        slug: fm['slug'] || file.replace('.md', ''),
        date: fm['date'] || '2000-01-01',
        category: fm['category'] || 'default',
        canonicalUrl: fm['canonicalUrl'] || '',
        publishedAt: new Date(fm['date'] || '2000-01-01'),
      });
    } catch {
      // arquivo com frontmatter inválido — ignorado silenciosamente
    }
  }

  // Ordenar do mais antigo para o mais recente
  return posts.sort((a, b) => a.publishedAt.getTime() - b.publishedAt.getTime());
}

function loadRedirects(): RedirectEntry[] {
  if (!fs.existsSync(REDIRECTS_FILE)) return [];
  try {
    return JSON.parse(fs.readFileSync(REDIRECTS_FILE, 'utf-8'));
  } catch {
    return [];
  }
}

function saveRedirects(redirects: RedirectEntry[]): void {
  fs.writeFileSync(REDIRECTS_FILE, JSON.stringify(redirects, null, 2), 'utf-8');
}

function archivePost(postMeta: PostMeta): void {
  const filePath = path.join(CONTENT_DIR, postMeta.file);
  const content = fs.readFileSync(filePath, 'utf-8');
  const updated = content.replace(/^status: published$/m, 'status: archived');
  fs.writeFileSync(filePath, updated, 'utf-8');
}

// ─── Main ──────────────────────────────────────────────────────────────────────

async function rotateOldPosts(): Promise<void> {
  console.log(`[rotate-old-posts] ${DRY_RUN ? '(DRY RUN) ' : ''}Iniciando rotação...\n`);

  const published = getPublishedPosts();
  const excess = published.length - MAX_ACTIVE_POSTS;

  console.log(`Posts publicados: ${published.length}`);
  console.log(`Limite máximo:    ${MAX_ACTIVE_POSTS}`);
  console.log(`Para arquivar:    ${Math.max(0, excess)}\n`);

  if (excess <= 0) {
    console.log('[INFO] Nenhuma rotação necessária.');
    return;
  }

  // Posts mais antigos a arquivar (os primeiros da lista ordenada)
  const toArchive = published.slice(0, excess);
  const redirects = loadRedirects();

  for (const post of toArchive) {
    // Destino do redirect: categoria do post ou /blog como fallback
    const destination = CATEGORY_REDIRECT_MAP[post.category] || CATEGORY_REDIRECT_MAP['default'];

    // Fonte do redirect: path canônico do post
    const baseUrl = process.env.BLOG_BASE_URL || 'https://blog.zairyx.com.br';
    const sourcePath = post.canonicalUrl
      ? post.canonicalUrl.replace(baseUrl, '')
      : `/post/${post.slug}`;

    const redirectEntry: RedirectEntry = {
      source: sourcePath,
      destination,
      permanent: true,
      archivedAt: new Date().toISOString(),
      originalCanonical: post.canonicalUrl,
    };

    // Evitar duplicatas no arquivo de redirects
    const alreadyExists = redirects.some(r => r.source === sourcePath);

    if (!alreadyExists) {
      redirects.push(redirectEntry);
    }

    if (!DRY_RUN) {
      archivePost(post);
      console.log(`[ARQUIVADO] ${post.file}`);
      console.log(`  Redirect 301: ${sourcePath} → ${destination}`);
      console.log(`  Canonical preservado: ${post.canonicalUrl}\n`);
    } else {
      console.log(`[DRY RUN] Arquivaria: ${post.file}`);
      console.log(`  Redirect 301: ${sourcePath} → ${destination}\n`);
    }
  }

  if (!DRY_RUN) {
    saveRedirects(redirects);

    // Regenerar next.config.js redirects (formato Next.js)
    // Para usar em next.config.js: async redirects() { return require('./redirects.json') }
    console.log(`\n[SEO] ${redirects.length} redirects salvos em redirects.json`);
    console.log('[SEO] Adicione ao next.config.js:');
    console.log('  async redirects() { return require(\'./redirects.json\'); }');
  }

  console.log(`\n[rotate-old-posts] Rotação concluída.`);
  console.log(`Posts ativos após rotação: ${published.length - (DRY_RUN ? 0 : excess)}/${MAX_ACTIVE_POSTS}`);
}

rotateOldPosts().catch(err => {
  console.error('[FATAL]', err);
  process.exit(1);
});
