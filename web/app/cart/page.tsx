'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Image from 'next/image'
import Link from 'next/link'
import { api, formatPrice, type CartItem } from '@/lib/api'
import { useAuth } from '@/lib/auth'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Minus, Plus, Trash2, ArrowRight, ShoppingBag, Tag } from 'lucide-react'
import { toast } from 'sonner'

export default function CartPage() {
  const router = useRouter()
  const { isLoggedIn } = useAuth()
  const [items, setItems] = useState<CartItem[]>([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [promoCode, setPromoCode] = useState('')

  const [fulfillmentMethod, setFulfillmentMethod] = useState('delivery')
  const [deliveryArea, setDeliveryArea] = useState('')
  const [paymentMethod, setPaymentMethod] = useState('mpesa')
  const [customerPhone, setCustomerPhone] = useState(() => {
    if (typeof window !== 'undefined') {
      try {
        const u = localStorage.getItem('ikobiz_user')
        if (u) {
          const parsed = JSON.parse(u)
          return parsed.phone || ''
        }
      } catch { /* ignore */ }
    }
    return ''
  })

  useEffect(() => {
    if (!isLoggedIn) return
    api.get('/cart', true).then((data: CartItem[]) => {
      setItems(data ?? [])
    }).catch((err: Error) => {
      toast.error(err.message || 'Failed to load cart')
    }).finally(() => setLoading(false))
  }, [isLoggedIn])

  const subtotal = items.reduce((sum, item) => sum + (item.product?.price ?? 0) * item.quantity, 0)
  const deliveryFee = subtotal > 100000 ? 0 : 500
  const total = subtotal + deliveryFee

  const updateQuantity = async (productId: number, newQty: number) => {
    if (newQty < 1) return
    try {
      await api.patch('/cart', { product_id: productId, quantity: newQty }, true)
      setItems(prev => prev.map(item =>
        item.product?.id === productId ? { ...item, quantity: newQty } : item
      ))
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Failed to update quantity')
    }
  }

  const removeItem = async (productId: number) => {
    try {
      await api.del(`/cart?product_id=${productId}`, true)
      setItems(prev => prev.filter(item => item.product?.id !== productId))
      toast.success('Item removed from cart')
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Failed to remove item')
    }
  }

  const handleCheckout = async () => {
    setSubmitting(true)
    try {
      const order = await api.post('/checkout', {
        fulfillment_method: fulfillmentMethod,
        delivery_area: fulfillmentMethod === 'delivery' ? deliveryArea : null,
        payment_method: paymentMethod,
        customer_phone: customerPhone || undefined,
      }, true) as { order_id: number }
      toast.success('Order placed successfully')
      router.push(`/orders/${order.order_id}`)
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Checkout failed')
    } finally {
      setSubmitting(false)
    }
  }

  if (!isLoggedIn) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] px-4 text-center">
        <div className="flex h-20 w-20 items-center justify-center rounded-full bg-muted mb-4">
          <ShoppingBag className="h-10 w-10 text-muted-foreground" />
        </div>
        <h2 className="text-xl font-semibold text-foreground mb-2">Shopping Cart</h2>
        <p className="text-muted-foreground max-w-sm mb-6">Please sign in to view your cart</p>
        <Link href="/login">
          <Button className="gap-2">Sign In</Button>
        </Link>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    )
  }

  if (items.length === 0) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-8 md:px-6">
        <h1 className="text-2xl font-bold text-foreground md:text-3xl mb-8">Shopping Cart</h1>
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="flex h-20 w-20 items-center justify-center rounded-full bg-muted mb-4">
            <ShoppingBag className="h-10 w-10 text-muted-foreground" />
          </div>
          <h2 className="text-xl font-semibold text-foreground mb-2">Your cart is empty</h2>
          <p className="text-muted-foreground max-w-sm mb-6">
            Looks like you haven&apos;t added anything yet. Start shopping to fill it up!
          </p>
          <Link href="/search">
            <Button className="gap-2">
              <ShoppingBag className="h-4 w-4" />
              Start Shopping
            </Button>
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 md:px-6">
      <h1 className="text-2xl font-bold text-foreground md:text-3xl mb-8">Shopping Cart</h1>

      <div className="grid gap-8 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-4">
          {items.map((item) => {
            const product = item.product
            if (!product) return null
            return (
              <div
                key={item.id}
                className="flex gap-4 rounded-2xl border border-border bg-card p-4"
              >
                <Link href={`/product/${product.id}`} className="flex-shrink-0">
                  <div className="relative h-24 w-24 overflow-hidden rounded-xl bg-muted">
                    <Image
                      src={product.image_url || '/placeholder.svg'}
                      alt={product.title}
                      fill
                      className="object-cover"
                    />
                  </div>
                </Link>

                <div className="flex flex-1 flex-col justify-between">
                  <div>
                    <Link
                      href={`/product/${product.id}`}
                      className="font-medium text-foreground hover:text-primary transition-colors line-clamp-2"
                    >
                      {product.title}
                    </Link>
                    {product.shop_name && (
                      <Link
                        href={`/shop/${product.shop_slug || product.shop_id}`}
                        className="text-sm text-muted-foreground hover:text-primary transition-colors block"
                      >
                        {product.shop_name}
                      </Link>
                    )}
                  </div>

                  <div className="flex items-center justify-between mt-3">
                    <div className="flex items-center rounded-lg border border-border">
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 rounded-r-none"
                        onClick={() => updateQuantity(product.id, item.quantity - 1)}
                        disabled={item.quantity <= 1}
                      >
                        <Minus className="h-3 w-3" />
                      </Button>
                      <span className="w-8 text-center text-sm font-medium">
                        {item.quantity}
                      </span>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 rounded-l-none"
                        onClick={() => updateQuantity(product.id, item.quantity + 1)}
                        disabled={item.quantity >= product.stock}
                      >
                        <Plus className="h-3 w-3" />
                      </Button>
                    </div>

                    <div className="flex items-center gap-4">
                      <span className="font-semibold text-primary">
                        {formatPrice(product.price * item.quantity)}
                      </span>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-muted-foreground hover:text-destructive"
                        onClick={() => removeItem(product.id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            )
          })}

          <Link href="/search">
            <Button variant="outline" className="gap-2">
              <ShoppingBag className="h-4 w-4" />
              Continue Shopping
            </Button>
          </Link>
        </div>

        <div className="lg:col-span-1">
          <div className="sticky top-24 rounded-2xl border border-border bg-card p-6 space-y-6">
            <h2 className="text-lg font-semibold text-foreground">Order Summary</h2>

            <div className="space-y-2">
              <label className="text-sm text-muted-foreground">Promo Code</label>
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <Tag className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    placeholder="Enter code"
                    className="pl-10"
                    value={promoCode}
                    onChange={(e) => setPromoCode(e.target.value)}
                  />
                </div>
                <Button variant="outline">Apply</Button>
              </div>
            </div>

            <div className="space-y-3 pt-4 border-t border-border">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Subtotal ({items.reduce((s, i) => s + i.quantity, 0)} items)</span>
                <span className="font-medium">{formatPrice(subtotal)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Delivery Fee</span>
                <span className="font-medium">
                  {deliveryFee === 0 ? (
                    <span className="text-green-600">Free</span>
                  ) : (
                    formatPrice(deliveryFee)
                  )}
                </span>
              </div>
              {subtotal < 100000 && (
                <p className="text-xs text-muted-foreground">
                  Add {formatPrice(100000 - subtotal)} more for free delivery
                </p>
              )}
              <div className="flex justify-between pt-3 border-t border-border">
                <span className="font-semibold text-foreground">Total</span>
                <span className="text-xl font-bold text-primary">
                  {formatPrice(total)}
                </span>
              </div>
            </div>

            <div className="space-y-4 pt-4 border-t border-border">
              <h3 className="text-sm font-semibold text-foreground">Delivery Details</h3>

              <div className="space-y-2">
                <label className="text-sm text-muted-foreground">Fulfillment Method</label>
                <div className="flex gap-3">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="fulfillment"
                      value="delivery"
                      checked={fulfillmentMethod === 'delivery'}
                      onChange={() => setFulfillmentMethod('delivery')}
                      className="text-primary"
                    />
                    <span className="text-sm">Delivery</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="fulfillment"
                      value="pickup"
                      checked={fulfillmentMethod === 'pickup'}
                      onChange={() => setFulfillmentMethod('pickup')}
                      className="text-primary"
                    />
                    <span className="text-sm">Pickup</span>
                  </label>
                </div>
              </div>

              {fulfillmentMethod === 'delivery' && (
                <div className="space-y-2">
                  <label className="text-sm text-muted-foreground">Delivery Area</label>
                  <Input
                    placeholder="e.g. Rongai near Quickmart"
                    value={deliveryArea}
                    onChange={(e) => setDeliveryArea(e.target.value)}
                  />
                </div>
              )}

              <div className="space-y-2">
                <label className="text-sm text-muted-foreground">Payment Method</label>
                <div className="flex gap-3 flex-wrap">
                  {[
                    { value: 'mpesa', label: 'M-Pesa' },
                    { value: 'card', label: 'Card' },
                    { value: 'cod', label: 'Cash on Delivery' },
                  ].map(({ value, label }) => (
                    <label key={value} className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="radio"
                        name="payment"
                        value={value}
                        checked={paymentMethod === value}
                        onChange={() => setPaymentMethod(value)}
                        className="text-primary"
                      />
                      <span className="text-sm">{label}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm text-muted-foreground">Phone Number</label>
                <Input
                  type="tel"
                  placeholder="+2547XXXXXXXX"
                  value={customerPhone}
                  onChange={(e) => setCustomerPhone(e.target.value)}
                />
              </div>
            </div>

            <Button
              className="w-full h-12 gap-2"
              onClick={handleCheckout}
              disabled={submitting}
            >
              {submitting ? 'Processing...' : 'Place Order'}
              <ArrowRight className="h-4 w-4" />
            </Button>

            <p className="text-xs text-center text-muted-foreground">
              We accept M-Pesa, Cards, and Cash on Delivery
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
