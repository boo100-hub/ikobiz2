'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { api, formatPrice, type Product, type Shop } from '@/lib/api'
import { useAuth } from '@/lib/auth'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { ShoppingCart, Minus, Plus, Store } from 'lucide-react'
import { toast } from 'sonner'

export default function ProductPage() {
  const { id } = useParams<{ id: string }>()
  const router = useRouter()
  const { isLoggedIn } = useAuth()
  const [product, setProduct] = useState<Product | null>(null)
  const [shops, setShops] = useState<Shop[]>([])
  const [loading, setLoading] = useState(true)
  const [qty, setQty] = useState(1)
  const [adding, setAdding] = useState(false)

  useEffect(() => {
    Promise.all([
      api.get('/products'),
      api.get('/shops'),
    ])
      .then(([products, shopsData]) => {
        const found = (products as Product[]).find(
          (p) => p.id === Number(id),
        )
        setProduct(found || null)
        setShops(shopsData as Shop[])
      })
      .finally(() => setLoading(false))
  }, [id])

  const shop = product
    ? shops.find((s) => s.id === product.shop_id)
    : null
  const shopName = product?.shop_name || shop?.name || ''
  const shopSlug = product?.shop_slug || shop?.slug || ''

  const addToCart = async () => {
    if (!isLoggedIn) {
      router.push('/auth/login')
      return
    }
    setAdding(true)
    try {
      await api.post('/cart', { product_id: Number(id), quantity: qty }, true)
      toast.success('Added to cart!')
    } catch {
      toast.error('Failed to add to cart')
    }
    setAdding(false)
  }

  const buyNow = async () => {
    if (!isLoggedIn) {
      router.push('/auth/login')
      return
    }
    setAdding(true)
    try {
      await api.post('/cart', { product_id: Number(id), quantity: qty }, true)
      router.push('/cart')
    } catch {
      toast.error('Failed to process order')
    }
    setAdding(false)
  }

  if (loading) {
    return (
      <div className="container section">
        <div className="grid gap-8 lg:grid-cols-2">
          <Skeleton className="h-[400px] w-full rounded-2xl" />
          <div className="space-y-4">
            <Skeleton className="h-8 w-3/4" />
            <Skeleton className="h-10 w-1/3" />
            <Skeleton className="h-5 w-1/4" />
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-12 w-full" />
          </div>
        </div>
      </div>
    )
  }

  if (!product) {
    return (
      <div className="container section">
        <p className="py-20 text-center text-muted-foreground">
          Product not found.
        </p>
      </div>
    )
  }

  const img = product.image_url || '/placeholder.svg'
  const isOos = product.stock <= 0

  return (
    <div className="container section">
      <div className="grid gap-8 lg:grid-cols-2">
        {/* Left: Product Image */}
        <div className="relative overflow-hidden rounded-2xl bg-muted">
          <img
            src={img}
            alt={product.title}
            className="h-[400px] w-full object-cover"
            onError={(e) => {
              ;(e.target as HTMLImageElement).src = '/placeholder.svg'
            }}
          />
        </div>

        {/* Right: Product Info */}
        <div className="space-y-6">
          {product.category && (
            <Badge variant="secondary">{product.category}</Badge>
          )}

          <h1 className="text-2xl font-bold md:text-3xl">
            {product.title}
          </h1>

          <div className="text-3xl font-bold text-primary">
            {formatPrice(product.price)}
          </div>

          {/* Stock Status */}
          {isOos ? (
            <Badge variant="destructive">Out of Stock</Badge>
          ) : (
            <div className="flex items-center gap-2 text-sm">
              <span className="h-2 w-2 rounded-full bg-green-500" />
              <span className="font-medium text-green-600">In Stock</span>
              {product.stock > 0 && (
                <span className="text-muted-foreground">
                  ({product.stock} available)
                </span>
              )}
            </div>
          )}

          {/* Description */}
          {product.description && (
            <p className="leading-relaxed text-muted-foreground">
              {product.description}
            </p>
          )}

          {/* Quantity Selector */}
          {!isOos && (
            <div className="space-y-2">
              <label className="text-sm font-medium">Quantity</label>
              <div className="flex items-center rounded-xl border border-border">
                <Button
                  variant="ghost"
                  size="icon"
                  className="rounded-l-xl rounded-r-none"
                  onClick={() => setQty(Math.max(1, qty - 1))}
                  disabled={qty <= 1}
                >
                  <Minus className="h-4 w-4" />
                </Button>
                <span className="w-12 text-center font-medium">{qty}</span>
                <Button
                  variant="ghost"
                  size="icon"
                  className="rounded-r-xl rounded-l-none"
                  onClick={() => setQty(Math.min(product.stock, qty + 1))}
                  disabled={qty >= product.stock}
                >
                  <Plus className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          {!isOos && (
            <div className="flex flex-col gap-3 sm:flex-row">
              <Button
                className="flex h-12 flex-1 gap-2"
                onClick={addToCart}
                disabled={adding}
              >
                <ShoppingCart className="h-5 w-5" />
                {adding ? 'Adding...' : 'Add to Cart'}
              </Button>
              <Button
                variant="secondary"
                className="flex h-12 flex-1"
                onClick={buyNow}
                disabled={adding}
              >
                {adding ? 'Processing...' : 'Buy Now'}
              </Button>
            </div>
          )}

          {/* Shop Info */}
          {(shopName || shop) && (
            <div className="rounded-2xl border border-border bg-card p-4">
              <Link
                href={`/shop/${shopSlug}`}
                className="group flex items-center gap-3"
              >
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10">
                  <Store className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold transition-colors group-hover:text-primary">
                    {shopName}
                  </h3>
                </div>
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
