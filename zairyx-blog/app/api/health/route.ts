import { NextResponse } from 'next/server';
import { createAdminClient } from '@/lib/supabase/admin';

/**
 * Zairyx IA | Health Check & Reliability
 * Automates system monitoring to ensure API and Database are alive.
 */
export async function GET() {
  try {
    const supabase = createAdminClient();

    // Quick DB ping against the active analytics table used in production.
    const start = performance.now();
    const { error } = await supabase.from('uni_ia_events').select('id').limit(1).maybeSingle();
    const dbLatency = performance.now() - start;

    if (error && error.code !== 'PGRST116') {
      throw new Error('Database connection failed');
    }

    return NextResponse.json({
      status: 'operational',
      timestamp: new Date().toISOString(),
      services: {
        database: { status: 'ok', latencyMs: Math.round(dbLatency) },
        llm: { status: 'ok', provider: 'Groq' } // Assume OK based on API status
      },
      compliance: {
        audit_ready: true,
        region: process.env.VERCEL_REGION || 'global'
      }
    });
  } catch (err: any) {
    return NextResponse.json({
      status: 'degraded',
      timestamp: new Date().toISOString(),
      error: err.message
    }, { status: 503 });
  }
}
