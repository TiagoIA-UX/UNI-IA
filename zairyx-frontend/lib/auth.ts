export const ALLOWED_PLATFORM_EMAILS: string[] = (
  process.env.ALLOWED_PLATFORM_EMAILS ||
  'globemarket7@gmail.com,tiagorocha1777@gmail.com,zairyx.ai@gmail.com,oficialuni.iabrasil@gmail.com,ciadaautomacao@gmail.com'
)
  .split(',')
  .map((e) => e.trim().toLowerCase())
  .filter(Boolean)

export function isAllowedPlatformEmail(email?: string | null): boolean {
  return !!email && ALLOWED_PLATFORM_EMAILS.includes(email.toLowerCase())
}

export function normalizeNextPath(next?: string | null): string {
  if (next && next.startsWith('/') && next !== '/login') {
    return next
  }
  return '/plataforma'
}