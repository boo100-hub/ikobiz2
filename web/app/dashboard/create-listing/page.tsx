'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { api } from '@/lib/api'
import { useAuth } from '@/lib/auth'

export default function CreateListingPage() {
  const router = useRouter()
  const { isLoggedIn, isSeller } = useAuth()
  const [form, setForm] = useState({
    title: '', description: '', starting_price: '', buy_now_price: '',
    quantity: '1', image_url: '',
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  if (!isLoggedIn || !isSeller) {
    return (
      <div className="dashboard-wrap">
        <aside className="dashboard-sidebar">
          <div className="sidebar-brand">Ikobiz<span>.</span></div>
          <Link href="/dashboard" className="nav-item">&#128202; Dashboard</Link>
          <Link href="/dashboard/ikobiz" className="nav-item">&#128176; Ikobiz Listings</Link>
          <Link href="/dashboard/create-listing" className="nav-item active">&#10133; New Listing</Link>
        </aside>
        <main className="dashboard-main">
          <div className="auth-card" style={{ margin: '2rem auto' }}>
            <h1>Create Listing</h1>
            <p className="subtitle">Please log in as a seller.</p>
            <Link href="/auth/login" className="btn btn-primary" style={{ width: '100%', justifyContent: 'center' }}>Login</Link>
          </div>
        </main>
      </div>
    )
  }

  const update = (field: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
    setForm(prev => ({ ...prev, [field]: e.target.value }))

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    if (!form.title || !form.starting_price) { setError('Title and starting price are required'); return }
    setLoading(true)
    try {
      await api.post('/ikobiz/products', {
        title: form.title,
        description: form.description,
        starting_price: Number(form.starting_price),
        buy_now_price: form.buy_now_price ? Number(form.buy_now_price) : null,
        quantity: Number(form.quantity) || 1,
        image_url: form.image_url || null,
      }, true)
      router.push('/dashboard/ikobiz')
    } catch (err: any) {
      setError(err?.message || 'Failed to create listing')
    }
    setLoading(false)
  }

  return (
    <div className="dashboard-wrap">
      <aside className="dashboard-sidebar">
        <div className="sidebar-brand">Ikobiz<span>.</span></div>
        <Link href="/dashboard" className="nav-item">&#128202; Dashboard</Link>
        <Link href="/dashboard/ikobiz" className="nav-item">&#128176; Ikobiz Listings</Link>
        <Link href="/dashboard/create-listing" className="nav-item active">&#10133; New Listing</Link>
      </aside>
      <main className="dashboard-main">
        <h1>Create New Listing</h1>

        <div style={{ maxWidth: 600 }}>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Title *</label>
              <input type="text" value={form.title} onChange={update('title')} required placeholder="What are you selling?" />
            </div>
            <div className="form-group">
              <label>Description</label>
              <textarea value={form.description} onChange={update('description')} rows={4} placeholder="Describe your item..." />
            </div>
            <div className="form-group">
              <label>Starting Price (KES) *</label>
              <input type="number" value={form.starting_price} onChange={update('starting_price')} required min={1} placeholder="1000" />
            </div>
            <div className="form-group">
              <label>Buy Now Price (KES, optional)</label>
              <input type="number" value={form.buy_now_price} onChange={update('buy_now_price')} min={1} placeholder="Leave blank for auction only" />
            </div>
            <div className="form-group">
              <label>Quantity</label>
              <input type="number" value={form.quantity} onChange={update('quantity')} min={1} />
            </div>
            <div className="form-group">
              <label>Image URL</label>
              <input type="url" value={form.image_url} onChange={update('image_url')} placeholder="https://example.com/image.jpg" />
            </div>
            {error && <div className="form-error" style={{ marginBottom: '0.75rem' }}>{error}</div>}
            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <button type="submit" className="btn btn-primary" disabled={loading}>
                {loading ? 'Creating...' : 'Create Listing'}
              </button>
              <Link href="/dashboard/ikobiz" className="btn btn-outline">Cancel</Link>
            </div>
          </form>
        </div>
      </main>
    </div>
  )
}
