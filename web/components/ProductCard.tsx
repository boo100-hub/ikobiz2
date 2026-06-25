"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import Image from "next/image"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ShoppingCart } from "lucide-react"
import type { Product } from "@/lib/api"
import { formatPrice, api } from "@/lib/api"
import { useAuth } from "@/lib/auth"
import { toast } from "sonner"

export function ProductCard({ product }: { product: Product }) {
  const router = useRouter()
  const { isLoggedIn } = useAuth()
  const [adding, setAdding] = useState(false)

  const addToCart = async () => {
    if (!isLoggedIn) {
      router.push('/auth/login')
      return
    }
    setAdding(true)
    try {
      await api.post('/cart', { product_id: product.id, quantity: 1 }, true)
      toast.success('Added to cart!')
    } catch {
      toast.error('Failed to add to cart')
    }
    setAdding(false)
  }

  return (
    <article className="group overflow-hidden rounded-2xl border border-border bg-card shadow-sm transition-all duration-200 hover:shadow-lg hover:-translate-y-1">
      <Link href={`/product/${product.id}`}>
        <div className="relative aspect-square w-full overflow-hidden bg-muted">
          {product.image_url ? (
            <Image
              src={product.image_url}
              alt={product.title}
              fill
              className="object-cover transition-transform duration-300 group-hover:scale-105"
            />
          ) : (
            <div className="flex h-full items-center justify-center text-muted-foreground/30">
              <ShoppingCart className="h-12 w-12" />
            </div>
          )}
          {product.stock <= 0 && (
            <div className="absolute inset-0 flex items-center justify-center bg-background/80">
              <Badge variant="secondary" className="text-sm">Out of Stock</Badge>
            </div>
          )}
        </div>
      </Link>
      <div className="p-4 space-y-3">
        <Link href={`/product/${product.id}`}>
          <h3 className="font-medium text-foreground group-hover:text-primary transition-colors line-clamp-2">
            {product.title}
          </h3>
        </Link>
        {product.shop_name && (
          <Link
            href={`/shop/${product.shop_slug || product.shop_id}`}
            className="text-sm text-muted-foreground hover:text-primary transition-colors line-clamp-1"
          >
            {product.shop_name}
          </Link>
        )}
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-baseline gap-2">
            <span className="text-lg font-bold text-primary">
              {formatPrice(product.price)}
            </span>
          </div>
        </div>
        <Button
          className="w-full gap-2 bg-primary hover:bg-[#059669] text-primary-foreground"
          disabled={product.stock <= 0 || adding}
          onClick={addToCart}
        >
          <ShoppingCart className="h-4 w-4" />
          {adding ? 'Adding...' : 'Add to Cart'}
        </Button>
      </div>
    </article>
  )
}
