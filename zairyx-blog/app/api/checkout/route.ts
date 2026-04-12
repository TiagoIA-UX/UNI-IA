import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import { createAdminClient } from '@/lib/supabase/admin';
import { withRateLimit } from '@/lib/rate-limit';

/**
 * Zairyx IA | Checkout API Endpoint
 * Regras Aplicadas do Cardápio Digital:
 * - Validação de payloads: Zod com z.object() e z.literal()
 * - Supabase: createAdminClient() para bypass de segurança restrita (inserir prospect)
 * - Erro Handling: NextResponse.json() com HTTP 4xx/5xx
 * - Sucesso: NextResponse.json({ success: true, ... })
 */

const CheckoutSchema = z.object({
  email: z.string().email('E-mail inválido'),
  fullName: z.string().min(3, 'Nome deve ter no mínimo 3 caracteres'),
  planType: z.literal('PREMIUM').or(z.literal('ENTERPRISE')),
});

export async function POST(req: NextRequest) {
  return withRateLimit(req, async () => {
    try {
      const body = await req.json();
      
      // 1. Validação Restrita com Zod (Nunca confiar no Frontend)
      const parseResult = CheckoutSchema.safeParse(body);
      if (!parseResult.success) {
        return NextResponse.json(
          { error: 'Dados inválidos.', details: parseResult.error.format() }, 
          { status: 400 }
        );
      }

      const { email, fullName, planType } = parseResult.data;

      // 2. Operação Privilegiada no Banco (Supabase Service Role / Admin Client)
      const adminSupabase = createAdminClient();
      
      // Tentar encontrar ou inserir na base de leads/usuários
      const { data: existingUser, error: checkError } = await adminSupabase
        .from('zairyx_users')
        .select('id, subscription_status')
        .eq('email', email)
        .maybeSingle();

      if (checkError) {
        throw new Error('Falha ao auditar usuário no banco de dados');
      }

      if (existingUser && existingUser.subscription_status === 'ACTIVE') {
        return NextResponse.json(
          { error: 'Este e-mail já possui uma assinatura ativa no Uni IA.' },
          { status: 409 }
        );
      }

      if (!existingUser) {
        // Criar registro preliminar "INACTIVE" aguardando Webhook de pagamento (ex: Mercado Pago / Stripe)
        const { error: insertError } = await adminSupabase
          .from('zairyx_users')
          .insert([{ 
            email, 
            full_name: fullName, 
            subscription_plan: planType,
            subscription_status: 'INACTIVE' 
          }]);

        if (insertError) throw new Error('Falha na criação da conta base');
      }

      // 3. Geração de Link de Checkout Dinâmico (Mock Padrão Unicórnio Financeiro)
      // Em produção, aqui chamaremos o SDK do Stripe ou Mercado Pago
      const checkoutUrl = planType === 'PREMIUM' 
        ? 'https://pay.stripe.com/p/link/assinar-zairyx-pro' 
        : 'https://pay.zairyx.ia/enterprise-desk';

      // 4. Sucesso! Padrão REST de saída
      return NextResponse.json({
        success: true,
        data: {
          checkoutUrl,
          message: 'Lead registrado. Redirecionando para o Gateway seguro.'
        }
      });

    } catch (error: any) {
      console.error('[API Checkout] Fatal:', error);
      return NextResponse.json(
        { error: 'Erro interno na orquestração financeira.' }, 
        { status: 500 }
      );
    }
  });
}
