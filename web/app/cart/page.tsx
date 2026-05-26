'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { api, formatPrice, type CartItem } from '@/lib/api'
import { useAuth } from '@/lib/auth'

function getItemPrice(item: CartItem): number {
  if (item.product) return item.product.price
  if (item.listing?.buy_now_price) return item.listing.buy_now_price
  if (item.listing) return item.listing.starting_price
  return 0
}

function getItemTitle(item: CartItem): string {
  if (item.product) return item.product.title
  if (item.listing) return item.listing.title
  return `Item #${item.id}`
}

function getItemImage(item: CartItem): string {
  if (item.product?.image_url) return item.product.image_url
  if (item.listing?.image_url) return item.listing.image_url
  return '/placeholder.svg'
}

function getItemType(item: CartItem): 'shop' | 'ikobiz' {
  if (item.type === 'secondary_market' || item.listing) return 'ikobiz'
  return 'shop'
}

export default function CartPage() {
  const router = useRouter()
  const { isLoggedIn } = useAuth()
  const [items, setItems] = useState<CartItem[]>([])
  const [loading, setLoading] = useState(true)
  const [checkingOut, setCheckingOut] = useState(false)

  useEffect(() => {
    if (!isLoggedIn) { setLoading(false); return }
    api.get('/cart', true).then(data => {
      setItems(Array.isArray(data) ? data : [])
    }).catch(() => {}).finally(() => setLoading(false))
  }, [isLoggedIn])

  const total = items.reduce((s, i) => s + getItemPrice(i) * i.quantity, 0)

  const removeItem = async (itemId: number) => {
    try {
      await api.del(`/cart/${itemId}`, true)
      setItems(prev => prev.filter(i => i.id !== itemId))
    } catch { alert('Failed to remove item') }
  }

  const checkout = async () => {
    setCheckingOut(true)
    try {
      const order = await api.post('/checkout', {}, true)
      router.push('/checkout/' + ((order as any).order_id || Date.now()))
    } catch { alert('Checkout failed. Please try again.') }
    setCheckingOut(false)
  }

  if (!isLoggedIn) return (
    <div className="container section">
      <div className="auth-card" style={{ margin: '2rem auto' }}>
        <h1>Cart</h1>
        <p className="subtitle">Please log in to view your cart.</p>
        <Link href="/auth/login" className="btn btn-primary" style={{ width: '100%', justifyContent: 'center' }}>Login</Link>
      </div>
    </div>
  )

  if (loading) return <div className="loading" />

  return (
    <div className="container section">
      <h1 style={{ fontSize: '1.5rem', fontWeight: 800, marginBottom: '1.5rem' }}>Shopping Cart</h1>

      {items.length === 0 ? (
        <div className="auth-card" style={{ margin: '0 auto' }}>
          <p className="text-center" style={{ color: 'var(--gray-400)', marginBottom: '1rem' }}>Your cart is empty.</p>
          <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'center' }}>
            <Link href="/" className="btn btn-outline">Browse Shops</Link>
            <Link href="/market" className="btn btn-primary">Secondary Market</Link>
          </div>
        </div>
      ) : (
        <>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Item</th>
                  <th>Type</th>
                  <th>Price</th>
                  <th>Total</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {items.map(item => {
                  const itemPrice = getItemPrice(item)
                  return (
                    <tr key={item.id}>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                          <img src={getItemImage(item)} alt="" style={{ width: 48, height: 48, borderRadius: 'var(--radius)', objectFit: 'cover', background: 'var(--gray-100)' }}
                            onError={e => { (e.target as HTMLImageElement).src = '/placeholder.svg' }} />
                          <div>
                            <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{getItemTitle(item)}</div>
                          </div>
                        </div>
                      </td>
                      <td><span className={`badge ${getItemType(item) === 'ikobiz' ? 'badge-primary' : 'badge-success'}`}>{getItemType(item)}</span></td>
                      <td style={{ fontWeight: 600 }}>{formatPrice(itemPrice)}</td>
                      <td style={{ textAlign: 'center', fontWeight: 600 }}>{item.quantity}</td>
                      <td style={{ fontWeight: 700, color: 'var(--primary)' }}>{formatPrice(itemPrice * item.quantity)}</td>
                      <td><button className="btn btn-sm btn-danger" onClick={() => removeItem(item.id)}>Remove</button></td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
            <div>
              <span style={{ fontSize: '1.1rem', color: 'var(--gray-500)' }}>Total: </span>
              <span style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--primary)' }}>{formatPrice(total)}</span>
            </div>
            <button className="btn btn-primary btn-lg" onClick={checkout} disabled={checkingOut}>
              {checkingOut ? 'Processing...' : 'Proceed to Checkout'}
            </button>
          </div>
        </>
      )}
    </div>
  )
}
