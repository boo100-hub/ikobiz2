'use client'

import { useEffect, useState, useRef } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { api, formatPrice, type Product } from '@/lib/api'
import { useAuth } from '@/lib/auth'

const CATEGORIES = [
  'food', 'electronics', 'fashion', 'health', 'home',
  'sports', 'services', 'agriculture', 'other',
]

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'

export default function InventoryPage() {
  const router = useRouter()
  const { user, isLoggedIn, isSeller } = useAuth()
  const [products, setProducts] = useState<Product[]>([])
  const [shops, setShops] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [saving, setSaving] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const fileInput = useRef<HTMLInputElement>(null)
  const [form, setForm] = useState({
    shop_id: 0,
    title: '',
    description: '',
    price: '',
    stock: '0',
    image_url: '',
    category: '',
    attributes: '',
    status: 'active',
  })

  const fetchData = () => {
    return Promise.all([
      api.get('/seller/products', true).catch(() => []),
      api.get('/seller/shops', true).catch(() => []),
    ])
  }

  useEffect(() => {
    if (!isLoggedIn) { setLoading(false); return }
    if (!isSeller) { router.push('/'); return }
    fetchData().then(([prods, shopData]) => {
      setProducts(Array.isArray(prods) ? prods : [])
      setShops(Array.isArray(shopData) ? shopData : [])
      const firstShop = Array.isArray(shopData) && shopData.length > 0 ? shopData[0] : null
      if (firstShop) {
        setForm(prev => ({ ...prev, shop_id: firstShop.id }))
      }
    }).finally(() => setLoading(false))
  }, [isLoggedIn, isSeller, router])

  const openAdd = () => {
    setEditingId(null)
    setForm({
      shop_id: shops.length > 0 ? shops[0].id : 0,
      title: '', description: '', price: '', stock: '0',
      image_url: '', category: '', attributes: '', status: 'active',
    })
    setError('')
    setSuccess('')
    setShowForm(true)
  }

  const openEdit = (p: Product) => {
    setEditingId(p.id)
    setForm({
      shop_id: p.shop_id,
      title: p.title,
      description: p.description || '',
      price: p.price.toString(),
      stock: p.stock.toString(),
      image_url: p.image_url || '',
      category: p.category || '',
      attributes: p.attributes || '',
      status: p.status || 'active',
    })
    setError('')
    setSuccess('')
    setShowForm(true)
  }

  const update = (field: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) =>
    setForm(prev => ({ ...prev, [field]: e.target.value }))

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
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
        headers: token ? { 'Authorization': `Bearer ${token}` } : {},
        body: fd,
      })
      if (!r.ok) {
        const errData = await r.json().catch(() => ({}))
        throw new Error(errData.detail || 'Upload failed')
      }
      const data = await r.json()
      setForm(prev => ({ ...prev, image_url: data.url }))
    } catch (err: any) {
      setError(err.message || 'Image upload failed')
    } finally {
      setUploading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccess('')
    if (!form.shop_id) {
      setError('Please select a shop')
      return
    }
    setSaving(true)
    try {
      const body = {
        title: form.title,
        description: form.description || null,
        price: Number(form.price),
        stock: Number(form.stock),
        image_url: form.image_url || null,
        category: form.category || null,
        attributes: form.attributes || null,
        status: form.status,
      }

      if (editingId) {
        await api.put(`/products/${editingId}`, body, true)
        setSuccess('Product updated!')
      } else {
        await api.post(`/shops/${form.shop_id}/products`, body, true)
        setSuccess('Product created!')
      }
      const [prods] = await fetchData()
      setProducts(Array.isArray(prods) ? prods : [])
      setShowForm(false)
    } catch (err: any) {
      setError(err?.message || 'Failed to save product')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (productId: number) => {
    if (!confirm('Delete this product? This cannot be undone.')) return
    try {
      await api.del(`/products/${productId}`, true)
      const [prods] = await fetchData()
      setProducts(Array.isArray(prods) ? prods : [])
    } catch (err: any) {
      alert(err.message || 'Failed to delete')
    }
  }

  const handleToggleStatus = async (p: Product) => {
    const newStatus = p.status === 'active' ? 'hidden' : 'active'
    try {
      await api.put(`/products/${p.id}`, { status: newStatus }, true)
      const [prods] = await fetchData()
      setProducts(Array.isArray(prods) ? prods : [])
    } catch (err: any) {
      alert(err.message || 'Failed to update status')
    }
  }

  if (loading) return <div className="loading" />
  if (!isLoggedIn || !isSeller) {
    return (
      <div className="dashboard-wrap">
        <aside className="dashboard-sidebar">
          <div className="sidebar-brand">Ikobiz<span>.</span></div>
          <Link href="/dashboard" className="nav-item">📊 Dashboard</Link>
          <Link href="/dashboard/inventory" className="nav-item active">📦 Inventory</Link>
          <Link href="/dashboard/shop-settings" className="nav-item">⚙️ Shop Settings</Link>
        </aside>
        <main className="dashboard-main">
          <div className="auth-card" style={{ margin: '2rem auto' }}>
            <h1>Inventory</h1>
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
        <Link href="/dashboard/inventory" className="nav-item active">📦 Inventory</Link>
        <Link href="/dashboard/shop-settings" className="nav-item">⚙️ Shop Settings</Link>
      </aside>
      <main className="dashboard-main">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <h1 style={{ margin: 0 }}>Inventory</h1>
          <button onClick={openAdd} className="btn btn-primary">+ Add Product</button>
        </div>

        {error && <div className="form-error" style={{ marginBottom: '0.75rem' }}>{error}</div>}
        {success && <div style={{ color: 'var(--secondary)', marginBottom: '0.75rem', fontWeight: 500 }}>{success}</div>}

        {shops.length === 0 ? (
          <div className="auth-card" style={{ textAlign: 'center', padding: '2rem' }}>
            <p>You don't have any shops yet.</p>
            <p style={{ color: 'var(--gray-500)', fontSize: '0.9rem', marginTop: '0.5rem' }}>
              Create a shop from the dashboard first.
            </p>
          </div>
        ) : products.length === 0 ? (
          <div className="auth-card" style={{ textAlign: 'center', padding: '2rem' }}>
            <p>No products yet.</p>
            <p style={{ color: 'var(--gray-500)', fontSize: '0.9rem', marginTop: '0.5rem' }}>
              Click &quot;Add Product&quot; to list your first item.
            </p>
          </div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Image</th>
                  <th>Product</th>
                  <th>Shop</th>
                  <th>Price</th>
                  <th>Stock</th>
                  <th>Category</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {products.map(p => (
                  <tr key={p.id}>
                    <td>
                      <div style={{
                        width: 48, height: 48, borderRadius: 8, overflow: 'hidden',
                        background: 'var(--gray-100)',
                      }}>
                        <img
                          src={p.image_url || '/placeholder.svg'}
                          alt={p.title}
                          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                          onError={e => { (e.target as HTMLImageElement).src = '/placeholder.svg' }}
                        />
                      </div>
                    </td>
                    <td style={{ fontWeight: 600 }}>{p.title}</td>
                    <td style={{ fontSize: '0.85rem', color: 'var(--gray-500)' }}>{p.shop_name || '\u2014'}</td>
                    <td style={{ fontWeight: 600 }}>{formatPrice(p.price)}</td>
                    <td>
                      <span className={`badge ${p.stock > 10 ? 'badge-success' : p.stock > 0 ? 'badge-warning' : 'badge-danger'}`}>
                        {p.stock > 10 ? `${p.stock}` : p.stock > 0 ? `${p.stock} left` : 'OOS'}
                      </span>
                    </td>
                    <td style={{ fontSize: '0.82rem' }}>{p.category || '\u2014'}</td>
                    <td>
                      <span className={`badge ${p.status === 'active' ? 'badge-success' : 'badge-warning'}`}>
                        {p.status}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '0.35rem', flexWrap: 'wrap' }}>
                        <button onClick={() => openEdit(p)} className="btn btn-sm btn-outline">Edit</button>
                        <button onClick={() => handleToggleStatus(p)} className="btn btn-sm btn-warning">
                          {p.status === 'active' ? 'Hide' : 'Show'}
                        </button>
                        <button onClick={() => handleDelete(p.id)} className="btn btn-sm btn-danger">Delete</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {showForm && (
          <div className="modal-overlay" onClick={() => setShowForm(false)}>
            <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 600 }}>
              <h2 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '1.25rem' }}>
                {editingId ? 'Edit Product' : 'Add Product'}
              </h2>

              <form onSubmit={handleSubmit}>
                <div className="form-group">
                  <label>Shop</label>
                  <select value={form.shop_id} onChange={update('shop_id')} required>
                    <option value={0}>Select shop</option>
                    {shops.map(s => (
                      <option key={s.id} value={s.id}>{s.name}</option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label>Product Title *</label>
                  <input type="text" value={form.title} onChange={update('title')} required placeholder="e.g. Fresh Tomatoes" />
                </div>

                <div className="form-group">
                  <label>Description</label>
                  <textarea value={form.description} onChange={update('description')} rows={3} placeholder="Describe your product..." />
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  <div className="form-group">
                    <label>Price (KES) *</label>
                    <input type="number" value={form.price} onChange={update('price')} min={0} required placeholder="e.g. 150" />
                  </div>
                  <div className="form-group">
                    <label>Stock *</label>
                    <input type="number" value={form.stock} onChange={update('stock')} min={0} required />
                  </div>
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
                    <label>Status</label>
                    <select value={form.status} onChange={update('status')}>
                      <option value="active">Active</option>
                      <option value="hidden">Hidden</option>
                      <option value="out_of_stock">Out of Stock</option>
                    </select>
                  </div>
                </div>

                <div className="form-group">
                  <label>Attributes (JSON)</label>
                  <input type="text" value={form.attributes} onChange={update('attributes')} placeholder='{"color":"red","size":"42"}' />
                </div>

                <div className="form-group">
                  <label>Product Image</label>
                  <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
                    <input
                      type="file"
                      ref={fileInput}
                      accept="image/jpeg,image/png,image/webp,image/gif"
                      onChange={handleUpload}
                      style={{ flex: 1 }}
                    />
                    {uploading && <span style={{ color: 'var(--gray-500)', fontSize: '0.85rem' }}>Uploading...</span>}
                  </div>
                  {form.image_url && (
                    <div style={{ marginTop: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <img src={form.image_url} alt="Preview" style={{ width: 60, height: 60, borderRadius: 8, objectFit: 'cover', background: 'var(--gray-100)' }} />
                      <input type="text" value={form.image_url} onChange={update('image_url')} placeholder="Or paste image URL" style={{ flex: 1, fontSize: '0.82rem', padding: '0.4rem', border: '1px solid var(--gray-200)', borderRadius: 6 }} />
                    </div>
                  )}
                </div>

                {error && <div className="form-error" style={{ marginBottom: '0.75rem' }}>{error}</div>}

                <div style={{ display: 'flex', gap: '0.75rem', marginTop: '0.5rem' }}>
                  <button type="submit" className="btn btn-primary" disabled={saving || uploading}>
                    {saving ? 'Saving...' : editingId ? 'Update Product' : 'Add Product'}
                  </button>
                  <button type="button" onClick={() => setShowForm(false)} className="btn btn-outline">Cancel</button>
                </div>
              </form>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
