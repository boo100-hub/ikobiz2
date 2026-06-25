'use client'

import { useEffect, useState, useRef, useMemo } from 'react'
import Link from 'next/link'
import { api, formatPrice, formatDate, type Order, type Message } from '@/lib/api'
import { useAuth } from '@/lib/auth'
import { toast } from 'sonner'
import {
  Search,
  MoreHorizontal,
  MessageCircle,
  CheckCircle,
  Truck,
  XCircle,
  Send,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'

const STATUS_VARIANT: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  PENDING: 'outline',
  CONFIRMED: 'default',
  DISPATCHED: 'secondary',
  DELIVERED: 'default',
  CANCELLED: 'destructive',
}

const STATUS_LABEL: Record<string, string> = {
  PENDING: 'Pending',
  CONFIRMED: 'Confirmed',
  DISPATCHED: 'Dispatched',
  DELIVERED: 'Delivered',
  CANCELLED: 'Cancelled',
}

const NEXT_ACTIONS: Record<
  string,
  { label: string; status: string; icon: typeof CheckCircle }[]
> = {
  PENDING: [
    { label: 'Confirm Order', status: 'CONFIRMED', icon: CheckCircle },
    { label: 'Cancel Order', status: 'CANCELLED', icon: XCircle },
  ],
  CONFIRMED: [
    { label: 'Dispatch Order', status: 'DISPATCHED', icon: Truck },
    { label: 'Cancel Order', status: 'CANCELLED', icon: XCircle },
  ],
  DISPATCHED: [
    { label: 'Mark Delivered', status: 'DELIVERED', icon: CheckCircle },
  ],
  DELIVERED: [],
  CANCELLED: [],
}

const FILTER_TABS = ['all', 'pending', 'confirmed', 'dispatched', 'delivered'] as const

