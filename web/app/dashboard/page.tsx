'use client'

import { useEffect, useState, useRef } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { api, formatPrice, formatDate, type Message } from '@/lib/api'
import { useAuth } from '@/lib/auth'

const STATUS_FLOW: Record<string, string[]> = {
  PENDING: ['CONFIRMED', 'CANCELLED'],
  CONFIRMED: ['PAID', 'DISPATCHED', 'CANCELLED'],
  PAID: ['DISPATCHED', 'CANCELLED'],
  DISPATCHED: ['SHIPPED', 'DELIVERED', 'CANCELLED'],
  SHIPPED: ['DELIVERED', 'CANCELLED'],
  DELIVERED: [],
  CANCELLED: [],
}

const STATUS_LABELS: Record<string, string> = {
  PENDING: '⏳ Pending',
  CONFIRMED: '✅ Confirmed',
  PAID: '💰 Paid',
  DISPATCHED: '🚚 Dispatched',
  SHIPPED: '📦 Shipped',
  DELIVERED: '📬 Delivered',
  CANCELLED: '❌ Cancelled',
}

const STATUS_COLORS: Record<string, string> = {
  PENDING: 'badge-primary',
  CONFIRMED: 'badge-success',
  PAID: 'badge-success',
  DISPATCHED: 'badge-warning',
  SHIPPED: 'badge-warning',
  DELIVERED: 'badge-success',
  CANCELLED: 'badge-danger',
}

const NEXT_ACTIONS: Record<string, { label: string; nextStatus: string; color: string }[]> = {
  PENDING: [{ label: '✅ Confirm', nextStatus: 'CONFIRMED', color: 'btn-secondary' }],
  CONFIRMED: [{ label: '💰 Mark Paid', nextStatus: 'PAID', color: 'btn-success' }, { label: '🚚 Dispatch', nextStatus: 'DISPATCHED', color: 'btn-warning' }],
  PAID: [{ label: '🚚 Dispatch', nextStatus: 'DISPATCHED', color: 'btn-warning' }],
  DISPATCHED: [{ label: '📦 Ship', nextStatus: 'SHIPPED', color: 'btn-secondary' }, { label: '📬 Delivered', nextStatus: 'DELIVERED', color: 'btn-secondary' }],
  SHIPPED: [{ label: '📬 Delivered', nextStatus: 'DELIVERED', color: 'btn-secondary' }],
  DELIVERED: [],
  CANCELLED: [],
}

