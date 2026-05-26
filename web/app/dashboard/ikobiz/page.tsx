'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { api, formatPrice, type IkobizListing } from '@/lib/api'
import { useAuth } from '@/lib/auth'

export default function IkobizDashboardPage() {
  const router = useRouter()
  const { isLoggedIn, isSeller } = useAuth()
  const [listings, setListings] = useState<IkobizListing[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!isLoggedIn || !isSeller) { setLoading(false); return }
    api.get('/seller/ikobiz-listings', true).then(data => {
      setListings(Array.isArray(data) ? data : [])
    }).catch(() => {}).finally(() => setLoading(false))
  }, [isLoggedIn, isSeller])

  if (loading) return <div className="loading" />
  if (!isLoggedIn) return (
    <div className="container section">
      <div className="auth-card" style={{ margin: '2rem auto' }}>
        <h1>Ikobiz Listings</h1>
        <p className="subtitle">Please log in as a seller.</p>
        <Link href="/auth/login" className="btn btn-primary" style={{ width: '100%', justifyContent: 'center' }}>Login</Link>
      </div>
    </div>
  )

  return (
    <div className="dashboard-wrap">
      <aside className="dashboard-sidebar">
        <div className="sidebar-brand">Ikobiz<span>.</span></div>
        <Link href="/dashboard" className="nav-item">&#128202; Dashboard</Link>
        <Link href="/dashboard/ikobiz" className="nav-item active">&#128176; Ikobiz Listings</Link>
        <Link href="/dashboard/create-listing" className="nav-item">&#10133; New Listing</Link>
      </aside>
      <main className="dashboard-main">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <h1 style={{ margin: 0 }}>Ikobiz Listings</h1>
          <Link href="/dashboard/create-listing" className="btn btn-primary">+ New Listing</Link>
        </div>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Title</th>
                <th>Price</th>
                <th>Qty</th>
                <th>Status</th>
                <th>Offers</th>
                <th>Created</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {listings.length === 0 ? (
                <tr><td colSpan={7} className="text-center" style={{ color: 'var(--gray-400)' }}>No listings yet</td></tr>
              ) : listings.map(l => (
                <tr key={l.id}>
                  <td style={{ fontWeight: 600 }}>{l.title}</td>
                  <td>{formatPrice(l.starting_price)}</td>
                  <td>{l.quantity}</td>
                  <td>
                    <span className={`badge ${l.status === 'OPEN' ? 'badge-primary' : l.status === 'NEGOTIATING' ? 'badge-warning' : 'badge-danger'}`}>
                      {l.status}
                    </span>
                  </td>
                  <td>{l.bid_count || 0}</td>
                  <td style={{ fontSize: '0.82rem', color: 'var(--gray-500)' }}>
                    {l.created_at ? new Date(l.created_at).toLocaleDateString() : '-'}
                  </td>
                  <td>
                    <Link href={`/market/${l.id}`} className="btn btn-sm btn-outline">View</Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  )
}
