import { NextRequest, NextResponse } from 'next/server';
import { createAdminClient } from '@/lib/supabase/admin';
import { requirePlatformAdminApi } from '@/lib/api-auth';

type EventRow = {
  event: string;
  variant: 'A' | 'B' | string;
  created_at: string;
};

export async function GET(req: NextRequest) {
  try {
    const authError = await requirePlatformAdminApi();
    if (authError) {
      return authError;
    }

    const page = req.nextUrl.searchParams.get('page') || 'planos';
    const days = Number(req.nextUrl.searchParams.get('days') || '30');
    const from = new Date(Date.now() - Math.max(days, 1) * 24 * 60 * 60 * 1000).toISOString();

    const admin = createAdminClient();
    const { data, error } = await admin
      .from('uni_ia_events')
      .select('event,variant,created_at')
      .eq('page', page)
      .gte('created_at', from);

    if (error) {
      console.error('[UNI_IA_EVENT_SUMMARY][DB_ERROR]', error);
      return NextResponse.json({ success: false, error: 'Falha ao carregar resumo.' }, { status: 500 });
    }

    const rows = (data || []) as EventRow[];
    const variants: Record<string, { views: number; premiumSubmit: number; premiumRedirect: number; freeClick: number }> = {
      A: { views: 0, premiumSubmit: 0, premiumRedirect: 0, freeClick: 0 },
      B: { views: 0, premiumSubmit: 0, premiumRedirect: 0, freeClick: 0 },
    };

    for (const row of rows) {
      const key = row.variant === 'B' ? 'B' : 'A';
      if (row.event === 'sales_page_view') variants[key].views += 1;
      if (row.event === 'premium_checkout_submit') variants[key].premiumSubmit += 1;
      if (row.event === 'premium_checkout_redirect') variants[key].premiumRedirect += 1;
      if (row.event === 'free_channel_click') variants[key].freeClick += 1;
    }

    const response = {
      success: true,
      data: {
        page,
        days,
        variants: {
          A: {
            ...variants.A,
            submitRate: variants.A.views > 0 ? Number((variants.A.premiumSubmit / variants.A.views).toFixed(4)) : 0,
            redirectRate: variants.A.views > 0 ? Number((variants.A.premiumRedirect / variants.A.views).toFixed(4)) : 0,
          },
          B: {
            ...variants.B,
            submitRate: variants.B.views > 0 ? Number((variants.B.premiumSubmit / variants.B.views).toFixed(4)) : 0,
            redirectRate: variants.B.views > 0 ? Number((variants.B.premiumRedirect / variants.B.views).toFixed(4)) : 0,
          },
        },
      },
    };

    return NextResponse.json(response);
  } catch (error) {
    return NextResponse.json({ success: false, error: String(error) }, { status: 400 });
  }
}
