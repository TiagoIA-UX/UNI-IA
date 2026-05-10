export const ALLOWED_PLATFORM_EMAILS: string[] = (
  process.env.ALLOWED_PLATFORM_EMAILS ||
  'globemarket7@gmail.com,tiagorocha1777@gmail.com,zairyx.ai@gmail.com,oficialuni.iabrasil@gmail.com,ciadaautomacao@gmail.com'
)
  .split(',')
  .map((e) => e.trim().toLowerCase())
  .filter(Boolean)

/**
 * Verifica se o e-mail tem permissão para acessar a plataforma
 */
export function isAllowedPlatformEmail(email?: string | null): boolean {
  return !!email && ALLOWED_PLATFORM_EMAILS.includes(email.toLowerCase())
}

/**
/**
/**
 * Define o destino pós-login.
 * Versão Blindada: Força o redirecionamento para o Dashboard de Elite 
 * independente de qualquer outra sugestão do sistema.
 */
export function normalizeNextPath(next?: string | null): string {
  // Ignoramos qualquer sugestão ('next') e forçamos o Dashboard.
  // Isso garante que o usuário caia direto no seu "Ouro".
  return '/dashboard'
}