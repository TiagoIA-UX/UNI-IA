import { NextRequest, NextResponse } from 'next/server';

/**
 * Zairyx IA | Rate Limiting MVP (In-Memory para Serveless/Edge)
 * Implementação baseada na regra: withRateLimit() + getRateLimitIdentifier() + retry headers
 */

const rateLimitMap = new Map<string, { count: number; lastReset: number }>();
const LIMIT = 5; // 5 requisições
const WINDOW_MS = 60 * 1000; // Por minuto

export function getRateLimitIdentifier(req: NextRequest): string {
  // Em produção, x-forwarded-for ou remoteAddress
  return req.headers.get('x-forwarded-for') || 'anonymous-ip';
}

export async function withRateLimit(req: NextRequest, handler: () => Promise<NextResponse>) {
  const ip = getRateLimitIdentifier(req);
  const now = Date.now();
  
  if (!rateLimitMap.has(ip)) {
    rateLimitMap.set(ip, { count: 1, lastReset: now });
  } else {
    const state = rateLimitMap.get(ip)!;
    if (now - state.lastReset > WINDOW_MS) {
      state.count = 1;
      state.lastReset = now;
    } else {
      state.count++;
      if (state.count > LIMIT) {
        return NextResponse.json(
          { error: 'Rate limit excedido. Tente novamente em alguns segundos.' },
          { 
            status: 429, 
            headers: { 'Retry-After': String(WINDOW_MS / 1000) } 
          }
        );
      }
    }
  }

  return handler();
}
