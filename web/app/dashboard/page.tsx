'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { api, formatPrice, type Order } from '@/lib/api'
import { useAuth } from '@/lib/auth'

export default function DashboardPage() {
  const router = useRouter()
  const { user, isLoggedIn, isSeller } = useAuth()
  const [orders, setOrders] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!isLoggedIn) { setLoading(false); return }
    if (!isSeller) { router.push('/'); return }
    Promise.all([
      api.get('/seller/shop-orders', true).catch(() => []),
      api.get('/seller/ikobiz-orders', true).catch(() => []),
    ]).then(([shopOrders, ikobizOrders]) => {
      const allOrders = [
        ...(Array.isArray(shopOrders) ? shopOrders : []),
        ...(Array.isArray(ikobizOrders) ? ikobizOrders : []),
      ]
      allOrders.sort((a: any, b: any) => new Date(b.created_at || '').getTime() - new Date(a.created_at || '').getTime())
      setOrders(allOrders)
    }).catch(() => {}).finally(() => setLoading(false))
  }, [isLoggedIn, isSeller, router])

  if (loading) return <div className="loading" />
  if (!isLoggedIn) return (
    <div className="container section">
      <div className="auth-card" style={{ margin: '2rem auto' }}>
        <h1>Dashboard</h1>
        <p className="subtitle">Please log in as a seller.</p>
        <Link href="/auth/login" className="btn btn-primary" style={{ width: '100%', justifyContent: 'center' }}>Login</Link>
      </div>
    </div>
  )

  const totalRevenue = orders.reduce((s: number, o: any) => s + (o.total || 0), 0)

  return (
    <div className="dashboard-wrap">
      <aside className="dashboard-sidebar">
        <div className="sidebar-brand">Ikobiz<span>.</span></div>
        <Link href="/dashboard" className="nav-item active">&#128202; Dashboard</Link>
        <Link href="/dashboard/ikobiz" className="nav-item">&#128176; Ikobiz Listings</Link>
        <Link href="/dashboard/create-listing" className="nav-item">&#10133; New Listing</Link>
      </aside>
      <main className="dashboard-main">
        <h1>Welcome, {user?.username}</h1>

        <div className="stat-grid">
          <div className="stat-card">
            <div className="stat-label">Total Orders</div>
            <div className="stat-value">{orders.length}</div>
          </div>
          <div className="stat-card" style={{ borderLeftColor: 'var(--secondary)' }}>
            <div className="stat-label">Total Revenue</div>
            <div className="stat-value">{formatPrice(totalRevenue)}</div>
          </div>
        </div>

        <h2 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.75rem' }}>Recent Orders</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Order #</th>
                <th>Items</th>
                <th>Total</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {orders.length === 0 ? (
                <tr><td colSpan={4} className="text-center" style={{ color: 'var(--gray-400)' }}>No orders yet</td></tr>
              ) : orders.slice(0, 10).map((o: any) => (
                <tr key={o.order_id || o.id}>
                  <td style={{ fontWeight: 600 }}>#{(o.order_id || o.id)}</td>
                  <td>{(o.items || []).length} item(s)</td>
                  <td>{formatPrice(o.total || 0)}</td>
                  <td><span className={`badge ${o.status === 'completed' ? 'badge-success' : o.status === 'cancelled' ? 'badge-danger' : 'badge-primary'}`}>{o.status || 'pending'}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  )
}
