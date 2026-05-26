'use client'

import { useEffect, useState, use } from 'react'
import { useRouter } from 'next/navigation'
import { api, formatPrice, type IkobizListing } from '@/lib/api'
import IkobizCard from '@/components/IkobizCard'
import { useAuth } from '@/lib/auth'

export default function MarketPage({ searchParams }: { searchParams: Promise<{ [key: string]: string | string[] | undefined }> }) {
  const { q } = use(searchParams)
  const query = (q as string) || ''
  const router = useRouter()
  const { isLoggedIn } = useAuth()
  const [listings, setListings] = useState<IkobizListing[]>([])
  const [loading, setLoading] = useState(true)
  const [searchInput, setSearchInput] = useState(query)
  const [sort, setSort] = useState('newest')
  const [statusFilter, setStatusFilter] = useState('')

  useEffect(() => {
    const params = new URLSearchParams()
    if (query) params.set('q', query)
    if (sort) params.set('sort', sort)
    if (statusFilter && statusFilter !== 'all') params.set('status', statusFilter)

    api.get('/ikobiz/products?' + params.toString()).then(data => {
      setListings(Array.isArray(data) ? data : [])
    }).catch(() => {}).finally(() => setLoading(false))
  }, [query, sort, statusFilter])

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    const params = new URLSearchParams()
    if (searchInput.trim()) params.set('q', searchInput.trim())
    router.push('/market' + (params.toString() ? '?' + params.toString() : ''))
  }

  return (
    <>
      <section className="hero" style={{ padding: '2rem 1rem' }}>
        <h1>Secondary Market</h1>
        <p>Bid on unique items or buy instantly. Find deals you won&apos;t find anywhere else.</p>
        <form onSubmit={handleSearch} style={{ display: 'flex', gap: '0.5rem', maxWidth: 500, margin: '0.75rem auto 0' }}>
          <input type="text" placeholder="Search listings..." value={searchInput}
            onChange={e => setSearchInput(e.target.value)}
            style={{ flex: 1, padding: '0.65rem 1rem', borderRadius: 50, border: '2px solid rgba(255,255,255,0.3)', background: 'rgba(255,255,255,0.15)', color: '#fff', fontSize: '0.95rem' }} />
          <button type="submit" className="btn btn-primary">Search</button>
        </form>
      </section>

      <div className="container section">
        <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', flexWrap: 'wrap', alignItems: 'center' }}>
          <div>
            <label style={{ fontSize: '0.82rem', fontWeight: 600, marginRight: '0.4rem' }}>Sort:</label>
            <select value={sort} onChange={e => setSort(e.target.value)}
              style={{ padding: '0.4rem 0.75rem', borderRadius: 'var(--radius)', border: '2px solid var(--gray-200)' }}>
              <option value="newest">Newest</option>
              <option value="price_asc">Price: Low to High</option>
              <option value="price_desc">Price: High to Low</option>
              <option value="ending">Ending Soon</option>
            </select>
          </div>
          <div>
            <label style={{ fontSize: '0.82rem', fontWeight: 600, marginRight: '0.4rem' }}>Status:</label>
            <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)}
              style={{ padding: '0.4rem 0.75rem', borderRadius: 'var(--radius)', border: '2px solid var(--gray-200)' }}>
              <option value="">All</option>
              <option value="OPEN">Open</option>
              <option value="NEGOTIATING">Negotiating</option>
              <option value="CLOSED">Closed</option>
              <option value="SOLD">Sold</option>
            </select>
          </div>
          {isLoggedIn && (
            <button className="btn btn-primary btn-sm" onClick={() => router.push('/dashboard/create-listing')}>
              + Create Listing
            </button>
          )}
        </div>

        {loading ? <div className="loading" /> : listings.length === 0 ? (
          <p className="text-center" style={{ color: 'var(--gray-400)' }}>No listings found.</p>
        ) : (
          <div className="product-grid">
            {listings.map(p => <IkobizCard key={p.id} p={p} />)}
          </div>
        )}
      </div>
    </>
  )
}
