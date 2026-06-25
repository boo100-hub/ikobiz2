'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { api, formatPrice, formatDate } from '@/lib/api'
import { useAuth } from '@/lib/auth'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  DollarSign,
  ShoppingCart,
  Clock,
  CheckCircle,
  TrendingUp,
  ArrowRight,
  Package,
} from 'lucide-react'

type Summary = {
  shops: number
  products: number
  orders_total: number
  orders_pending: number
  orders_confirmed: number
  orders_dispatched: number
  orders_delivered: number
  revenue_total: number
}

type Order = {
  id: number
  order_id?: number
  customer_name?: string
  customer_phone?: string
  total: number
  status: string
  created_at?: string
  items?: { title: string; quantity: number }[]
}

const STATUS_STYLES: Record<string, string> = {
  PENDING: 'border-amber-200 bg-amber-50 text-amber-700',
  CONFIRMED: 'border-blue-200 bg-blue-50 text-blue-700',
  DISPATCHED: 'border-purple-200 bg-purple-50 text-purple-700',
  DELIVERED: 'border-green-200 bg-green-50 text-green-700',
  CANCELLED: 'border-red-200 bg-red-50 text-red-700',
}

export default function SellerDashboardPage() {
  const { user, isLoggedIn, isSeller } = useAuth()
  const [summary, setSummary] = useState<Summary | null>(null)
  const [orders, setOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!isLoggedIn || !isSeller) {
      setLoading(false)
      return
    }
    Promise.all([
      api.get('/dashboard/summary', true).catch(() => null),
      api.get('/seller/shop-orders', true).catch(() => []),
    ]).then(([s, o]) => {
      setSummary(s)
      const allOrders = Array.isArray(o) ? o : []
      allOrders.sort(
        (a: Order, b: Order) =>
          new Date(b.created_at || '').getTime() -
          new Date(a.created_at || '').getTime()
      )
      setOrders(allOrders)
    }).finally(() => setLoading(false))
  }, [isLoggedIn, isSeller])

  if (loading) {
    return (
      <div className="space-y-6 p-6">
        <div className="h-8 w-48 animate-pulse rounded bg-gray-200" />
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-28 animate-pulse rounded-xl bg-gray-100" />
          ))}
        </div>
        <div className="h-64 animate-pulse rounded-xl bg-gray-100" />
        <div className="h-40 animate-pulse rounded-xl bg-gray-100" />
      </div>
    )
  }

  if (!isLoggedIn || !isSeller) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold">Access Denied</h1>
          <p className="mt-2 text-gray-500">Please log in as a seller.</p>
          <Link href="/auth/login">
            <Button className="mt-4">Login</Button>
          </Link>
        </div>
      </div>
    )
  }

  const recentOrders = orders.slice(0, 5)

  const statCards = [
    {
      label: 'Total Revenue',
      value: formatPrice(summary?.revenue_total ?? 0),
      icon: DollarSign,
      color: 'text-green-600',
      bg: 'bg-green-50',
    },
    {
      label: 'Total Orders',
      value: summary?.orders_total ?? 0,
      icon: ShoppingCart,
      color: 'text-blue-600',
      bg: 'bg-blue-50',
    },
    {
      label: 'Pending Orders',
      value: summary?.orders_pending ?? 0,
      icon: Clock,
      color: 'text-amber-600',
      bg: 'bg-amber-50',
    },
    {
      label: 'Delivered',
      value: summary?.orders_delivered ?? 0,
      icon: CheckCircle,
      color: 'text-emerald-600',
      bg: 'bg-emerald-50',
    },
  ]

  return (
    <div className="space-y-8 p-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">
          Welcome back, {user?.username}
        </h1>
        <p className="mt-1 text-gray-500">
          Here&apos;s what&apos;s happening with your shop today.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {statCards.map((card) => {
          const Icon = card.icon
          return (
            <div
              key={card.label}
              className="flex items-center gap-4 rounded-xl border p-5 shadow-sm"
            >
              <div className={`rounded-lg p-3 ${card.bg}`}>
                <Icon className={`h-6 w-6 ${card.color}`} />
              </div>
              <div>
                <p className="text-sm text-gray-500">{card.label}</p>
                <p className="text-2xl font-bold">{card.value}</p>
              </div>
            </div>
          )
        })}
      </div>

      {summary && (
        <div className="flex items-center gap-2 rounded-lg border bg-gray-50 px-4 py-3 text-sm text-gray-600">
          <TrendingUp className="h-4 w-4 text-gray-400" />
          <span>
            <strong>{summary.products}</strong> products across{' '}
            <strong>{summary.shops}</strong> shop{summary.shops !== 1 ? 's' : ''}
          </span>
        </div>
      )}

      <div className="rounded-xl border shadow-sm">
        <div className="flex items-center justify-between border-b px-5 py-4">
          <h2 className="text-lg font-semibold">Recent Orders</h2>
          <Link href="/seller/orders">
            <Button variant="ghost" size="sm" className="gap-1 text-sm">
              View All <ArrowRight className="h-3.5 w-3.5" />
            </Button>
          </Link>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-gray-50 text-left text-xs font-medium uppercase text-gray-500">
                <th className="px-5 py-3">Order #</th>
                <th className="px-5 py-3">Customer</th>
                <th className="px-5 py-3">Items</th>
                <th className="px-5 py-3">Total</th>
                <th className="px-5 py-3">Status</th>
                <th className="px-5 py-3">Date</th>
              </tr>
            </thead>
            <tbody>
              {recentOrders.length === 0 ? (
                <tr>
                  <td
                    colSpan={6}
                    className="px-5 py-10 text-center text-gray-400"
                  >
                    No orders yet. Orders will appear here when customers buy.
                  </td>
                </tr>
              ) : (
                recentOrders.map((o) => {
                  const oid = o.order_id || o.id
                  const status = (o.status || 'PENDING').toUpperCase()
                  const itemCount = Array.isArray(o.items)
                    ? o.items.reduce((sum, i) => sum + (i.quantity || 1), 0)
                    : 0
                  return (
                    <tr key={oid} className="border-b last:border-b-0">
                      <td className="px-5 py-3 font-medium">#{oid}</td>
                      <td className="px-5 py-3">
                        <div className="font-medium">
                          {o.customer_name || 'Guest'}
                        </div>
                        {o.customer_phone && (
                          <div className="text-xs text-gray-400">
                            {o.customer_phone}
                          </div>
                        )}
                      </td>
                      <td className="px-5 py-3">{itemCount}</td>
                      <td className="px-5 py-3 font-medium">
                        {formatPrice(o.total || 0)}
                      </td>
                      <td className="px-5 py-3">
                        <Badge
                          variant="outline"
                          className={`border px-2 py-0.5 text-xs font-medium ${
                            STATUS_STYLES[status] ||
                            'border-gray-200 bg-gray-50 text-gray-700'
                          }`}
                        >
                          {status}
                        </Badge>
                      </td>
                      <td className="px-5 py-3 text-gray-500">
                        {formatDate(o.created_at || '')}
                      </td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="rounded-xl border shadow-sm">
        <div className="border-b px-5 py-4">
          <h2 className="text-lg font-semibold">Top Products</h2>
        </div>
        <div className="px-5 py-8 text-center text-gray-400">
          <Package className="mx-auto h-8 w-8 text-gray-300" />
          <p className="mt-2 text-sm">
            Product performance data will appear here once you have orders.
          </p>
        </div>
      </div>

      <div className="rounded-xl border shadow-sm">
        <div className="border-b px-5 py-4">
          <h2 className="text-lg font-semibold">Quick Actions</h2>
        </div>
        <div className="flex flex-wrap gap-3 px-5 py-4">
          <Link href="/dashboard/inventory">
            <Button variant="default" size="sm" className="gap-2">
              <Package className="h-4 w-4" /> Add New Product
            </Button>
          </Link>
          <Link href="/seller/orders">
            <Button variant="secondary" size="sm" className="gap-2">
              <ShoppingCart className="h-4 w-4" /> View All Orders
            </Button>
          </Link>
          <Link href="/dashboard/shop-settings">
            <Button variant="outline" size="sm" className="gap-2">
              Edit Shop Settings
            </Button>
          </Link>
        </div>
      </div>
    </div>
  )
}
