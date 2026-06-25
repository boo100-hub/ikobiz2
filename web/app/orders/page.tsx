'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { ShoppingBag, Package, ArrowRight } from 'lucide-react'
import { api, formatPrice, formatDate, type Order } from '@/lib/api'
import { useAuth } from '@/lib/auth'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'

const STATUS_STYLES: Record<string, string> = {
  PENDING: 'bg-amber-50 text-amber-700 border-amber-200 hover:bg-amber-100',
  CONFIRMED: 'bg-blue-50 text-blue-700 border-blue-200 hover:bg-blue-100',
  DISPATCHED: 'bg-purple-50 text-purple-700 border-purple-200 hover:bg-purple-100',
  DELIVERED: 'bg-green-50 text-green-700 border-green-200 hover:bg-green-100',
  CANCELLED: 'bg-red-50 text-red-700 border-red-200 hover:bg-red-100',
}

function totalItems(order: Order) {
  return order.items.reduce((sum, item) => sum + (item.quantity || 1), 0)
}

export default function OrdersPage() {
  const { isLoggedIn } = useAuth()
  const [orders, setOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!isLoggedIn) { setLoading(false); return }
    api.get('/orders', true)
      .then(data => setOrders(Array.isArray(data) ? data : []))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [isLoggedIn])

  if (!isLoggedIn) {
    return (
      <div className="container mx-auto px-4 py-12">
        <div className="mx-auto max-w-md text-center space-y-4">
          <div className="flex justify-center">
            <div className="rounded-full bg-primary/10 p-4">
              <ShoppingBag className="h-8 w-8 text-primary" />
            </div>
          </div>
          <h1 className="text-2xl font-bold">My Orders</h1>
          <p className="text-muted-foreground">Please log in to view your orders.</p>
          <Button asChild>
            <Link href="/auth/login">Login</Link>
          </Button>
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-12 space-y-4">
        <div className="flex items-center gap-3 mb-8">
          <Package className="h-6 w-6 text-primary" />
          <h1 className="text-2xl font-bold">My Orders</h1>
        </div>
        {[...Array(3)].map((_, i) => (
          <Skeleton key={i} className="h-24 w-full rounded-lg" />
        ))}
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-12">
      <div className="flex items-center gap-3 mb-8">
        <Package className="h-6 w-6 text-primary" />
        <h1 className="text-2xl font-bold">My Orders</h1>
      </div>

      {orders.length === 0 ? (
        <div className="mx-auto max-w-md text-center space-y-4">
          <div className="flex justify-center">
            <div className="rounded-full bg-muted p-4">
              <ShoppingBag className="h-8 w-8 text-muted-foreground" />
            </div>
          </div>
          <h2 className="text-xl font-semibold">No orders yet</h2>
          <p className="text-muted-foreground">Start shopping and your orders will appear here.</p>
          <Button asChild>
            <Link href="/search">
              Browse Products <ArrowRight className="ml-1 h-4 w-4" />
            </Link>
          </Button>
        </div>
      ) : (
        <>
          <div className="hidden md:block rounded-lg border bg-card">
            <table className="w-full">
              <thead>
                <tr className="border-b bg-muted/50">
                  <th className="p-4 text-left text-sm font-medium">Order #</th>
                  <th className="p-4 text-left text-sm font-medium">Date</th>
                  <th className="p-4 text-left text-sm font-medium">Items</th>
                  <th className="p-4 text-left text-sm font-medium">Total</th>
                  <th className="p-4 text-left text-sm font-medium">Status</th>
                  <th className="p-4 text-right text-sm font-medium"></th>
                </tr>
              </thead>
              <tbody>
                {orders.map(order => (
                  <tr key={order.id} className="border-b last:border-0 transition-colors hover:bg-muted/30">
                    <td className="p-4 font-medium">
                      <Link href={`/orders/${order.id}`} className="transition-colors hover:text-primary">
                        #{order.id}
                      </Link>
                    </td>
                    <td className="p-4 text-sm text-muted-foreground">
                      {formatDate(order.created_at || '')}
                    </td>
                    <td className="p-4 text-sm">{totalItems(order)} item{totalItems(order) !== 1 ? 's' : ''}</td>
                    <td className="p-4 font-semibold">{formatPrice(order.total)}</td>
                    <td className="p-4">
                      <Badge variant="outline" className={STATUS_STYLES[order.status] || ''}>
                        {order.status}
                      </Badge>
                    </td>
                    <td className="p-4 text-right">
                      <Button variant="ghost" size="sm" asChild>
                        <Link href={`/orders/${order.id}`}>
                          View <ArrowRight className="ml-1 h-3 w-3" />
                        </Link>
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="space-y-3 md:hidden">
            {orders.map(order => (
              <Link key={order.id} href={`/orders/${order.id}`}>
                <div className="rounded-lg border bg-card p-4 transition-shadow hover:shadow-md space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold">#{order.id}</span>
                    <Badge variant="outline" className={STATUS_STYLES[order.status] || ''}>
                      {order.status}
                    </Badge>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">{formatDate(order.created_at || '')}</span>
                    <span className="text-muted-foreground">{totalItems(order)} item{totalItems(order) !== 1 ? 's' : ''}</span>
                  </div>
                  <div className="flex items-center justify-between border-t pt-1">
                    <span className="font-bold text-primary">{formatPrice(order.total)}</span>
                    <span className="flex items-center gap-1 text-sm text-muted-foreground">
                      View details <ArrowRight className="h-3 w-3" />
                    </span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
