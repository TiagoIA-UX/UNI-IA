export type BlogPost = {
  slug: string
  title: string
  excerpt: string
  content: string
  publishedAt: string
}

export const MAX_PUBLISHED_POSTS = 365

export const posts: BlogPost[] = [
  {
    slug: 'como-usar-google-meu-negocio-para-delivery',
    title: 'Como usar Google Meu Negocio para atrair pedidos locais',
    excerpt: 'Passo a passo simples para aparecer melhor nas buscas locais e converter em pedidos.',
    content:
      'Otimize categoria, fotos reais, horario e botao de contato. Atualize semanalmente e leve o cliente para o seu canal proprio.',
    publishedAt: '2026-04-12',
  },
]

export function getPostBySlug(slug: string) {
  return posts.find((post) => post.slug === slug)
}
