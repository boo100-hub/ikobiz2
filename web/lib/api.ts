const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'

function getHeaders(auth = false): Record<string, string> {
  const h: Record<string, string> = { 'Content-Type': 'application/json' }
  if (auth) {
    const token = typeof window !== 'undefined' ? localStorage.getItem('ikobiz_token') : null
    if (token) h['Authorization'] = 'Bearer ' + token
  }
  return h
}

async function handleResponse(r: Response) {
  if (!r.ok) {
    const e = await r.json().catch(() => ({}))
    throw new Error(e.detail || `Request failed (${r.status})`)
  }
  return r.json()
}

export const api = {
  async get(path: string, auth = false) {
    const r = await fetch(API_BASE + path, { headers: getHeaders(auth) })
    return handleResponse(r)
  },

  async post(path: string, data: unknown, auth = false) {
    const r = await fetch(API_BASE + path, {
      method: 'POST',
      headers: getHeaders(auth),
      body: JSON.stringify(data),
    })
    return handleResponse(r)
  },

  async put(path: string, data: unknown, auth = false) {
    const r = await fetch(API_BASE + path, {
      method: 'PUT',
      headers: getHeaders(auth),
      body: JSON.stringify(data),
    })
    return handleResponse(r)
  },

  async del(path: string, auth = false) {
    const r = await fetch(API_BASE + path, {
      method: 'DELETE',
      headers: getHeaders(auth),
    })
    if (r.status === 204) return null
    return handleResponse(r)
  },
}

export function formatPrice(price: number) {
  return 'KSh ' + price.toLocaleString()
}

export function formatDate(dateStr: string) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString('en-KE', { year: 'numeric', month: 'short', day: 'numeric' })
}

export function timeAgo(dateStr: string) {
  if (!dateStr) return ''
  const now = new Date()
  const d = new Date(dateStr)
  const diff = Math.floor((now.getTime() - d.getTime()) / 1000)
  if (diff < 60) return 'just now'
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  if (diff < 2592000) return `${Math.floor(diff / 86400)}d ago`
  return formatDate(dateStr)
}

export function stockClass(qty: number) {
  if (qty > 10) return 'stock-active'
  if (qty > 0) return 'stock-low'
  return 'stock-oos'
}

export function stockLabel(qty: number) {
  if (qty > 10) return 'In Stock'
  if (qty > 0) return `Only ${qty} left`
  return 'Out of Stock'
}

export type Shop = {
  id: number; name: string; slug: string; description?: string
  banner_image?: string; product_count?: number
}

export type Product = {
  id: number; shop_id: number; title: string; description?: string
  price: number; stock: number; image_url?: string; status: string
  shop_name?: string; shop_slug?: string
}

export type IkobizListing = {
  id: number; seller_id?: number; seller_name: string; title: string
  description?: string; starting_price: number; buy_now_price?: number
  quantity: number; image_url?: string; status: string
  bid_count?: number; created_at?: string
}

export type CartItem = {
  id: number; quantity: number; type: 'shop_product' | 'secondary_market' | null
  product?: Product | null; listing?: IkobizListing | null
}

export type OrderItem = {
  id: number; title: string; price: number; quantity: number; type?: string; image_url?: string
}

export type Order = {
  id: number; total: number; status: string; created_at?: string; items: OrderItem[]
  customer_name?: string; customer_phone?: string
}
