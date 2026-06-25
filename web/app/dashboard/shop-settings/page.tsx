'use client'

import { useEffect, useState, useRef } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { api } from '@/lib/api'
import { useAuth } from '@/lib/auth'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'

const FULFILLMENT_OPTIONS = [
  { value: 'pickup', label: 'Pickup' },
  { value: 'seller_delivery', label: 'Delivery' },
]

const PAYMENT_OPTIONS = [
  { value: 'mpesa', label: 'M-Pesa' },
  { value: 'cash_on_delivery', label: 'Cash on Delivery' },
  { value: 'bank_transfer', label: 'Bank Transfer' },
]

const CATEGORIES = [
  'food', 'electronics', 'fashion', 'health', 'home',
  'sports', 'services', 'agriculture', 'other',
]

export default function ShopSettingsPage() {
  const router = useRouter()
  const { isLoggedIn, isSeller } = useAuth()
  const [shops, setShops] = useState<any[]>([])
  const [selectedShopId, setSelectedShopId] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const bannerInput = useRef<HTMLInputElement>(null)
  const [form, setForm] = useState({
    name: '',
    description: '',
    banner_image: '',
    category: '',
    location_area: '',
    fulfillment_modes: [] as string[],
    delivery_radius_km: '',
    delivery_fee: '',
    operating_hours: '',
    payment_methods: [] as string[],
    pickup_address: '',
    phone: '',
  })

  useEffect(() => {
    if (!isLoggedIn) { setLoading(false); return }
    api.get('/seller/shops', true).then(data => {
      if (Array.isArray(data) && data.length > 0) {
        setShops(data)
        selectShop(data[0])
      }
    }).catch(() => {}).finally(() => setLoading(false))
  }, [isLoggedIn])

  const selectShop = (shop: any) => {
    setSelectedShopId(shop.id)
    setForm({
      name: shop.name || '',
      description: shop.description || '',
      banner_image: shop.banner_image || '',
      category: shop.category || '',
      location_area: shop.location_area || '',
      fulfillment_modes: (shop.fulfillment_modes || '').split(',').filter(Boolean),
      delivery_radius_km: shop.delivery_radius_km?.toString() || '',
      delivery_fee: shop.delivery_fee?.toString() || '',
      operating_hours: shop.operating_hours || '',
      payment_methods: (shop.payment_methods || '').split(',').filter(Boolean),
      pickup_address: shop.pickup_address || '',
      phone: shop.phone || '',
    })
  }

  const toggleArray = (field: 'fulfillment_modes' | 'payment_methods', value: string) => {
    setForm(prev => ({
      ...prev,
      [field]: prev[field].includes(value)
        ? prev[field].filter(v => v !== value)
        : [...prev[field], value],
    }))
  }

  const update = (field: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) =>
    setForm(prev => ({ ...prev, [field]: e.target.value }))

  const handleBannerUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    setError('')
    try {
      const token = localStorage.getItem('ikobiz_token')
      const fd = new FormData()
      fd.append('file', file)
      const r = await fetch(`${API_BASE}/upload/image`, {
        method: 'POST',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: fd,
      })
      if (!r.ok) {
        const errData = await r.json().catch(() => ({}))
        throw new Error(errData.detail || 'Upload failed')
      }
      const data = await r.json()
      setForm(prev => ({ ...prev, banner_image: data.url }))
    } catch (err: any) {
      setError(err.message || 'Image upload failed')
    } finally {
      setUploading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedShopId) return
    setError('')
    setSuccess('')
    setSaving(true)
    try {
      await api.put(`/shops/${selectedShopId}`, {
        name: form.name,
        description: form.description || null,
        banner_image: form.banner_image || null,
        category: form.category || null,
        location_area: form.location_area || null,
        fulfillment_modes: form.fulfillment_modes.join(',') || null,
        delivery_radius_km: form.delivery_radius_km ? Number(form.delivery_radius_km) : null,
        delivery_fee: form.delivery_fee ? Number(form.delivery_fee) : null,
        operating_hours: form.operating_hours || null,
        payment_methods: form.payment_methods.join(',') || null,
        pickup_address: form.pickup_address || null,
        phone: form.phone || null,
      }, true)
      setSuccess('Shop settings saved!')
      // Refresh shop data
      const data = await api.get('/seller/shops', true)
      if (Array.isArray(data)) {
        setShops(data)
        const updated = data.find((s: any) => s.id === selectedShopId)
        if (updated) selectShop(updated)
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to save')
    }
    setSaving(false)
  }

  if (loading) return <div className="loading" />

  if (!isLoggedIn || !isSeller) {
    return (
      <div className="dashboard-wrap">
        <aside className="dashboard-sidebar">
          <div className="sidebar-brand">Ikobiz<span>.</span></div>
          <Link href="/dashboard" className="nav-item">📊 Dashboard</Link>
          <Link href="/dashboard/inventory" className="nav-item">📦 Inventory</Link>
          <Link href="/dashboard/shop-settings" className="nav-item active">⚙️ Shop Settings</Link>
        </aside>
        <main className="dashboard-main">
          <div className="auth-card" style={{ margin: '2rem auto' }}>
            <h1>Shop Settings</h1>
            <p className="subtitle">Please log in as a seller.</p>
            <Link href="/auth/login" className="btn btn-primary" style={{ width: '100%', justifyContent: 'center' }}>Login</Link>
          </div>
        </main>
      </div>
    )
  }

  return (
    <div className="dashboard-wrap">
      <aside className="dashboard-sidebar">
        <div className="sidebar-brand">Ikobiz<span>.</span></div>
        <Link href="/dashboard" className="nav-item">📊 Dashboard</Link>
        <Link href="/dashboard/shop-settings" className="nav-item active">⚙️ Shop Settings</Link>
      </aside>
      <main className="dashboard-main">
        <h1>Shop Settings</h1>
        <p className="subtitle" style={{ marginBottom: '1.5rem' }}>
          Configure your shop details, delivery options, and payment methods.
        </p>

        {shops.length === 0 ? (
          <div className="auth-card" style={{ textAlign: 'center', padding: '2rem' }}>
            <p>You don't have any shops yet.</p>
            <p style={{ color: 'var(--gray-500)', fontSize: '0.9rem', marginTop: '0.5rem' }}>
              Create a shop from the dashboard first.
            </p>
          </div>
        ) : (
          <>
            {shops.length > 1 && (
              <div style={{ marginBottom: '1rem', display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                <label style={{ fontWeight: 600 }}>Switch shop:</label>
                <select
                  value={selectedShopId || ''}
                  onChange={e => {
                    const shop = shops.find(s => s.id === Number(e.target.value))
                    if (shop) selectShop(shop)
                  }}
                  style={{
                    padding: '0.5rem', borderRadius: '8px', border: '1px solid var(--gray-200)',
                    fontSize: '0.9rem',
                  }}
                >
                  {shops.map(s => (
                    <option key={s.id} value={s.id}>{s.name}</option>
                  ))}
                </select>
              </div>
            )}

            <div style={{ maxWidth: 700 }}>
              <form onSubmit={handleSubmit}>
                <div className="form-group">
                  <label>Shop Name</label>
                  <input type="text" value={form.name} onChange={update('name')} required />
                </div>

                <div className="form-group">
                  <label>Description</label>
                  <textarea value={form.description} onChange={update('description')} rows={3} placeholder="Describe your shop..." />
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  <div className="form-group">
                    <label>Category</label>
                    <select value={form.category} onChange={update('category')}>
                      <option value="">Select category</option>
                      {CATEGORIES.map(c => (
                        <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>
                      ))}
                    </select>
                  </div>
                  <div className="form-group">
                    <label>Location Area</label>
                    <input type="text" value={form.location_area} onChange={update('location_area')} placeholder="e.g. Westlands, Kawangware" />
                  </div>
                </div>

                <h3 style={{ fontSize: '1rem', margin: '1.5rem 0 0.75rem', fontWeight: 700 }}>Fulfillment</h3>

                <div className="form-group">
                  <label>Fulfillment Modes</label>
                  <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                    {FULFILLMENT_OPTIONS.map(opt => (
                      <label key={opt.value} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', cursor: 'pointer' }}>
                        <input
                          type="checkbox"
                          checked={form.fulfillment_modes.includes(opt.value)}
                          onChange={() => toggleArray('fulfillment_modes', opt.value)}
                        />
                        {opt.label}
                      </label>
                    ))}
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  <div className="form-group">
                    <label>Delivery Radius (km)</label>
                    <input type="number" value={form.delivery_radius_km} onChange={update('delivery_radius_km')} min={0} step={0.5} placeholder="e.g. 10" />
                  </div>
                  <div className="form-group">
                    <label>Delivery Fee (KES)</label>
                    <input type="number" value={form.delivery_fee} onChange={update('delivery_fee')} min={0} placeholder="e.g. 200" />
                  </div>
                </div>

                <div className="form-group">
                  <label>Operating Hours (JSON)</label>
                  <input type="text" value={form.operating_hours} onChange={update('operating_hours')} placeholder='{"mon-fri":"8-18","sat":"9-15","sun":"closed"}' />
                  <div style={{ fontSize: '0.78rem', color: 'var(--gray-500)', marginTop: '0.25rem' }}>
                    JSON format: day-range to hours. Example: {'{"mon-fri":"8:00-18:00","sat":"9:00-15:00"}'}
                  </div>
                </div>

                <h3 style={{ fontSize: '1rem', margin: '1.5rem 0 0.75rem', fontWeight: 700 }}>Payment & Contact</h3>

                <div className="form-group">
                  <label>Payment Methods</label>
                  <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                    {PAYMENT_OPTIONS.map(opt => (
                      <label key={opt.value} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', cursor: 'pointer' }}>
                        <input
                          type="checkbox"
                          checked={form.payment_methods.includes(opt.value)}
                          onChange={() => toggleArray('payment_methods', opt.value)}
                        />
                        {opt.label}
                      </label>
                    ))}
                  </div>
                </div>

                <div className="form-group">
                  <label>Pickup Address</label>
                  <textarea value={form.pickup_address} onChange={update('pickup_address')} rows={2} placeholder="e.g. Moi Avenue, Ambassador Building, G4, Nairobi" />
                </div>

                <div className="form-group">
                  <label>Contact Phone</label>
                  <input type="tel" value={form.phone} onChange={update('phone')} placeholder="e.g. 254700000001" />
                </div>

                <div className="form-group">
                  <label>Shop Banner</label>
                  <div
                    onClick={() => bannerInput.current?.click()}
                    style={{
                      border: '2px dashed var(--gray-300)', borderRadius: 'var(--radius)',
                      padding: '1rem', textAlign: 'center', cursor: 'pointer',
                      background: form.banner_image ? 'transparent' : 'var(--gray-50)',
                      position: 'relative', overflow: 'hidden',
                      minHeight: 100, display: 'flex', alignItems: 'center', justifyContent: 'center',
                    }}
                  >
                    {form.banner_image ? (
                      <img src={form.banner_image} alt="Banner" style={{
                        width: '100%', height: 100, objectFit: 'cover', borderRadius: 'var(--radius)',
                      }} />
                    ) : (
                      <div style={{ color: 'var(--gray-400)' }}>
                        <div style={{ fontSize: '1.3rem' }}>🖼️</div>
                        <div style={{ fontSize: '0.82rem' }}>{uploading ? 'Uploading...' : 'Click to upload banner'}</div>
                      </div>
                    )}
                    <input ref={bannerInput} type="file" accept="image/jpeg,image/png,image/webp" onChange={handleBannerUpload} style={{ display: 'none' }} />
                  </div>
                  {form.banner_image && (
                    <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.4rem' }}>
                      <input type="url" value={form.banner_image} onChange={update('banner_image')} placeholder="Or paste image URL"
                        style={{ flex: 1, fontSize: '0.8rem', padding: '0.35rem', border: '1px solid var(--gray-200)', borderRadius: 6 }} />
                      <button onClick={() => setForm(prev => ({ ...prev, banner_image: '' }))}
                        className="btn btn-sm btn-outline" style={{ fontSize: '0.72rem' }}>Remove</button>
                    </div>
                  )}
                </div>

                {error && <div className="form-error" style={{ marginBottom: '0.75rem' }}>{error}</div>}
                {success && <div style={{ color: 'var(--secondary)', marginBottom: '0.75rem', fontWeight: 500 }}>{success}</div>}

                <div style={{ display: 'flex', gap: '0.75rem' }}>
                  <button type="submit" className="btn btn-primary" disabled={saving}>
                    {saving ? 'Saving...' : 'Save Settings'}
                  </button>
                  <Link href="/dashboard" className="btn btn-outline">Back to Dashboard</Link>
                </div>
              </form>
            </div>
          </>
        )}
      </main>
    </div>
  )
}
