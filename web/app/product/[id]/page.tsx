'use client'

import { useEffect, useState, use } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { api, formatPrice, stockClass, stockLabel, type Product } from '@/lib/api'
import { useAuth } from '@/lib/auth'

export default function ProductPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const router = useRouter()
  const { isLoggedIn } = useAuth()
  const [p, setP] = useState<Product | null>(null)
  const [loading, setLoading] = useState(true)
  const [qty, setQty] = useState(1)
  const [adding, setAdding] = useState(false)

  useEffect(() => {
    api.get(`/products/${id}`).then(data => {
      setP(data as Product)
    }).catch(() => {}).finally(() => setLoading(false))
  }, [id])

  const addToCart = async () => {
    if (!isLoggedIn) { router.push('/auth/login'); return }
    setAdding(true)
    try {
      await api.post('/cart/add', { product_id: Number(id), quantity: qty }, true)
      alert('Added to cart!')
    } catch { alert('Failed to add to cart') }
    setAdding(false)
  }

  const buyNow = async () => {
    if (!isLoggedIn) { router.push('/auth/login'); return }
    setAdding(true)
    try {
      await api.post('/cart/add', { product_id: Number(id), quantity: qty }, true)
      const order = await api.post('/checkout', {}, true)
      router.push('/checkout/' + ((order as any).order_id || Date.now()))
    } catch { alert('Checkout failed') }
    setAdding(false)
  }

  if (loading) return <div className="loading" />
  if (!p) return <div className="container section"><p className="text-center">Product not found.</p></div>

  const img = p.image_url || '/placeholder.svg'
  const isOos = p.stock <= 0

  return (
    <div className="container section">
      <div className="product-detail">
        <div className="gallery">
          <img src={img} alt={p.title} className="main-img"
            onError={e => { (e.target as HTMLImageElement).src = '/placeholder.svg' }} />
        </div>
        <div className="info">
          <div className="title">{p.title}</div>
          <div className="price-lg">{formatPrice(p.price)}</div>
          <span className={`stock-badge ${stockClass(p.stock)}`}>{stockLabel(p.stock)}</span>

          <div className="desc" style={{ marginTop: '1rem' }}>
            {p.description || 'No description available.'}
          </div>

          <div className="meta" style={{ marginTop: '1rem' }}>
            <span>Shop: <Link href={`/shops/${p.shop_slug}`} style={{ fontWeight: 600 }}>{p.shop_name}</Link></span>
          </div>

          {!isOos && (
            <div className="actions" style={{ marginTop: '1.25rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <label style={{ fontWeight: 600, fontSize: '0.85rem' }}>Qty:</label>
                <select value={qty} onChange={e => setQty(Number(e.target.value))}
                  style={{ padding: '0.4rem', borderRadius: 'var(--radius)', border: '2px solid var(--gray-200)' }}>
                  {Array.from({ length: Math.min(p.stock || 10, 10) }, (_, i) => i + 1).map(n => (
                    <option key={n} value={n}>{n}</option>
                  ))}
                </select>
              </div>
              <button className="btn btn-primary btn-lg" onClick={addToCart} disabled={adding}>
                {adding ? 'Adding...' : 'Add to Cart'}
              </button>
              <button className="btn btn-secondary btn-lg" onClick={buyNow} disabled={adding}>
                {adding ? 'Processing...' : 'Buy Now'}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
