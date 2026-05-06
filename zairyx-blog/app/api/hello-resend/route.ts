import { Resend } from 'resend';
import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import { requirePlatformAdminApi } from '@/lib/api-auth';

const EmailRequestSchema = z.object({
  email: z.string().email('O email informado e invalido.'),
  plan: z.string().trim().min(1).max(60).optional(),
});

export async function POST(req: NextRequest) {
  try {
    const authError = await requirePlatformAdminApi();
    if (authError) {
      return authError;
    }

    const resendApiKey = process.env.RESEND_API_KEY;
    const resendFromEmail = process.env.RESEND_FROM_EMAIL;
    if (!resendApiKey || !resendFromEmail) {
      return NextResponse.json(
        { success: false, error: 'Servico de e-mail nao configurado.' },
        { status: 503 }
      );
    }

    const body = await req.json();
    const parseResult = EmailRequestSchema.safeParse(body);
    if (!parseResult.success) {
      return NextResponse.json(
        { success: false, error: 'Payload invalido.', details: parseResult.error.flatten() },
        { status: 400 }
      );
    }

    const { email, plan } = parseResult.data;
    const resend = new Resend(resendApiKey);
    const data = await resend.emails.send({
      from: resendFromEmail,
      to: email,
      subject: `UNI IA - Sua jornada rumo ao plano ${plan || 'PRO'} começou!`,
      html: `
        <div style="font-family: sans-serif; color: #111;">
          <h2>Bem-vindo à revolução financeira, investidor(a)!</h2>
          <p>Seu lead foi prospectado pelos agentes do <strong>Uni IA</strong>.</p>
          <p>O mercado é agressivo, mas a informação algorítmica vai te proteger.</p>
          <hr />
          <p>Acesse seu perfil do Supabase e finalize a assinatura no link seguro:</p>
          <a href="https://pay.stripe.com/p/link/assinar-zairyx-pro">Completar Inscrição Premium</a>
          <br/><br/>
          <small>Robô Ph.D da UNI IA. Resolução 100% livre de humanos.</small>
        </div>
      `
    });

    return NextResponse.json({ success: true, data });
  } catch (error) {
    return NextResponse.json({ error: String(error) }, { status: 500 });
  }
}
