import { NextResponse } from 'next/server'
import { isAllowedPlatformEmail } from '@/lib/auth'
import { createClient } from '@/lib/supabase/server'

export async function requirePlatformAdminApi() {
  const supabase = await createClient()
  const { data, error } = await supabase.auth.getUser()
  const user = data.user

  if (error || !user?.email) {
    return NextResponse.json(
      { success: false, error: 'Autenticacao obrigatoria.' },
      { status: 401 }
    )
  }

  if (!isAllowedPlatformEmail(user.email)) {
    return NextResponse.json(
      { success: false, error: 'Acesso administrativo negado.' },
      { status: 403 }
    )
  }

  return null
}
