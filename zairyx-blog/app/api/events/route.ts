import { NextRequest, NextResponse } from 'next/server';
import { createAdminClient } from '@/lib/supabase/admin';

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const event = String(body?.event || 'unknown');
    const page = String(body?.page || 'unknown');
    const variant = String(body?.variant || 'A');
    const locale = String(body?.locale || 'en');
    const ts = String(body?.ts || new Date().toISOString());
    const details = typeof body?.details === 'object' && body?.details !== null ? body.details : {};
    const sessionId = String(body?.sessionId || 'anonymous');

    const admin = createAdminClient();
    const { error } = await admin.from('uni_ia_events').insert([
      {
        event,
        page,
        variant,
        locale,
        session_id: sessionId,
        event_ts: ts,
        details,
      },
    ]);

    if (error) {
      console.error('[UNI_IA_EVENT][DB_ERROR]', error);
      return NextResponse.json({ success: false, error: 'Falha ao persistir evento.' }, { status: 500 });
    }

    // Log server-side para acompanhar conversao por variante.
    console.info('[UNI_IA_EVENT]', { event, page, variant, locale, ts });

    return NextResponse.json({ success: true });
  } catch (error) {
    return NextResponse.json({ success: false, error: String(error) }, { status: 400 });
  }
}
