'use client'

import { useEffect, useState, use } from 'react'
import { api, formatPrice, type Shop, type Product } from '@/lib/api'
import { ProductCard } from '@/components/ProductCard'
import { useAuth } from '@/lib/auth'

export default function ShopPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = use(params)
  const { isLoggedIn } = useAuth()
  const [shop, setShop] = useState<Shop | null>(null)
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    (async () => {
      try {
        const shops = await api.get('/shops') as Shop[]
        const found = shops.find(s => s.slug === slug)
        if (!found) throw new Error('Shop not found')
        setShop(found)
        const prodData = await api.get(`/shops/${found.id}/products`)
        setProducts(Array.isArray(prodData) ? prodData : [])
      } catch {}
      setLoading(false)
    })()
  }, [slug])

  if (loading) return <div className="loading" />
  if (!shop) return <div className="container section"><p className="text-center" style={{ color: 'var(--gray-400)' }}>Shop not found.</p></div>

  const modes = shop.fulfillment_modes
    ? shop.fulfillment_modes.replace(/,/g, ' + ').replace(/_/g, ' ')
    : null
  const payments = shop.payment_methods
    ? shop.payment_methods.replace(/,/g, ', ').replace(/_/g, ' ')
    : null

  const categoryBadge = shop.category
    ? shop.category.charAt(0).toUpperCase() + shop.category.slice(1)
    : null

  return (
    <>
      <div className="shop-header">
        <div className="shop-banner">
          <img src={shop.banner_image || '/banner-placeholder.svg'} alt={shop.name}
            onError={e => { (e.target as HTMLImageElement).src = '/banner-placeholder.svg' }} />
        </div>
        <div className="shop-info-bar">
          <img src="/shop-placeholder.svg" alt={shop.name} className="shop-logo" />
          <div className="info">
            <h1>{shop.name}</h1>
            <p>{shop.description || `Quality products from ${shop.name}`}</p>
            <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem', flexWrap: 'wrap' }}>
              {categoryBadge && <span className="badge badge-primary">{categoryBadge}</span>}
              {shop.location_area && <span className="badge badge-success">📍 {shop.location_area}</span>}
            </div>
          </div>
          <div className="shop-stats">
            <div className="stat"><div className="num">{products.length}</div><div className="label">Products</div></div>
            <button
              onClick={() => {
                const msg = encodeURIComponent(`I'm looking at products from ${shop.name} (${shop.slug}) on Ikobiz. Can you help me?`)
                window.open(`https://wa.me/?text=${msg}`, '_blank')
              }}
              style={{
                marginTop: '0.5rem', width: '100%', padding: '0.5rem 1rem',
                background: 'var(--primary, #25D366)', color: 'white', border: 'none',
                borderRadius: '0.5rem', cursor: 'pointer', fontWeight: 600, fontSize: '0.9rem'
              }}
            >
              💬 Ask about products
            </button>
          </div>
        </div>
      </div>

      {/* Fulfillment & Operations Info */}
      {(modes || payments || shop.delivery_radius_km || shop.pickup_address || shop.phone) && (
        <div className="container section" style={{ paddingTop: '0' }}>
          <div style={{
            background: 'var(--white)', borderRadius: 'var(--radius-lg)',
            padding: '1.25rem', boxShadow: 'var(--shadow)',
            display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '1rem'
          }}>
            {modes && (
              <div>
                <div style={{ fontSize: '0.75rem', color: 'var(--gray-500)', fontWeight: 600, textTransform: 'uppercase' }}>Fulfillment</div>
                <div style={{ fontSize: '0.9rem', fontWeight: 500 }}>🚚 {modes}</div>
              </div>
            )}
            {shop.location_area && (
              <div>
                <div style={{ fontSize: '0.75rem', color: 'var(--gray-500)', fontWeight: 600, textTransform: 'uppercase' }}>Location</div>
                <div style={{ fontSize: '0.9rem', fontWeight: 500 }}>📍 {shop.location_area}</div>
              </div>
            )}
            {shop.delivery_radius_km ? (
              <div>
                <div style={{ fontSize: '0.75rem', color: 'var(--gray-500)', fontWeight: 600, textTransform: 'uppercase' }}>Delivery Radius</div>
                <div style={{ fontSize: '0.9rem', fontWeight: 500 }}>📏 {shop.delivery_radius_km} km</div>
              </div>
            ) : null}
            {shop.delivery_fee ? (
              <div>
                <div style={{ fontSize: '0.75rem', color: 'var(--gray-500)', fontWeight: 600, textTransform: 'uppercase' }}>Delivery Fee</div>
                <div style={{ fontSize: '0.9rem', fontWeight: 500 }}>{formatPrice(shop.delivery_fee)}</div>
              </div>
            ) : null}
            {payments && (
              <div>
                <div style={{ fontSize: '0.75rem', color: 'var(--gray-500)', fontWeight: 600, textTransform: 'uppercase' }}>Payment</div>
                <div style={{ fontSize: '0.9rem', fontWeight: 500 }}>💳 {payments}</div>
              </div>
            )}
            {shop.pickup_address && (
              <div>
                <div style={{ fontSize: '0.75rem', color: 'var(--gray-500)', fontWeight: 600, textTransform: 'uppercase' }}>Pickup Address</div>
                <div style={{ fontSize: '0.9rem', fontWeight: 500 }}>🏪 {shop.pickup_address}</div>
              </div>
            )}
            {shop.phone && (
              <div>
                <div style={{ fontSize: '0.75rem', color: 'var(--gray-500)', fontWeight: 600, textTransform: 'uppercase' }}>Contact</div>
                <div style={{ fontSize: '0.9rem', fontWeight: 500 }}>📞 {shop.phone}</div>
              </div>
            )}
          </div>
        </div>
      )}

      <div className="container section">
        <h2 style={{ marginBottom: '1rem', fontSize: '1.2rem', fontWeight: 700 }}>Products</h2>
        {products.length === 0 ? (
          <p className="text-center" style={{ color: 'var(--gray-400)' }}>No products yet.</p>
        ) : (
          <div className="product-grid">
            {products.map(p => <ProductCard key={p.id} product={p} />)}
          </div>
        )}
      </div>
    </>
  )
}
