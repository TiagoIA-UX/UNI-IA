import { NextRequest, NextResponse } from 'next/server';
import { createAdminClient } from '@/lib/supabase/admin';
import { requirePlatformAdminApi } from '@/lib/api-auth';

type EventRow = {
  event: string;
  variant: 'A' | 'B' | string;
  created_at: string;
};

type VariantMetrics = {
  views: number;
  premiumSubmit: number;
  premiumRedirect: number;
  freeClick: number;
  submitRate: number;
  redirectRate: number;
};

function normalizeVariant(value: string): 'A' | 'B' {
  return value === 'B' ? 'B' : 'A';
}

function buildMetrics(rows: EventRow[]) {
  const base: Record<'A' | 'B', VariantMetrics> = {
    A: { views: 0, premiumSubmit: 0, premiumRedirect: 0, freeClick: 0, submitRate: 0, redirectRate: 0 },
    B: { views: 0, premiumSubmit: 0, premiumRedirect: 0, freeClick: 0, submitRate: 0, redirectRate: 0 },
  };

  for (const row of rows) {
    const key = normalizeVariant(row.variant);
    if (row.event === 'sales_page_view') base[key].views += 1;
    if (row.event === 'premium_checkout_submit') base[key].premiumSubmit += 1;
    if (row.event === 'premium_checkout_redirect') base[key].premiumRedirect += 1;
    if (row.event === 'free_channel_click') base[key].freeClick += 1;
  }

  for (const key of ['A', 'B'] as const) {
    const views = base[key].views;
    base[key].submitRate = views > 0 ? Number((base[key].premiumSubmit / views).toFixed(4)) : 0;
    base[key].redirectRate = views > 0 ? Number((base[key].premiumRedirect / views).toFixed(4)) : 0;
  }

  return base;
}

export async function GET(req: NextRequest) {
  try {
    const authError = await requirePlatformAdminApi();
    if (authError) {
      return authError;
    }

    const page = req.nextUrl.searchParams.get('page') || 'planos';
    const days = Number(req.nextUrl.searchParams.get('days') || '30');
    const minViews = Number(req.nextUrl.searchParams.get('minViews') || '100');
    const metric = req.nextUrl.searchParams.get('metric') === 'submit' ? 'submitRate' : 'redirectRate';
    const from = new Date(Date.now() - Math.max(days, 1) * 24 * 60 * 60 * 1000).toISOString();

    const admin = createAdminClient();
    const { data, error } = await admin
      .from('uni_ia_events')
      .select('event,variant,created_at')
      .eq('page', page)
      .gte('created_at', from);

    if (error) {
      console.error('[UNI_IA_EVENT_DECISION][DB_ERROR]', error);
      return NextResponse.json({ success: false, error: 'Falha ao carregar decisao.' }, { status: 500 });
    }

    const rows = (data || []) as EventRow[];
    const variants = buildMetrics(rows);

    const hasSample = variants.A.views >= minViews && variants.B.views >= minViews;
    const scoreA = variants.A[metric];
    const scoreB = variants.B[metric];

    let winner: 'A' | 'B' | null = null;
    let loser: 'A' | 'B' | null = null;
    let reason = '';

    if (!hasSample) {
      reason = `Amostra insuficiente. minViews=${minViews}, A=${variants.A.views}, B=${variants.B.views}`;
    } else if (scoreA === scoreB) {
      reason = `Empate na metrica ${metric}.`;
    } else {
      winner = scoreA > scoreB ? 'A' : 'B';
      loser = winner === 'A' ? 'B' : 'A';
      reason = `Vencedora por ${metric}: ${winner} (${variants[winner][metric]}) vs ${loser} (${variants[loser][metric]}).`;
    }

    const uplift = winner && loser
      ? Number(((variants[winner][metric] - variants[loser][metric]) * 100).toFixed(2))
      : 0;

    return NextResponse.json({
      success: true,
      data: {
        page,
        days,
        metric,
        minViews,
        hasSample,
        winner,
        loser,
        uplift,
        reason,
        variants,
      },
    });
  } catch (error) {
    return NextResponse.json({ success: false, error: String(error) }, { status: 400 });
  }
}
