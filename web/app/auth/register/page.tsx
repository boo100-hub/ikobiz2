'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useAuth } from '@/lib/auth'

export default function RegisterPage() {
  const router = useRouter()
  const { register } = useAuth()
  const [form, setForm] = useState({
    username: '', email: '', phone: '', password: '', confirmPassword: '',
    is_seller: false,
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const update = (field: string) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm(prev => ({ ...prev, [field]: e.target.value }))

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    if (form.password !== form.confirmPassword) { setError('Passwords do not match'); return }
    setLoading(true)
    try {
      await register(form.username, form.email, form.password, form.is_seller, form.phone)
      if (form.is_seller) {
        router.push('/dashboard/onboarding')
      } else {
        router.push('/')
      }
    } catch (err: any) {
      setError(err?.message || 'Registration failed')
    }
    setLoading(false)
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1>Create Account</h1>
        <p className="subtitle">Join Ikobiz to shop and sell</p>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Username</label>
            <input type="text" value={form.username} onChange={update('username')} required placeholder="Choose a username" />
          </div>
          <div className="form-group">
            <label>Email</label>
            <input type="email" value={form.email} onChange={update('email')} required placeholder="your@email.com" />
          </div>
          <div className="form-group">
            <label>Phone (for WhatsApp notifications)</label>
            <input type="tel" value={form.phone} onChange={update('phone')} placeholder="+2547XXXXXXXX" />
          </div>
          <div className="form-group">
            <label>Password</label>
            <input type="password" value={form.password} onChange={update('password')} required minLength={6} placeholder="At least 6 characters" />
          </div>
          <div className="form-group">
            <label>Confirm Password</label>
            <input type="password" value={form.confirmPassword} onChange={update('confirmPassword')} required placeholder="Repeat your password" />
          </div>

          <div className="form-group" style={{
            background: 'var(--gray-50)', borderRadius: 'var(--radius)',
            padding: '0.75rem 1rem', marginTop: '0.5rem',
          }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', cursor: 'pointer', margin: 0 }}>
              <input
                type="checkbox"
                checked={form.is_seller}
                onChange={e => setForm(prev => ({ ...prev, is_seller: e.target.checked }))}
                style={{ width: 18, height: 18, cursor: 'pointer' }}
              />
              <div>
                <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>I want to start selling</span>
                <div style={{ fontSize: '0.78rem', color: 'var(--gray-500)', fontWeight: 400 }}>
                  Create a shop and list products for customers to discover
                </div>
              </div>
            </label>
          </div>

          {error && <div className="form-error" style={{ marginBottom: '0.75rem' }}>{error}</div>}
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Creating account...' : form.is_seller ? 'Create Your Shop' : 'Sign Up'}
          </button>
        </form>

        <div className="auth-link">
          Already have an account? <Link href="/auth/login">Log in</Link>
        </div>
      </div>
    </div>
  )
}
