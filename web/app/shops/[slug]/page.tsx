'use client'

import { useEffect, useState, use } from 'react'
import { api, formatPrice, type Shop, type Product } from '@/lib/api'
import ProductCard from '@/components/ProductCard'
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
          </div>
          <div className="shop-stats">
            <div className="stat"><div className="num">{products.length}</div><div className="label">Products</div></div>
          </div>
        </div>
      </div>

      <div className="container section">
        <h2 style={{ marginBottom: '1rem', fontSize: '1.2rem', fontWeight: 700 }}>Products</h2>
        {products.length === 0 ? (
          <p className="text-center" style={{ color: 'var(--gray-400)' }}>No products yet.</p>
        ) : (
          <div className="product-grid">
            {products.map(p => <ProductCard key={p.id} p={p} />)}
          </div>
        )}
      </div>
    </>
  )
}
