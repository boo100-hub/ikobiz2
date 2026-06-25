"use client"

import { useState, useEffect } from "react"
import { useParams, useRouter } from "next/navigation"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Card } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { Skeleton } from "@/components/ui/skeleton"
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
  Store,
  ShoppingBag,
} from "lucide-react"
import { toast } from "sonner"
import { api, formatPrice, formatDate, type Order, type Message } from "@/lib/api"

const statusColors: Record<string, string> = {
  PENDING: "bg-amber-100 text-amber-700",
  CONFIRMED: "bg-blue-100 text-blue-700",
  DISPATCHED: "bg-purple-100 text-purple-700",
  DELIVERED: "bg-green-100 text-green-700",
  CANCELLED: "bg-red-100 text-red-700",
}

const statusIcons: Record<string, typeof Clock> = {
  PENDING: Clock,
  CONFIRMED: CheckCircle,
  DISPATCHED: Truck,
  DELIVERED: Package,
}

const statusFlow = ["PENDING", "CONFIRMED", "DISPATCHED", "DELIVERED"]

const nextStatus: Record<string, string> = {
  PENDING: "CONFIRMED",
  CONFIRMED: "DISPATCHED",
  DISPATCHED: "DELIVERED",
}

export default function SellerOrderDetailPage() {
  const params = useParams()
  const router = useRouter()
  const id = params.id as string
  const [order, setOrder] = useState<Order | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [newMessage, setNewMessage] = useState("")
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const [updating, setUpdating] = useState(false)

  useEffect(() => {
    if (!id) return
    setLoading(true)
    Promise.all([
      api.get('/orders/' + id, true),
      api.get('/orders/' + id + '/messages', true),
    ]).then(([orderData, messagesData]) => {
      setOrder(orderData)
      setMessages(messagesData)
    }).catch(() => {
      toast.error("Failed to load order")
    }).finally(() => setLoading(false))
  }, [id])

  const handleStatusUpdate = async (status: string) => {
    setUpdating(true)
    try {
      await api.patch('/orders/' + id + '/status', { status }, true)
      setOrder(prev => prev ? { ...prev, status } : null)
      toast.success(`Order ${status.toLowerCase()}`)
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Failed to update status")
    } finally {
      setUpdating(false)
    }
  }

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newMessage.trim()) return
    setSending(true)
    try {
      const msg = await api.post('/orders/' + id + '/messages', { content: newMessage.trim() }, true)
      setMessages(prev => [...prev, msg])
      setNewMessage("")
    } catch {
      toast.error("Failed to send message")
    } finally {
      setSending(false)
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-40 w-full" />
        <Skeleton className="h-60 w-full" />
      </div>
    )
  }

  if (!order) {
    return (
      <div className="text-center py-16">
        <h2 className="text-xl font-semibold text-foreground">Order not found</h2>
        <Link href="/seller/orders">
          <Button variant="outline" className="mt-4">Back to Orders</Button>
        </Link>
      </div>
    )
  }

  const currentIndex = statusFlow.indexOf(order.status)
  const canCancel = ["PENDING", "CONFIRMED"].includes(order.status)
  const next = nextStatus[order.status]

  return (
    <div className="space-y-6">
      {/* Back + Title */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => router.back()}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold text-foreground">Order #{order.id}</h1>
          <p className="text-sm text-muted-foreground">{formatDate(order.created_at || "")}</p>
        </div>
        <Badge className={statusColors[order.status] || ""}>{order.status}</Badge>
      </div>

      {/* Status Timeline */}
      <Card className="p-6">
        <h2 className="font-semibold text-foreground mb-4">Order Status</h2>
        <div className="flex items-center gap-2">
          {statusFlow.map((s, i) => {
            const Icon = statusIcons[s] || Clock
            const isActive = i <= currentIndex
            const isLast = i === statusFlow.length - 1
            return (
              <div key={s} className="flex items-center gap-2 flex-1">
                <div className={`flex flex-col items-center ${isLast ? "" : "flex-1"}`}>
                  <div className={`flex h-10 w-10 items-center justify-center rounded-full ${
                    isActive ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"
                  }`}>
                    <Icon className="h-5 w-5" />
                  </div>
                  <span className={`text-xs mt-1 ${isActive ? "text-primary font-medium" : "text-muted-foreground"}`}>
                    {s.charAt(0) + s.slice(1).toLowerCase()}
                  </span>
                </div>
                {!isLast && (
                  <div className={`h-0.5 flex-1 ${i < currentIndex ? "bg-primary" : "bg-muted"}`} />
                )}
              </div>
            )
          })}
        </div>
        {next && (
          <div className="mt-4 flex gap-2">
            <Button
              size="sm"
              className="bg-primary hover:bg-[#059669]"
              onClick={() => handleStatusUpdate(next)}
              disabled={updating}
            >
              {updating ? "Updating..." : `Mark as ${next.charAt(0) + next.slice(1).toLowerCase()}`}
            </Button>
            {canCancel && (
              <Button
                size="sm"
                variant="outline"
                className="text-destructive border-destructive"
                onClick={() => handleStatusUpdate("CANCELLED")}
                disabled={updating}
              >
                Cancel Order
              </Button>
            )}
          </div>
        )}
      </Card>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Order Items + Info */}
        <div className="lg:col-span-2 space-y-6">
          {/* Items */}
          <Card className="p-6">
            <h2 className="font-semibold text-foreground mb-4 flex items-center gap-2">
              <ShoppingBag className="h-5 w-5 text-primary" />
              Items
            </h2>
            <div className="space-y-4">
              {order.items?.map((item) => (
                <div key={item.id} className="flex items-center gap-4">
                  <div className="h-16 w-16 rounded-xl bg-muted flex items-center justify-center flex-shrink-0">
                    <Package className="h-6 w-6 text-muted-foreground" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-foreground line-clamp-1">{item.title}</p>
                    <p className="text-sm text-muted-foreground">Qty: {item.quantity}</p>
                  </div>
                  <p className="font-medium text-foreground">{formatPrice(item.price * item.quantity)}</p>
                </div>
              ))}
            </div>
          </Card>

          {/* Chat */}
          <Card className="p-6">
            <h2 className="font-semibold text-foreground mb-4 flex items-center gap-2">
              <MessageCircle className="h-5 w-5 text-primary" />
              Messages
            </h2>
            {messages.length === 0 && (
              <p className="text-sm text-muted-foreground mb-4">No messages yet</p>
            )}
            <div className="space-y-3 max-h-80 overflow-y-auto mb-4">
              {messages.map((msg) => (
                <div key={msg.id} className="flex flex-col">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-medium text-foreground">{msg.sender_name}</span>
                    <span className="text-xs text-muted-foreground">{formatDate(msg.created_at)}</span>
                    {msg.is_auto_reply && (
                      <Badge variant="secondary" className="text-[10px]">Auto</Badge>
                    )}
                  </div>
                  <p className="text-sm text-muted-foreground bg-muted rounded-xl p-3">{msg.content}</p>
                </div>
              ))}
            </div>
            <form onSubmit={handleSendMessage} className="flex gap-2">
              <Input
                placeholder="Type a reply..."
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                className="flex-1"
              />
              <Button type="submit" size="icon" disabled={sending || !newMessage.trim()}>
                <Send className="h-4 w-4" />
              </Button>
            </form>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          <Card className="p-6 space-y-4">
            <h2 className="font-semibold text-foreground">Customer</h2>
            {order.customer_name && (
              <p className="text-sm text-foreground">{order.customer_name}</p>
            )}
            {order.customer_phone && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Phone className="h-4 w-4" />
                {order.customer_phone}
              </div>
            )}
          </Card>

          <Card className="p-6 space-y-4">
            <h2 className="font-semibold text-foreground">Delivery</h2>
            {order.fulfillment_method && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Truck className="h-4 w-4" />
                {order.fulfillment_method}
              </div>
            )}
            {order.delivery_area && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <MapPin className="h-4 w-4" />
                {order.delivery_area}
              </div>
            )}
            {order.delivery_fee !== undefined && (
              <p className="text-sm text-muted-foreground">
                Fee: {formatPrice(order.delivery_fee)}
              </p>
            )}
          </Card>

          <Card className="p-6 space-y-4">
            <h2 className="font-semibold text-foreground">Payment</h2>
            {order.payment_method && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <CreditCard className="h-4 w-4" />
                {order.payment_method}
              </div>
            )}
            {order.payment_status && (
              <Badge variant="secondary">{order.payment_status}</Badge>
            )}
          </Card>

          <Card className="p-6">
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Total</span>
                <span className="text-xl font-bold text-primary">{formatPrice(order.total)}</span>
              </div>
            </div>
          </Card>

          {order.seller_notes && (
            <Card className="p-6">
              <h2 className="font-semibold text-foreground mb-2">Notes</h2>
              <p className="text-sm text-muted-foreground">{order.seller_notes}</p>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
