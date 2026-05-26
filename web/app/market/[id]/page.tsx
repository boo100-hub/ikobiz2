'use client'

import { useEffect, useState, use } from 'react'
import { useRouter } from 'next/navigation'
import { api, formatPrice, type IkobizListing } from '@/lib/api'
import { useAuth } from '@/lib/auth'

export default function ListingPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const router = useRouter()
  const { user, isLoggedIn } = useAuth()
  const [p, setP] = useState<IkobizListing | null>(null)
  const [loading, setLoading] = useState(true)
  const [bidAmount, setBidAmount] = useState('')
  const [bidMsg, setBidMsg] = useState('')
  const [buying, setBuying] = useState(false)

  useEffect(() => {
    api.get(`/ikobiz/products/${id}`).then(data => {
      const item = data as IkobizListing
      setP(item)
      setBidAmount(String(item.starting_price + 1))
    }).catch(() => {}).finally(() => setLoading(false))
  }, [id])

  const placeBid = async () => {
    if (!isLoggedIn) { router.push('/auth/login'); return }
    if (!bidAmount || Number(bidAmount) <= 0) { setBidMsg('Enter a valid bid amount'); return }
    setBidMsg('')
    try {
      await api.post(`/ikobiz/products/${id}/bid`, { amount: Number(bidAmount) }, true)
      setBidMsg('Bid placed successfully! Waiting for seller response.')
    } catch (e: any) {
      setBidMsg(e?.message || 'Failed to place bid')
    }
  }

  const buyNow = async () => {
    if (!isLoggedIn) { router.push('/auth/login'); return }
    setBuying(true)
    try {
      await api.post('/cart/add', { listing_id: Number(id), quantity: 1 }, true)
      alert('Added to cart!')
    } catch { alert('Failed to add to cart') }
    setBuying(false)
  }

  if (loading) return <div className="loading" />
  if (!p) return <div className="container section"><p className="text-center">Listing not found.</p></div>

  const img = p.image_url || '/placeholder.svg'
  const isClosed = p.status === 'CLOSED' || p.status === 'SOLD'
  const hasBuyNow = p.buy_now_price != null

  return (
    <div className="container section">
      <div className="product-detail">
        <div className="gallery">
          <img src={img} alt={p.title} className="main-img"
            onError={e => { (e.target as HTMLImageElement).src = '/placeholder.svg' }} />
        </div>
        <div className="info">
          <div className="badge-row" style={{ display: 'flex', gap: '0.4rem', marginBottom: '0.5rem', flexWrap: 'wrap' }}>
            <span className="badge badge-primary">Bid</span>
            {hasBuyNow && <span className="badge badge-success">Buy Now</span>}
            {p.status === 'CLOSED' && <span className="badge badge-danger">Closed</span>}
            {p.status === 'SOLD' && <span className="badge badge-danger">Sold</span>}
            {p.status === 'NEGOTIATING' && <span className="badge badge-warning">Negotiating</span>}
          </div>

          <div className="title">{p.title}</div>
          <div style={{ fontSize: '0.85rem', color: 'var(--gray-500)', marginBottom: '0.5rem' }}>
            Seller: {p.seller_name || 'Unknown'}
            {p.quantity > 0 && ` · Quantity: ${p.quantity}`}
          </div>

          <div className="price-lg" style={{ color: 'var(--primary)' }}>{formatPrice(p.starting_price)}</div>
          {hasBuyNow && (
            <div style={{ fontSize: '0.95rem', color: 'var(--secondary)', marginBottom: '0.75rem' }}>
              Buy Now: <strong>{formatPrice(p.buy_now_price!)}</strong>
            </div>
          )}

          <div className="desc" style={{ marginTop: '1rem' }}>
            {p.description || 'No description available.'}
          </div>

          {!isClosed && (
            <div className="actions" style={{ marginTop: '1.25rem' }}>
              <div style={{ marginBottom: '0.75rem' }}>
                <label style={{ fontWeight: 600, fontSize: '0.85rem', display: 'block', marginBottom: '0.3rem' }}>
                  Your Bid Amount
                </label>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <input type="number" value={bidAmount} onChange={e => setBidAmount(e.target.value)}
                    min={p.starting_price + 1} step={1}
                    style={{ flex: 1, padding: '0.65rem 0.85rem', border: '2px solid var(--gray-200)', borderRadius: 'var(--radius)', fontSize: '0.92rem' }} />
                  <button className="btn btn-primary" onClick={placeBid}>Place Bid</button>
                </div>
                {bidMsg && <div style={{ fontSize: '0.85rem', marginTop: '0.3rem', color: bidMsg.includes('Failed') ? 'var(--danger)' : 'var(--secondary)' }}>{bidMsg}</div>}
              </div>

              {hasBuyNow && (
                <button className="btn btn-secondary btn-lg" onClick={buyNow} disabled={buying} style={{ width: '100%' }}>
                  {buying ? 'Adding...' : `Buy Now - ${formatPrice(p.buy_now_price!)}`}
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
