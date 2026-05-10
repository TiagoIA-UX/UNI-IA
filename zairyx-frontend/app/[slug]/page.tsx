import { notFound } from 'next/navigation'
import { getPostBySlug, posts } from '../../lib/posts'

export function generateStaticParams() {
  return posts.map((post) => ({ slug: post.slug }))
}

export default async function PostPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params
  const post = getPostBySlug(slug)

  if (!post) return notFound()

  return (
    <article>
      <p style={{ margin: 0, color: '#6b7280', fontSize: 13 }}>{post.publishedAt}</p>
      <h1 style={{ marginTop: 10, fontSize: 34, lineHeight: 1.1 }}>{post.title}</h1>
      <p style={{ color: '#374151', lineHeight: 1.7 }}>{post.content}</p>

      <div
        style={{
          marginTop: 20,
          border: '1px solid #dbeafe',
          background: '#eff6ff',
          borderRadius: 12,
          padding: 14,
        }}
      >
        <strong style={{ color: '#1d4ed8' }}>CTA:</strong>
        <p style={{ margin: '6px 0 0', color: '#1e3a8a' }}>
          Quer aplicar isso no seu delivery? Acesse a plataforma principal:
          <a
            href="https://zairyx.com.br?utm_source=blog&utm_medium=article&utm_campaign=organic"
            style={{ marginLeft: 6, color: '#1d4ed8', fontWeight: 700 }}
          >
            zairyx.com.br
          </a>
        </p>
      </div>
    </article>
  )
}
