'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { api, type Shop } from '@/lib/api'
import ShopCard from '@/components/ShopCard'

export default function HomePage() {
  const router = useRouter()
  const [shops, setShops] = useState<Shop[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')

  useEffect(() => {
    api.get('/shops').then(data => {
      setShops(Array.isArray(data) ? data : [])
    }).catch(() => {}).finally(() => setLoading(false))
  }, [])

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (search.trim()) {
      router.push('/market?q=' + encodeURIComponent(search.trim()))
    }
  }

  if (loading) return <div className="loading" />

  return (
    <>
      <section className="hero">
        <h1>Welcome to Ikobiz</h1>
        <p>Discover trusted shops and unique products across Africa. Shop directly or bid in our secondary market.</p>
        <form onSubmit={handleSearch} style={{ display: 'flex', gap: '0.5rem', maxWidth: 500, margin: '0 auto' }}>
          <input
            type="text"
            placeholder="Search products, shops..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            style={{ flex: 1, padding: '0.65rem 1rem', borderRadius: 50, border: '2px solid rgba(255,255,255,0.3)', background: 'rgba(255,255,255,0.15)', color: '#fff', fontSize: '0.95rem' }}
          />
          <button type="submit" className="btn btn-primary">Search</button>
        </form>
      </section>

      <div className="container section">
        <div className="section-header">
          <h2>Featured Shops</h2>
        </div>
        {shops.length === 0 ? (
          <p className="text-center" style={{ color: 'var(--gray-400)' }}>No shops available yet.</p>
        ) : (
          <div className="shop-grid">
            {shops.map(s => <ShopCard key={s.id} s={s} />)}
          </div>
        )}
      </div>
    </>
  )
}
