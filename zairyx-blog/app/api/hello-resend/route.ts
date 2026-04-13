import { Resend } from 'resend';
import { NextRequest, NextResponse } from 'next/server';

// Utilizando a credencial (Suposta do Cardápio Digital) 
// ou o Fallback do Vercel Environment Variables real.
const resend = new Resend(process.env.RESEND_API_KEY || 're_CHAVEDORESEND_CARDAPIODIGITAL');

export async function POST(req: NextRequest) {
  try {
    const { email, plan } = await req.json();

    if (!email) {
      return NextResponse.json({ error: 'O email é obrigatório' }, { status: 400 });
    }

    // Disparo oficial transacional via Resend
    const data = await resend.emails.send({
      from: 'UNI IA <onboarding@zairyx.ia>',
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
