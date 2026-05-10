export default function robots() {
  const baseUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://blog.zairyx.com.br'

  return {
    rules: {
      userAgent: '*',
      allow: '/',
    },
    sitemap: `${baseUrl}/sitemap.xml`,
    host: baseUrl,
  }
}
