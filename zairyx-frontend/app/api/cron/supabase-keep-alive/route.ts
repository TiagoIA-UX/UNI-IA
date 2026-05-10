import { NextRequest, NextResponse } from 'next/server';
import { createAdminClient } from '@/lib/supabase/admin';

/**
 * UNI IA | Supabase Keep-Alive Cron
 *
 * Roda a cada 6 dias via Vercel Cron (ver vercel.json).
 * Faz uma query leve no banco para evitar que o projeto
 * seja pausado pelo Supabase free tier (pausa após 7 dias sem uso).
 *
 * Protegido por CRON_SECRET — nunca expor esta rota publicamente.
 */
export async function GET(req: NextRequest) {
  // Verificação de segurança: apenas o Vercel Cron pode chamar esta rota
  const authHeader = req.headers.get('authorization');
  const cronSecret = process.env.CRON_SECRET;

  if (!cronSecret) {
    return NextResponse.json(
      { error: 'CRON_SECRET não configurado.' },
      { status: 500 }
    );
  }

  if (authHeader !== `Bearer ${cronSecret}`) {
    return NextResponse.json(
      { error: 'Não autorizado.' },
      { status: 401 }
    );
  }

  try {
    const supabase = createAdminClient();
    const start = performance.now();

    // Query leve — só verifica se o banco está acordado
    const { error } = await supabase
      .from('uni_ia_events')
      .select('id')
      .limit(1)
      .maybeSingle();

    const latencyMs = Math.round(performance.now() - start);

    if (error && error.code !== 'PGRST116') {
      throw new Error(`DB error: ${error.message}`);
    }

    console.info('[KEEPALIVE] Supabase acordado. Latência:', latencyMs, 'ms');

    return NextResponse.json({
      success: true,
      timestamp: new Date().toISOString(),
      latencyMs,
      message: 'Supabase keep-alive executado com sucesso.',
    });

  } catch (err: any) {
    console.error('[KEEPALIVE] Falha:', err.message);
    return NextResponse.json(
      { success: false, error: err.message },
      { status: 503 }
    );
  }
}
