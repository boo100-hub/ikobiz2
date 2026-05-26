'use client'

import { useEffect, useState, use } from 'react'
import Link from 'next/link'
import { api, formatPrice, formatDate } from '@/lib/api'
import { useAuth } from '@/lib/auth'

export default function CheckoutPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const { isLoggedIn } = useAuth()
  const [orders, setOrders] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!isLoggedIn) { setLoading(false); return }
    api.get('/orders', true).then(data => {
      setOrders(Array.isArray(data) ? data : [])
    }).catch(() => {}).finally(() => setLoading(false))
  }, [isLoggedIn])

  const isNewOrder = orders.length > 0 && orders[0].id === Number(id)

  if (!isLoggedIn) return (
    <div className="container section">
      <div className="auth-card" style={{ margin: '2rem auto' }}>
        <h1>Order</h1>
        <p className="subtitle">Please log in to view your orders.</p>
        <Link href="/auth/login" className="btn btn-primary" style={{ width: '100%', justifyContent: 'center' }}>Login</Link>
      </div>
    </div>
  )

  if (loading) return <div className="loading" />

  return (
    <div className="container section">
      {isNewOrder ? (
        <div className="auth-card" style={{ margin: '0 auto 2rem', textAlign: 'center' }}>
          <div style={{ fontSize: '3rem', marginBottom: '0.5rem' }}>&#10003;</div>
          <h1>Order Confirmed!</h1>
          <p className="subtitle">Order #{id}</p>
          <div style={{ fontSize: '0.9rem', color: 'var(--gray-500)', marginBottom: '1rem' }}>
            {orders[0]?.created_at ? formatDate(orders[0].created_at) : 'Just now'}
          </div>
          <div style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--primary)', marginBottom: '1rem' }}>
            Total: {formatPrice(orders[0]?.total || 0)}
          </div>
          <p style={{ fontSize: '0.85rem', color: 'var(--gray-500)' }}>
            Your order has been placed. You will receive a confirmation via WhatsApp.
          </p>
        </div>
      ) : (
        <div className="auth-card" style={{ margin: '0 auto 2rem', textAlign: 'center' }}>
          <h1>Order #{id}</h1>
          <p className="subtitle">Viewing previous order</p>
        </div>
      )}

      <h2 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '1rem' }}>Order History</h2>
      {orders.length === 0 ? (
        <p className="text-center" style={{ color: 'var(--gray-400)' }}>No orders yet.</p>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Order #</th>
                <th>Date</th>
                <th>Items</th>
                <th>Total</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((o: any) => (
                <tr key={o.id}>
                  <td><Link href={`/checkout/${o.id}`} style={{ fontWeight: 600 }}>#{o.id}</Link></td>
                  <td>{formatDate(o.created_at || '')}</td>
                  <td>{(o.items || []).length} item(s)</td>
                  <td style={{ fontWeight: 700 }}>{formatPrice(o.total || 0)}</td>
                  <td><span className={`badge ${o.status === 'completed' ? 'badge-success' : o.status === 'cancelled' ? 'badge-danger' : 'badge-primary'}`}>{o.status || 'pending'}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div style={{ textAlign: 'center', marginTop: '2rem' }}>
        <Link href="/" className="btn btn-primary">Continue Shopping</Link>
      </div>
    </div>
  )
}
