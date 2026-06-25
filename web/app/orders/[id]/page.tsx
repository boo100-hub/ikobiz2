'use client'

import { useEffect, useState, useRef } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { api, formatPrice, formatDate, type Order, type Message } from '@/lib/api'
import { useAuth } from '@/lib/auth'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Package,
  Truck,
  CheckCircle,
  Clock,
  XCircle,
  MessageCircle,
  Send,
  Phone,
  MapPin,
  CreditCard,
  ArrowLeft,
} from 'lucide-react'
import { toast } from 'sonner'

const STATUS_STEPS = ['PENDING', 'CONFIRMED', 'PAID', 'DISPATCHED', 'SHIPPED', 'DELIVERED']

const STATUS_ICONS: Record<string, typeof Clock> = {
  PENDING: Clock,
  CONFIRMED: CheckCircle,
  PAID: CreditCard,
  DISPATCHED: Truck,
  SHIPPED: Package,
  DELIVERED: Package,
  CANCELLED: XCircle,
}

const STATUS_COLORS: Record<string, string> = {
  PENDING: 'text-yellow-500 border-yellow-500',
  CONFIRMED: 'text-blue-500 border-blue-500',
  PAID: 'text-green-500 border-green-500',
  DISPATCHED: 'text-orange-500 border-orange-500',
  SHIPPED: 'text-purple-500 border-purple-500',
  DELIVERED: 'text-green-500 border-green-500',
  CANCELLED: 'text-red-500 border-red-500',
}

const BADGE_VARIANTS: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  PENDING: 'secondary',
  CONFIRMED: 'default',
  PAID: 'default',
  DISPATCHED: 'outline',
  SHIPPED: 'outline',
  DELIVERED: 'default',
  CANCELLED: 'destructive',
}

function getStatusIndex(status: string): number {
  const idx = STATUS_STEPS.indexOf(status.toUpperCase())
  return idx >= 0 ? idx : -1
}

function TimelineCircle({
  step,
  index,
  statusIndex,
}: {
  step: string
  index: number
  statusIndex: number
}) {
  const isActive = index <= statusIndex
  const isCurrent = index === statusIndex
  const Icon = STATUS_ICONS[step] || Clock

  return (
    <div className="flex flex-col items-center">
      <div
        className={`relative flex h-10 w-10 items-center justify-center rounded-full border-2 transition-all duration-300 ${
          isActive ? 'bg-primary border-primary text-primary-foreground' : 'bg-muted border-muted-foreground/30 text-muted-foreground'
        } ${isCurrent ? 'ring-4 ring-primary/20' : ''}`}
      >
        <Icon className="h-5 w-5" />
      </div>
      <span
        className={`mt-2 text-xs font-medium capitalize ${
          isActive ? 'text-primary' : 'text-muted-foreground'
        }`}
      >
        {step.toLowerCase()}
      </span>
    </div>
  )
}

