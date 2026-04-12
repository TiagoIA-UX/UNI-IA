import { posts } from '../lib/posts'

export default function sitemap() {
  const baseUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://blog.zairyx.com.br'

  return [
    {
      url: `${baseUrl}/`,
      lastModified: new Date(),
      changeFrequency: 'daily' as const,
      priority: 0.9,
    },
    ...posts.map((post) => ({
      url: `${baseUrl}/${post.slug}`,
      lastModified: new Date(post.publishedAt),
      changeFrequency: 'daily' as const,
      priority: 0.7,
    })),
  ]
}
