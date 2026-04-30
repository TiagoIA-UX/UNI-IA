'use client'

import { useState } from 'react'

type GoogleLoginButtonProps = {
  nextPath?: string
}

export default function GoogleLoginButton({ nextPath = '/plataforma' }: GoogleLoginButtonProps) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleLogin() {
    setLoading(true)
    setError('')

    try {
      window.location.assign(`/auth/login?next=${encodeURIComponent(nextPath)}`)
    } catch {
      setError('Nao foi possivel iniciar o login com Google.')
      setLoading(false)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.8rem' }}>
      <button
        type='button'
        onClick={handleLogin}
        disabled={loading}
        style={{
          border: 'none',
          borderRadius: '0.9rem',
          padding: '0.95rem 1.2rem',
          background: 'linear-gradient(135deg, #f8fafc, #dbeafe)',
          color: '#0f172a',
          fontSize: '1rem',
          fontWeight: 800,
          cursor: loading ? 'wait' : 'pointer',
          boxShadow: '0 16px 40px rgba(15,23,42,0.22)',
        }}
      >
        {loading ? 'Abrindo Google...' : 'Entrar com Google'}
      </button>
      {error ? (
        <p style={{ margin: 0, color: '#fda4af', fontSize: '0.95rem' }}>{error}</p>
      ) : null}
    </div>
  )
}