export default function OrderPage() {
  const params = useParams()
  const router = useRouter()
  const id = params.id as string
  const { isLoggedIn, user } = useAuth()
  const [order, setOrder] = useState<Order | null>(null)
  const [loading, setLoading] = useState(true)
  const [cancelling, setCancelling] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])
  const [newMessage, setNewMessage] = useState('')
  const [sending, setSending] = useState(false)
  const chatEnd = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!id) return
    if (!isLoggedIn) {
      setLoading(false)
      return
    }
    api
      .get('/orders/' + id, true)
      .then((data) => {
        setOrder(data as Order)
      })
      .catch(() => {
        setOrder(null)
      })
      .finally(() => setLoading(false))
  }, [id, isLoggedIn])

  useEffect(() => {
    if (!id) return
    api
      .get('/orders/' + id + '/messages', true)
      .then((data) => {
        setMessages(Array.isArray(data) ? data : [])
      })
      .catch(() => {})
  }, [id])

  useEffect(() => {
    chatEnd.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleCancel = async () => {
    if (!confirm('Are you sure you want to cancel this order?')) return
    setCancelling(true)
    try {
      await api.post('/orders/' + id + '/cancel', {}, true)
      toast.success('Order cancelled successfully')
      setOrder((prev) => (prev ? { ...prev, status: 'CANCELLED' } : prev))
    } catch (e: any) {
      toast.error(e.message || 'Failed to cancel order')
    } finally {
      setCancelling(false)
    }
  }

  const handleSend = async () => {
    if (!newMessage.trim() || sending) return
    setSending(true)
    try {
      const msg = await api.post(
        '/orders/' + id + '/messages',
        { content: newMessage.trim() },
        true,
      )
      setMessages((prev) => [...prev, msg])
      setNewMessage('')
    } catch (e: any) {
      toast.error(e.message || 'Failed to send message')
    } finally {
      setSending(false)
    }
  }

  if (!isLoggedIn) {
    return (
      <div className="container mx-auto flex min-h-[60vh] items-center justify-center px-4 py-8">
        <Card className="w-full max-w-md text-center">
          <CardContent className="pt-6">
            <p className="text-muted-foreground mb-4">Please log in to view your orders.</p>
            <Button asChild className="w-full">
              <Link href="/auth/login">Login</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="container mx-auto space-y-6 px-4 py-8">
        <Skeleton className="h-8 w-48" />
        <Card>
          <CardContent className="space-y-4 pt-6">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-4 w-1/2" />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="space-y-4 pt-6">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-4 w-1/2" />
          </CardContent>
        </Card>
      </div>
    )
  }

  if (!order) {
    return (
      <div className="container mx-auto flex min-h-[60vh] items-center justify-center px-4 py-8">
        <Card className="w-full max-w-md text-center">
          <CardContent className="pt-6">
            <XCircle className="mx-auto mb-4 h-12 w-12 text-destructive" />
            <CardTitle className="mb-2">Order not found</CardTitle>
            <p className="text-muted-foreground mb-4">
              The order you are looking for does not exist or has been removed.
            </p>
            <Button asChild variant="outline">
              <Link href="/">
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back to Home
              </Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  const status = (order.status || 'PENDING').toUpperCase()
  const statusIdx = getStatusIndex(status)
  const isCancelled = status === 'CANCELLED'
  const canCancel = !isCancelled && statusIdx < 2
  const sellerPhone = order.customer_phone || ''

  return (
    <div className="container mx-auto max-w-4xl space-y-6 px-4 py-8">
      {/* Back Button */}
      <Button variant="ghost" asChild className="-ml-2">
        <Link href="/orders">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Orders
        </Link>
      </Button>

      {/* Order Header */}
      <Card>
        <CardHeader className="flex-row items-start justify-between gap-4">
          <div>
            <CardTitle className="flex items-center gap-3 text-2xl">
              Order #{order.id}
              <Badge variant={BADGE_VARIANTS[status] || 'secondary'}>
                {status}
              </Badge>
            </CardTitle>
            <CardDescription>
              {order.created_at ? formatDate(order.created_at) : ''}
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Status Timeline */}
          {!isCancelled ? (
            <div className="relative">
              <div className="flex items-center justify-between">
                {STATUS_STEPS.map((step, index) => (
                  <div key={step} className="flex flex-1 flex-col items-center">
                    <TimelineCircle step={step} index={index} statusIndex={statusIdx} />
                    {index < STATUS_STEPS.length - 1 && (
                      <div className="mt-2 h-0.5 w-full bg-muted-foreground/20" />
                    )}
                  </div>
                ))}
              </div>
              <div className="relative -top-2 flex justify-between px-5">
                {STATUS_STEPS.slice(0, -1).map((_, index) => (
                  <div
                    key={index}
                    className={`h-0.5 flex-1 transition-colors duration-300 ${
                      index < statusIdx ? 'bg-primary' : 'bg-muted-foreground/20'
                    }`}
                    style={{ marginRight: index < STATUS_STEPS.length - 2 ? '0' : '0' }}
                  />
                ))}
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center gap-2 py-4 text-destructive">
              <XCircle className="h-6 w-6" />
              <span className="font-semibold">This order was cancelled</span>
            </div>
          )}

          <Separator />

          {/* Order Items */}
          <div className="space-y-3">
            <h3 className="font-semibold">Items ({order.items.length})</h3>
            {order.items.map((item) => (
              <div
                key={item.id}
                className="flex items-center gap-4 rounded-lg border p-3"
              >
                <div className="h-16 w-16 flex-shrink-0 overflow-hidden rounded-md bg-muted">
                  {item.image_url ? (
                    <img
                      src={item.image_url}
                      alt={item.title}
                      className="h-full w-full object-cover"
                    />
                  ) : (
                    <div className="flex h-full w-full items-center justify-center text-muted-foreground">
                      <Package className="h-6 w-6" />
                    </div>
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium truncate">{item.title}</p>
                  <p className="text-sm text-muted-foreground">
                    Qty: {item.quantity} &times; {formatPrice(item.price)}
                  </p>
                </div>
                <div className="text-right font-semibold">
                  {formatPrice(item.price * item.quantity)}
                </div>
              </div>
            ))}
          </div>

          <Separator />

          {/* Delivery & Payment Info */}
          <div className="grid gap-6 sm:grid-cols-2">
            {order.fulfillment_method && (
              <div className="space-y-2">
                <h4 className="flex items-center gap-2 text-sm font-semibold text-muted-foreground">
                  <MapPin className="h-4 w-4" />
                  Delivery
                </h4>
                <div className="rounded-lg border p-3 text-sm">
                  <p>
                    <span className="font-medium">Method:</span>{' '}
                    {order.fulfillment_method === 'pickup' ? 'Pickup' : 'Delivery'}
                  </p>
                  {order.delivery_area && (
                    <p>
                      <span className="font-medium">Area:</span> {order.delivery_area}
                    </p>
                  )}
                  {order.delivery_address && (
                    <p>
                      <span className="font-medium">Address:</span> {order.delivery_address}
                    </p>
                  )}
                  {order.delivery_fee !== undefined && order.delivery_fee > 0 && (
                    <p>
                      <span className="font-medium">Fee:</span>{' '}
                      {formatPrice(order.delivery_fee)}
                    </p>
                  )}
                </div>
              </div>
            )}
            <div className="space-y-2">
              <h4 className="flex items-center gap-2 text-sm font-semibold text-muted-foreground">
                <CreditCard className="h-4 w-4" />
                Payment
              </h4>
              <div className="rounded-lg border p-3 text-sm">
                <p>
                  <span className="font-medium">Method:</span>{' '}
                  {order.payment_method || 'N/A'}
                </p>
                <p>
                  <span className="font-medium">Status:</span>{' '}
                  <Badge
                    variant={
                      order.payment_status === 'paid' ? 'default' : 'secondary'
                    }
                    className="ml-1"
                  >
                    {order.payment_status || 'pending'}
                  </Badge>
                </p>
              </div>
            </div>
          </div>

          <Separator />

          {/* Total Summary */}
          <div className="space-y-1 text-right">
            {order.delivery_fee !== undefined && order.delivery_fee > 0 && (
              <p className="text-sm text-muted-foreground">
                Delivery fee: {formatPrice(order.delivery_fee)}
              </p>
            )}
            <p className="text-lg font-bold">
              Total: {formatPrice(order.total || 0)}
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap gap-3">
            {canCancel && (
              <Button
                variant="destructive"
                onClick={handleCancel}
                disabled={cancelling}
              >
                <XCircle className="mr-2 h-4 w-4" />
                {cancelling ? 'Cancelling...' : 'Cancel Order'}
              </Button>
            )}
            {sellerPhone && (
              <Button variant="outline" asChild>
                <a
                  href={`https://wa.me/${sellerPhone.replace(/^0/, '254')}?text=Hi%2C%20I%27m%20inquiring%20about%20Order%20%23${order.id}`}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <Phone className="mr-2 h-4 w-4" />
                  Contact Seller on WhatsApp
                </a>
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Chat Panel */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <MessageCircle className="h-5 w-5" />
            Order Messages
          </CardTitle>
          <CardDescription>
            Chat with the seller about your order
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="mb-4 max-h-[400px] overflow-y-auto space-y-3 rounded-lg border bg-muted/30 p-4">
            {messages.length === 0 ? (
              <p className="py-8 text-center text-sm text-muted-foreground">
                No messages yet. The seller will be notified of your order.
              </p>
            ) : (
              messages.map((m) => {
                const isMine = user && m.sender_id === Number(user.id)
                return (
                  <div
                    key={m.id}
                    className={`flex ${isMine ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[75%] rounded-2xl px-4 py-2.5 text-sm ${
                        isMine
                          ? 'bg-primary text-primary-foreground'
                          : 'bg-card border text-card-foreground'
                      }`}
                    >
                      <p className="text-xs font-semibold opacity-70">
                        {m.is_auto_reply ? '🤖 ' : ''}{m.sender_name}
                      </p>
                      <p className="mt-0.5 whitespace-pre-wrap">{m.content}</p>
                      <p className="mt-1 text-right text-xs opacity-50">
                        {formatDate(m.created_at)}
                      </p>
                    </div>
                  </div>
                )
              })
            )}
            <div ref={chatEnd} />
          </div>
          <form
            onSubmit={(e) => {
              e.preventDefault()
              handleSend()
            }}
            className="flex gap-2"
          >
            <Input
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              placeholder="Type your message..."
              disabled={sending}
            />
            <Button
              type="submit"
              size="icon"
              disabled={sending || !newMessage.trim()}
            >
              {sending ? (
                <span className="animate-spin">...</span>
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
