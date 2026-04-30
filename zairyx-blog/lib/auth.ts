export const ALLOWED_PLATFORM_EMAIL = (
  process.env.ALLOWED_PLATFORM_EMAIL || 'globemarket7@gmail.com'
).toLowerCase()

export function isAllowedPlatformEmail(email?: string | null) {
  return !!email && email.toLowerCase() === ALLOWED_PLATFORM_EMAIL
}

export function normalizeNextPath(next?: string | null) {
  if (!next || !next.startsWith('/')) {
    return '/plataforma'
  }

  return next
}