export default function SellerOrdersPage() {
  const { user } = useAuth()
  const [orders, setOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [tab, setTab] = useState('all')
  const [expandedOrder, setExpandedOrder] = useState<number | null>(null)
  const [messages, setMessages] = useState<Record<number, Message[]>>({})
  const [newMessage, setNewMessage] = useState('')
  const [sending, setSending] = useState(false)
  const [updating, setUpdating] = useState<number | null>(null)
  const chatEnd = useRef<HTMLDivElement>(null)

  const fetchOrders = async () => {
    setLoading(true)
    try {
      const data = await api.get('/seller/shop-orders', true)
      const list = Array.isArray(data) ? data : []
      list.sort(
        (a: any, b: any) =>
          new Date(b.created_at || '').getTime() - new Date(a.created_at || '').getTime()
      )
      setOrders(list)
    } catch {
      toast.error('Failed to load orders')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchOrders()
  }, [])

  useEffect(() => {
    chatEnd.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, expandedOrder])

  const filtered = useMemo(() => {
    let list = orders
    if (tab !== 'all') {
      list = list.filter(
        (o) => (o.status || 'PENDING').toUpperCase() === tab.toUpperCase()
      )
    }
    if (search.trim()) {
      const q = search.toLowerCase()
      list = list.filter(
        (o) =>
          String(o.id).includes(q) ||
          (o.customer_name || '').toLowerCase().includes(q) ||
          (o.customer_phone || '').toLowerCase().includes(q)
      )
    }
    return list
  }, [orders, tab, search])

  const updateStatus = async (orderId: number, status: string) => {
    setUpdating(orderId)
    try {
      await api.patch(`/orders/${orderId}/status`, { status: status.toLowerCase() }, true)
      toast.success(`Order #${orderId} marked as ${STATUS_LABEL[status] || status.toLowerCase()}`)
      await fetchOrders()
    } catch (e: any) {
      toast.error(e.message || 'Failed to update status')
    } finally {
      setUpdating(null)
    }
  }

  const toggleChat = async (orderId: number) => {
    if (expandedOrder === orderId) {
      setExpandedOrder(null)
      return
    }
    setExpandedOrder(orderId)
    if (!messages[orderId]) {
      try {
        const data = await api.get(`/orders/${orderId}/messages`, true)
        setMessages((prev) => ({ ...prev, [orderId]: Array.isArray(data) ? data : [] }))
      } catch {
        setMessages((prev) => ({ ...prev, [orderId]: [] }))
      }
    }
  }

  const handleSend = async (orderId: number) => {
    if (!newMessage.trim() || sending) return
    setSending(true)
    try {
      const msg = await api.post(
        `/orders/${orderId}/messages`,
        { content: newMessage.trim() },
        true
      )
      setMessages((prev) => ({
        ...prev,
        [orderId]: [...(prev[orderId] || []), msg],
      }))
      setNewMessage('')
    } catch (e: any) {
      toast.error(e.message || 'Failed to send message')
    } finally {
      setSending(false)
    }
  }

  const getOrderId = (o: any) => o.order_id || o.id
  const currentUserId = user?.id ? Number(user.id) : null

  if (loading && orders.length === 0) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-muted border-t-primary" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Orders</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Manage and track all incoming orders
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={fetchOrders} disabled={loading}>
          Refresh
        </Button>
      </div>

      {/* Tabs + Search */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <Tabs value={tab} onValueChange={(v) => setTab(v)} className="w-full sm:w-auto">
          <TabsList>
            {FILTER_TABS.map((t) => (
              <TabsTrigger key={t} value={t} className="capitalize">
                {t}
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>
        <div className="relative w-full sm:w-72">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search by order # or customer..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
      </div>

      {/* Desktop Table */}
      <div className="hidden md:block rounded-lg border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Order #</TableHead>
              <TableHead>Customer</TableHead>
              <TableHead>Items</TableHead>
              <TableHead>Amount</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Date</TableHead>
              <TableHead>Actions</TableHead>
              <TableHead className="w-12" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {filtered.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={8}
                  className="h-32 text-center text-muted-foreground"
                >
                  {search || tab !== 'all'
                    ? 'No orders match your filters.'
                    : 'No orders yet. Orders will appear here when customers buy.'}
                </TableCell>
              </TableRow>
            ) : (
              filtered.map((o: any) => {
                const oid = getOrderId(o)
                const status = (o.status || 'PENDING').toUpperCase()
                const isExpanded = expandedOrder === oid
                const itemNames = (o.items || [])
                  .map((i: any) => i.title)
                  .filter(Boolean)
                  .join(', ')

                return (
                  <TableRow
                    key={oid}
                    className={
                      status === 'PENDING' ? 'bg-amber-50/50 dark:bg-amber-950/10' : ''
                    }
                  >
                    <TableCell>
                      <Link
                        href={`/seller/orders/${oid}`}
                        className="font-medium text-primary hover:underline"
                      >
                        #{oid}
                      </Link>
                    </TableCell>
                    <TableCell>
                      <div className="font-medium">{o.customer_name || '—'}</div>
                      {o.customer_phone && (
                        <div className="text-xs text-muted-foreground">
                          {o.customer_phone}
                        </div>
                      )}
                    </TableCell>
                    <TableCell className="max-w-[200px]">
                      <span className="block truncate text-sm" title={itemNames}>
                        {itemNames || `${(o.items || []).length} item(s)`}
                      </span>
                    </TableCell>
                    <TableCell className="font-medium">
                      {formatPrice(o.total || 0)}
                    </TableCell>
                    <TableCell>
                      <Badge variant={STATUS_VARIANT[status] || 'outline'}>
                        {STATUS_LABEL[status] || status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {formatDate(o.created_at)}
                    </TableCell>
                    <TableCell>
                      {(NEXT_ACTIONS[status] || []).length > 0 ? (
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button
                              variant="ghost"
                              size="icon-sm"
                              disabled={updating === oid}
                            >
                              {updating === oid ? (
                                <span className="h-4 w-4 animate-spin rounded-full border-2 border-muted-foreground border-t-transparent" />
                              ) : (
                                <MoreHorizontal className="h-4 w-4" />
                              )}
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end" className="w-48">
                            {NEXT_ACTIONS[status].map((action) => {
                              const Icon = action.icon
                              return (
                                <DropdownMenuItem
                                  key={action.status}
                                  onClick={() => updateStatus(oid, action.status)}
                                >
                                  <Icon className="h-4 w-4" />
                                  {action.label}
                                </DropdownMenuItem>
                              )
                            })}
                          </DropdownMenuContent>
                        </DropdownMenu>
                      ) : (
                        <span className="text-xs text-muted-foreground">—</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        onClick={() => toggleChat(oid)}
                        data-state={isExpanded ? 'open' : 'closed'}
                        className="data-[state=open]:bg-muted"
                      >
                        <MessageCircle className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                )
              })
            )}
          </TableBody>
        </Table>
      </div>

      {/* Inline Chat Panel (desktop) */}
      {expandedOrder && (() => {
        const order = filtered.find((o: any) => getOrderId(o) === expandedOrder)
        return (
          <div className="hidden md:block rounded-lg border bg-card p-4">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="flex items-center gap-2 font-semibold">
                <MessageCircle className="h-4 w-4" />
                Messages for Order #{expandedOrder}
              </h3>
              <Button variant="ghost" size="sm" onClick={() => setExpandedOrder(null)}>
                Close
              </Button>
            </div>
            {order?.seller_notes && (
              <div className="mb-4 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm dark:border-amber-800 dark:bg-amber-950/20">
                <strong>Your note:</strong> {order.seller_notes}
              </div>
            )}
            <OrderChat
              messages={messages[expandedOrder] || []}
              newMessage={newMessage}
              sending={sending}
              chatEnd={chatEnd}
              currentUserId={currentUserId}
              onNewMessageChange={setNewMessage}
              onSend={() => handleSend(expandedOrder)}
            />
          </div>
        )
      })()}

      {/* Mobile Cards */}
      <div className="space-y-3 md:hidden">
        {filtered.length === 0 ? (
          <div className="rounded-lg border p-8 text-center text-muted-foreground">
            {search || tab !== 'all'
              ? 'No orders match your filters.'
              : 'No orders yet. Orders will appear here when customers buy.'}
          </div>
        ) : (
          filtered.map((o: any) => {
            const oid = getOrderId(o)
            const status = (o.status || 'PENDING').toUpperCase()
            const isExpanded = expandedOrder === oid
            const itemNames = (o.items || [])
              .map((i: any) => i.title)
              .filter(Boolean)
              .join(', ')

            return (
              <div key={oid} className="rounded-lg border bg-card p-4">
                {/* Card Header */}
                <div className="flex items-start justify-between">
                  <div>
                    <Link
                      href={`/seller/orders/${oid}`}
                      className="font-semibold text-primary hover:underline"
                    >
                      #{oid}
                    </Link>
                    <div className="mt-0.5 text-sm font-medium">
                      {o.customer_name || '—'}
                    </div>
                    {o.customer_phone && (
                      <div className="text-xs text-muted-foreground">
                        {o.customer_phone}
                      </div>
                    )}
                  </div>
                  <Badge variant={STATUS_VARIANT[status] || 'outline'}>
                    {STATUS_LABEL[status] || status}
                  </Badge>
                </div>

                {/* Card Details */}
                <div className="mt-3 grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <span className="text-muted-foreground">Items: </span>
                    <span className="block truncate" title={itemNames}>
                      {itemNames || `${(o.items || []).length} item(s)`}
                    </span>
                  </div>
                  <div className="text-right">
                    <span className="font-semibold">
                      {formatPrice(o.total || 0)}
                    </span>
                  </div>
                  <div className="col-span-2 text-xs text-muted-foreground">
                    {formatDate(o.created_at)}
                  </div>
                </div>

                {/* Card Actions */}
                <div className="mt-3 flex items-center gap-2">
                  {(NEXT_ACTIONS[status] || []).length > 0 && (
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="outline" size="sm" disabled={updating === oid}>
                          {updating === oid && (
                            <span className="mr-1 h-3 w-3 animate-spin rounded-full border-2 border-muted-foreground border-t-transparent" />
                          )}
                          Update Status
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="start" className="w-48">
                        {NEXT_ACTIONS[status].map((action) => {
                          const Icon = action.icon
                          return (
                            <DropdownMenuItem
                              key={action.status}
                              onClick={() => updateStatus(oid, action.status)}
                            >
                              <Icon className="h-4 w-4" />
                              {action.label}
                            </DropdownMenuItem>
                          )
                        })}
                      </DropdownMenuContent>
                    </DropdownMenu>
                  )}
                  <Button
                    variant={isExpanded ? 'default' : 'secondary'}
                    size="sm"
                    onClick={() => toggleChat(oid)}
                  >
                    <MessageCircle className="mr-1 h-4 w-4" />
                    {isExpanded ? 'Hide Chat' : 'Chat'}
                  </Button>
                </div>

                {/* Inline Chat (mobile) */}
                {isExpanded && (
                  <div className="mt-4 border-t pt-4">
                    {o.seller_notes && (
                      <div className="mb-3 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm dark:border-amber-800 dark:bg-amber-950/20">
                        <strong>Your note:</strong> {o.seller_notes}
                      </div>
                    )}
                    <OrderChat
                      messages={messages[oid] || []}
                      newMessage={newMessage}
                      sending={sending}
                      chatEnd={chatEnd}
                      currentUserId={currentUserId}
                      onNewMessageChange={setNewMessage}
                      onSend={() => handleSend(oid)}
                    />
                  </div>
                )}
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}

function OrderChat({
  messages,
  newMessage,
  sending,
  chatEnd,
  currentUserId,
  onNewMessageChange,
  onSend,
}: {
  messages: Message[]
  newMessage: string
  sending: boolean
  chatEnd: React.RefObject<HTMLDivElement | null>
  currentUserId: number | null
  onNewMessageChange: (val: string) => void
  onSend: () => void
}) {
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      onSend()
    }
  }

  return (
    <div className="space-y-3">
      <div className="max-h-[320px] overflow-y-auto space-y-3 rounded-lg border bg-muted/30 p-4">
        {messages.length === 0 ? (
          <p className="py-8 text-center text-sm text-muted-foreground">
            No messages for this order yet.
          </p>
        ) : (
          messages.map((m) => {
            const isMine =
              currentUserId !== null && m.sender_id === currentUserId
            return (
              <div
                key={m.id}
                className={`flex ${isMine ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-xl px-4 py-2.5 text-sm ${
                    isMine
                      ? 'bg-primary text-primary-foreground rounded-br-sm'
                      : 'bg-card border rounded-bl-sm'
                  }`}
                >
                  <div className="mb-1 flex items-center gap-2">
                    <span className="text-xs font-medium opacity-70">
                      {m.is_auto_reply ? '🤖 ' : ''}
                      {m.sender_name}
                    </span>
                    <span className="ml-auto text-[10px] opacity-50">
                      {formatDate(m.created_at)}
                    </span>
                  </div>
                  <p className="whitespace-pre-wrap">{m.content}</p>
                </div>
              </div>
            )
          })
        )}
        <div ref={chatEnd} />
      </div>

      <div className="flex gap-2">
        <Input
          value={newMessage}
          onChange={(e) => onNewMessageChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type your reply..."
          className="flex-1"
        />
        <Button onClick={onSend} disabled={sending || !newMessage.trim()} size="sm">
          {sending ? (
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-background border-t-transparent" />
          ) : (
            <Send className="h-4 w-4" />
          )}
        </Button>
      </div>
    </div>
  )
}
