'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useAuth } from '@/lib/auth'

export default function RegisterPage() {
  const router = useRouter()
  const { register } = useAuth()
  const [form, setForm] = useState({ username: '', email: '', phone: '', password: '', confirmPassword: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const update = (field: string) => (e: React.ChangeEvent<HTMLInputElement>) => setForm(prev => ({ ...prev, [field]: e.target.value }))

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    if (form.password !== form.confirmPassword) { setError('Passwords do not match'); return }
    setLoading(true)
    try {
      await register(form.username, form.email, form.password, false, form.phone)
      router.push('/')
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
          {error && <div className="form-error" style={{ marginBottom: '0.75rem' }}>{error}</div>}
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Creating account...' : 'Sign Up'}
          </button>
        </form>

        <div className="auth-link">
          Already have an account? <Link href="/auth/login">Log in</Link>
        </div>
      </div>
    </div>
  )
}