export default function DashboardPage() {
  const router = useRouter()
  const { user, isLoggedIn, isSeller } = useAuth()
  const [orders, setOrders] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [expandedOrder, setExpandedOrder] = useState<number | null>(null)
  const [messages, setMessages] = useState<Record<number, Message[]>>({})
  const [newMessage, setNewMessage] = useState('')
  const [sending, setSending] = useState(false)
  const [summary, setSummary] = useState<any>(null)
  const [updating, setUpdating] = useState<number | null>(null)
  const [shops, setShops] = useState<any[]>([])
  const [onboarded, setOnboarded] = useState(false)
  const chatEnd = useRef<HTMLDivElement>(null)

  const fetchData = () => {
    setLoading(true)
    Promise.all([
      api.get('/seller/shop-orders', true).catch(() => []),
      api.get('/dashboard/summary', true).catch(() => null),
      api.get('/seller/shops', true).catch(() => []),
    ]).then(([shopOrders, summaryData, shopData]) => {
      const allOrders = Array.isArray(shopOrders) ? shopOrders : []
      allOrders.sort((a: any, b: any) => new Date(b.created_at || '').getTime() - new Date(a.created_at || '').getTime())
      setOrders(allOrders)
      setSummary(summaryData)
      setShops(Array.isArray(shopData) ? shopData : [])
    }).catch(() => {}).finally(() => setLoading(false))
  }

  useEffect(() => {
    if (!isLoggedIn) { setLoading(false); return }
    if (!isSeller) { router.push('/'); return }
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search)
      if (params.get('onboarded') === '1') {
        setOnboarded(true)
        window.history.replaceState({}, '', '/dashboard')
      }
    }
    fetchData()
  }, [isLoggedIn, isSeller, router])

  useEffect(() => {
    chatEnd.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, expandedOrder])

  const updateStatus = async (orderId: number, newStatus: string) => {
    setUpdating(orderId)
    try {
      await api.patch(`/orders/${orderId}/status`, { status: newStatus }, true)
      await fetchData()
    } catch (e: any) {
      alert(e.message || 'Failed to update status')
    } finally {
      setUpdating(null)
    }
  }

  const toggleOrder = async (orderId: number) => {
    if (expandedOrder === orderId) {
      setExpandedOrder(null)
      return
    }
    setExpandedOrder(orderId)
    if (!messages[orderId]) {
      try {
        const data = await api.get(`/orders/${orderId}/messages`, true)
        setMessages(prev => ({ ...prev, [orderId]: Array.isArray(data) ? data : [] }))
      } catch {
        setMessages(prev => ({ ...prev, [orderId]: [] }))
      }
    }
  }

  const handleSend = async (orderId: number) => {
    if (!newMessage.trim() || sending) return
    setSending(true)
    try {
      const msg = await api.post(`/orders/${orderId}/messages`, { content: newMessage.trim() }, true)
      setMessages(prev => ({ ...prev, [orderId]: [...(prev[orderId] || []), msg] }))
      setNewMessage('')
    } catch (e: any) {
      alert(e.message || 'Failed to send message')
    } finally {
      setSending(false)
    }
  }

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

  const totalRevenue = summary?.total_revenue ?? orders.reduce((s: number, o: any) => s + (o.total || 0), 0)

  return (
    <div className="dashboard-wrap">
      <aside className="dashboard-sidebar">
        <div className="sidebar-brand">Ikobiz<span>.</span></div>
        <Link href="/dashboard" className="nav-item active">📊 Dashboard</Link>
        <Link href="/dashboard/inventory" className="nav-item">📦 Inventory</Link>
        <Link href="/dashboard/shop-settings" className="nav-item">⚙️ Shop Settings</Link>
      </aside>
      <main className="dashboard-main">
        <h1>Welcome, {user?.username}</h1>

        {onboarded && (
          <div style={{
            background: '#d1fae5', color: '#065f46', padding: '1rem 1.25rem',
            borderRadius: 'var(--radius-lg)', marginBottom: '1.25rem',
            display: 'flex', alignItems: 'center', gap: '0.75rem',
            fontSize: '0.92rem', fontWeight: 500,
          }}>
            <span style={{ fontSize: '1.3rem' }}>🎉</span>
            Your shop is live! Start adding more products from the{" "}
            <Link href="/dashboard/inventory" style={{
              fontWeight: 700, color: '#065f46', textDecoration: 'underline',
            }}>Inventory</Link> page.
          </div>
        )}

        {shops.length === 0 ? (
          <div style={{
            background: 'white', borderRadius: 'var(--radius-xl)',
            boxShadow: 'var(--shadow-lg)', padding: '3rem 2rem',
            textAlign: 'center', maxWidth: 500, margin: '0 auto',
          }}>
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🏪</div>
            <h2 style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: '0.5rem' }}>
              You don&apos;t have a shop yet
            </h2>
            <p style={{ color: 'var(--gray-500)', marginBottom: '1.5rem', fontSize: '0.95rem' }}>
              Set up your shop to start selling on Ikobiz. It only takes a few minutes!
            </p>
            <Link href="/dashboard/onboarding" className="btn btn-primary btn-lg">
              🚀 Create Your Shop
            </Link>
            <div style={{ marginTop: '1rem' }}>
              <Link href="/dashboard/inventory" className="btn btn-outline btn-sm">
                Or manage existing products
              </Link>
            </div>
          </div>
        ) : summary && (
          <div className="stat-grid">
            <div className="stat-card">
              <div className="stat-label">⏳ Pending</div>
              <div className="stat-value">{summary.pending_orders || 0}</div>
            </div>
            <div className="stat-card" style={{ borderLeftColor: 'var(--secondary)' }}>
              <div className="stat-label">✅ Confirmed</div>
              <div className="stat-value">{summary.confirmed_orders || 0}</div>
            </div>
            <div className="stat-card" style={{ borderLeftColor: 'var(--accent)' }}>
              <div className="stat-label">🚚 Dispatched</div>
              <div className="stat-value">{summary.dispatched_orders || 0}</div>
            </div>
            <div className="stat-card" style={{ borderLeftColor: '#065f46' }}>
              <div className="stat-label">📬 Delivered</div>
              <div className="stat-value">{summary.delivered_orders || 0}</div>
            </div>
            <div className="stat-card" style={{ borderLeftColor: 'var(--secondary)' }}>
              <div className="stat-label">💰 Revenue (delivered)</div>
              <div className="stat-value">{formatPrice(summary.total_revenue || 0)}</div>
            </div>
          </div>
        )}

        <div className="orders-controls" style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
          <input
            type="text"
            placeholder="Filter by order # or customer name..."
            className="search-input"
            onChange={e => {
              // client-side filter is handled via state if needed
            }}
            style={{
              flex: 1, maxWidth: '400px', padding: '0.55rem 1rem',
              border: '2px solid var(--gray-200)', borderRadius: 'var(--radius)',
              fontSize: '0.9rem'
            }}
          />
        </div>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Order #</th>
                <th>Customer</th>
                <th>Items</th>
                <th>Total</th>
                <th>Fulfillment</th>
                <th>Payment</th>
                <th>Status</th>
                <th>Actions</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {orders.length === 0 ? (
                <tr><td colSpan={9} className="text-center" style={{ color: 'var(--gray-400)', padding: '2rem' }}>No orders yet. Orders will appear here when customers buy via WhatsApp or web.</td></tr>
              ) : orders.map((o: any) => {
                const oid = o.order_id || o.id
                const status = (o.status || 'PENDING').toUpperCase()
                const fulfillIcon = o.fulfillment_method === 'pickup' ? '🏪' : '🚚'
                const payLabel = o.payment_method === 'mpesa' ? '💳 M-Pesa' : o.payment_method === 'cash_on_delivery' ? '💵 COD' : '—'
                const itemNames = (o.items || []).map((i: any) => i.title).join(', ')
                const isExpanded = expandedOrder === oid

                return (
                  <tr key={oid} style={{ background: status === 'PENDING' ? '#fffbeb' : undefined }}>
                    <td style={{ fontWeight: 600 }}>#{oid}</td>
                    <td>
                      <div style={{ fontWeight: 500 }}>{o.customer_name || '—'}</div>
                      {o.customer_phone && <div style={{ fontSize: '0.78rem', color: 'var(--gray-500)' }}>{o.customer_phone}</div>}
                    </td>
                    <td style={{ fontSize: '0.85rem', maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={itemNames}>
                      {itemNames || `${(o.items || []).length} item(s)`}
                    </td>
                    <td style={{ fontWeight: 600 }}>{formatPrice(o.total || 0)}</td>
                    <td style={{ fontSize: '0.85rem' }}>
                      <div>{fulfillIcon} {o.fulfillment_method === 'pickup' ? 'Pickup' : 'Delivery'}</div>
                      {o.delivery_area && <div style={{ color: 'var(--gray-500)', fontSize: '0.78rem' }}>{o.delivery_area}</div>}
                      {o.delivery_fee ? <div style={{ fontSize: '0.78rem', color: 'var(--gray-500)' }}>Fee: {formatPrice(o.delivery_fee)}</div> : null}
                    </td>
                    <td style={{ fontSize: '0.85rem' }}>
                      {payLabel}
                      <div style={{ fontSize: '0.7rem', color: 'var(--gray-500)' }}>{o.payment_status || 'pending'}</div>
                    </td>
                    <td>
                      <span className={`badge ${STATUS_COLORS[status] || 'badge-primary'}`}>
                        {STATUS_LABELS[status] || status}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '0.35rem', flexWrap: 'wrap' }}>
                        {(NEXT_ACTIONS[status] || []).map(action => (
                          <button
                            key={action.nextStatus}
                            onClick={() => updateStatus(oid, action.nextStatus)}
                            disabled={updating === oid}
                            className={`btn btn-sm ${action.color}`}
                            style={{ fontSize: '0.72rem', padding: '0.25rem 0.6rem' }}
                          >
                            {updating === oid ? '...' : action.label}
                          </button>
                        ))}
                        {status === 'PENDING' && (
                          <button
                            onClick={() => updateStatus(oid, 'CANCELLED')}
                            disabled={updating === oid}
                            className="btn btn-sm btn-danger"
                            style={{ fontSize: '0.72rem', padding: '0.25rem 0.6rem' }}
                          >
                            {updating === oid ? '...' : '❌ Cancel'}
                          </button>
                        )}
                      </div>
                    </td>
                    <td>
                      <button
                        onClick={() => toggleOrder(oid)}
                        className="btn btn-sm"
                        style={{ fontSize: '0.78rem' }}
                      >
                        {isExpanded ? '💬 Hide' : '💬 Chat'}
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>

        {expandedOrder && (() => {
          const currentOrder = orders.find(o => (o.order_id || o.id) === expandedOrder)
          return (
            <div className="auth-card" style={{ marginTop: '1.5rem', maxWidth: '700px' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '0.75rem' }}>
                💬 Messages for Order #{expandedOrder}
              </h3>
              {currentOrder?.seller_notes && (
                <div style={{
                  background: '#fef3c7', padding: '0.5rem 0.75rem', borderRadius: '8px',
                  marginBottom: '0.75rem', fontSize: '0.85rem'
                }}>
                  📝 <strong>Your note:</strong> {currentOrder.seller_notes}
                </div>
              )}
              <div style={{
                maxHeight: '400px', overflowY: 'auto',
                border: '1px solid var(--gray-200)', borderRadius: '8px',
                padding: '1rem', marginBottom: '1rem',
                background: 'var(--gray-50)'
              }}>
                {(!messages[expandedOrder] || messages[expandedOrder].length === 0) ? (
                  <p style={{ textAlign: 'center', color: 'var(--gray-400)', padding: '2rem 0' }}>
                    No messages for this order yet.
                  </p>
                ) : messages[expandedOrder].map(m => {
                  const isMine = user && m.sender_id === Number(user.id)
                  return (
                    <div key={m.id} style={{
                      display: 'flex',
                      justifyContent: isMine ? 'flex-end' : 'flex-start',
                      marginBottom: '0.75rem'
                    }}>
                      <div style={{
                        maxWidth: '75%',
                        padding: '0.6rem 1rem',
                        borderRadius: '12px',
                        background: isMine ? 'var(--primary)' : 'white',
                        color: isMine ? 'white' : 'var(--text)',
                        border: isMine ? 'none' : '1px solid var(--gray-200)',
                        fontSize: '0.9rem',
                      }}>
                        <div style={{ fontWeight: 600, fontSize: '0.75rem', marginBottom: '0.25rem', opacity: 0.7 }}>
                          {m.is_auto_reply ? '🤖 ' : ''}{m.sender_name}
                        </div>
                        <div style={{ whiteSpace: 'pre-wrap' }}>{m.content}</div>
                        <div style={{ fontSize: '0.7rem', opacity: 0.6, marginTop: '0.25rem', textAlign: 'right' }}>
                          {formatDate(m.created_at)}
                        </div>
                      </div>
                    </div>
                  )
                })}
                <div ref={chatEnd} />
              </div>

              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <input
                  value={newMessage}
                  onChange={e => setNewMessage(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleSend(expandedOrder)}
                  placeholder="Reply to buyer..."
                  style={{ flex: 1, padding: '0.6rem', borderRadius: '8px', border: '1px solid var(--gray-200)' }}
                />
                <button
                  onClick={() => handleSend(expandedOrder)}
                  disabled={sending || !newMessage.trim()}
                  className="btn btn-primary"
                  style={{ padding: '0.6rem 1.2rem' }}
                >
                  {sending ? '...' : 'Send'}
                </button>
              </div>
            </div>
          )
        })()}
      </main>
    </div>
  )
}
