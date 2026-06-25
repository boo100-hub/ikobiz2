'use client'

import { useEffect, useState, use, useRef } from 'react'
import Link from 'next/link'
import { api, formatPrice, formatDate, type Message } from '@/lib/api'
import { useAuth } from '@/lib/auth'

const STATUS_STEPS = ['PENDING', 'CONFIRMED', 'PAID', 'DISPATCHED', 'SHIPPED', 'DELIVERED']
const STATUS_LABELS: Record<string, string> = {
  PENDING: '⏳ Order Placed',
  CONFIRMED: '✅ Seller Confirmed',
  PAID: '💰 Paid',
  DISPATCHED: '🚚 Dispatched',
  SHIPPED: '📦 Shipped',
  DELIVERED: '📬 Delivered',
  CANCELLED: '❌ Cancelled',
}

function getStatusIndex(status: string): number {
  const idx = STATUS_STEPS.indexOf(status.toUpperCase())
  return idx >= 0 ? idx : -1
}

export default function CheckoutPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const { isLoggedIn, user } = useAuth()
  const [orders, setOrders] = useState<any[]>([])
  const [currentOrder, setCurrentOrder] = useState<any | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [newMessage, setNewMessage] = useState('')
  const [sending, setSending] = useState(false)
  const [loading, setLoading] = useState(true)
  const chatEnd = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!isLoggedIn) { setLoading(false); return }
    api.get('/orders', true).then(data => {
      const list = Array.isArray(data) ? data : []
      setOrders(list)
      const found = list.find((o: any) => o.id === Number(id))
      setCurrentOrder(found || null)
    }).catch(() => {}).finally(() => setLoading(false))
  }, [isLoggedIn, id])

  useEffect(() => {
    if (id) {
      api.get(`/orders/${id}/messages`, true).then(data => {
        setMessages(Array.isArray(data) ? data : [])
      }).catch(() => {})
    }
  }, [id])

  useEffect(() => {
    chatEnd.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async () => {
    if (!newMessage.trim() || sending) return
    setSending(true)
    try {
      const msg = await api.post(`/orders/${id}/messages`, { content: newMessage.trim() }, true)
      setMessages(prev => [...prev, msg])
      setNewMessage('')
    } catch (e: any) {
      alert(e.message || 'Failed to send message')
    } finally {
      setSending(false)
    }
  }

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

  const status = currentOrder ? (currentOrder.status || 'PENDING').toUpperCase() : 'PENDING'
  const statusIdx = getStatusIndex(status)
  const isCancelled = status === 'CANCELLED'
  const itemNames = (currentOrder?.items || []).map((i: any) => i.title).join(', ')

  return (
    <div className="container section">
      {/* Order Header */}
      <div className="auth-card" style={{ margin: '0 auto 2rem' }}>
        <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
          {isCancelled ? (
            <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>❌</div>
          ) : statusIdx >= STATUS_STEPS.length - 1 ? (
            <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>📬</div>
          ) : (
            <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>📦</div>
          )}
          <h1>Order #{id}</h1>
          <p className="subtitle">
            {currentOrder?.created_at ? formatDate(currentOrder.created_at) : ''}
          </p>
        </div>

        {/* Status Timeline */}
        {!isCancelled ? (
          <div style={{
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            marginBottom: '1.5rem', position: 'relative', padding: '0 0.5rem'
          }}>
            {STATUS_STEPS.map((step, i) => {
              const isActive = i <= statusIdx
              const isCurrent = i === statusIdx
              return (
                <div key={step} style={{ textAlign: 'center', flex: 1, position: 'relative' }}>
                  <div style={{
                    width: '32px', height: '32px', borderRadius: '50%',
                    background: isActive ? 'var(--secondary)' : 'var(--gray-200)',
                    color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center',
                    margin: '0 auto 0.35rem', fontSize: '0.8rem', fontWeight: 700,
                    boxShadow: isCurrent ? '0 0 0 4px rgba(5,150,105,0.2)' : undefined,
                    transition: 'all 0.3s',
                  }}>
                    {isActive ? '✓' : i + 1}
                  </div>
                  <div style={{
                    fontSize: '0.7rem', fontWeight: isCurrent ? 700 : 500,
                    color: isActive ? 'var(--secondary)' : 'var(--gray-400)',
                    whiteSpace: 'nowrap',
                  }}>
                    {STATUS_LABELS[step].replace(/^.{1,2} /, '')}
                  </div>
                </div>
              )
            })}
          </div>
        ) : (
          <div style={{ textAlign: 'center', color: 'var(--danger)', fontWeight: 700, marginBottom: '1.5rem' }}>
            This order was cancelled.
          </div>
        )}

        {/* Order Summary */}
        {currentOrder && (
          <div style={{
            background: 'var(--gray-50)', borderRadius: 'var(--radius)', padding: '1rem',
            marginBottom: '1rem'
          }}>
            <h3 style={{ fontSize: '0.9rem', fontWeight: 700, marginBottom: '0.5rem' }}>Order Details</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', fontSize: '0.85rem' }}>
              <div style={{ color: 'var(--gray-500)' }}>Items:</div>
              <div style={{ fontWeight: 500 }}>{itemNames || `${(currentOrder.items || []).length} item(s)`}</div>
              <div style={{ color: 'var(--gray-500)' }}>Total:</div>
              <div style={{ fontWeight: 700, color: 'var(--primary)' }}>{formatPrice(currentOrder.total || 0)}</div>
              {currentOrder.fulfillment_method && (
                <>
                  <div style={{ color: 'var(--gray-500)' }}>Delivery:</div>
                  <div>
                    {currentOrder.fulfillment_method === 'pickup' ? '🏪 Pickup' : '🚚 Delivery'}
                    {currentOrder.delivery_area ? ` — ${currentOrder.delivery_area}` : ''}
                  </div>
                </>
              )}
              {currentOrder.delivery_fee ? (
                <>
                  <div style={{ color: 'var(--gray-500)' }}>Delivery fee:</div>
                  <div>{formatPrice(currentOrder.delivery_fee)}</div>
                </>
              ) : null}
              {currentOrder.payment_method && (
                <>
                  <div style={{ color: 'var(--gray-500)' }}>Payment:</div>
                  <div>
                    {currentOrder.payment_method === 'mpesa' ? '💳 M-Pesa' : '💵 Cash on delivery'}
                    <span style={{ fontSize: '0.75rem', color: 'var(--gray-400)', marginLeft: '0.3rem' }}>
                      ({currentOrder.payment_status || 'pending'})
                    </span>
                  </div>
                </>
              )}
              {currentOrder.seller_notes && (
                <>
                  <div style={{ color: 'var(--gray-500)' }}>Seller note:</div>
                  <div style={{ fontStyle: 'italic' }}>"{currentOrder.seller_notes}"</div>
                </>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Messages */}
      <div className="auth-card" style={{ margin: '2rem auto', maxWidth: '700px' }}>
        <h2 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem' }}>💬 Order Messages</h2>
        <div style={{
          maxHeight: '400px', overflowY: 'auto',
          border: '1px solid var(--gray-200)', borderRadius: '8px',
          padding: '1rem', marginBottom: '1rem',
          background: 'var(--gray-50)'
        }}>
          {messages.length === 0 ? (
            <p style={{ textAlign: 'center', color: 'var(--gray-400)', padding: '2rem 0' }}>
              No messages yet. The seller will be notified of your order.
            </p>
          ) : messages.map(m => {
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
            onKeyDown={e => e.key === 'Enter' && handleSend()}
            placeholder="Type your message..."
            style={{ flex: 1, padding: '0.6rem', borderRadius: '8px', border: '1px solid var(--gray-200)' }}
          />
          <button
            onClick={handleSend}
            disabled={sending || !newMessage.trim()}
            className="btn btn-primary"
            style={{ padding: '0.6rem 1.2rem' }}
          >
            {sending ? '...' : 'Send'}
          </button>
        </div>
      </div>

      {/* Order History */}
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
              {orders.map((o: any) => {
                const s = (o.status || 'PENDING').toUpperCase()
                const colorMap: Record<string, string> = {
                  PENDING: 'badge-primary',
                  CONFIRMED: 'badge-success',
                  DISPATCHED: 'badge-warning',
                  DELIVERED: 'badge-success',
                  CANCELLED: 'badge-danger',
                }
                return (
                  <tr key={o.id}>
                    <td><Link href={`/checkout/${o.id}`} style={{ fontWeight: 600 }}>#{o.id}</Link></td>
                    <td>{formatDate(o.created_at || '')}</td>
                    <td>{(o.items || []).length} item(s)</td>
                    <td style={{ fontWeight: 700 }}>{formatPrice(o.total || 0)}</td>
                    <td>
                      <span className={`badge ${colorMap[s] || 'badge-primary'}`}>
                        {STATUS_LABELS[s] || s}
                      </span>
                    </td>
                  </tr>
                )
              })}
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
