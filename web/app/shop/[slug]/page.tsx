"use client"

import { useEffect, useState } from "react"
import { useParams } from "next/navigation"
import Image from "next/image"
import Link from "next/link"
import { ProductCard } from "@/components/ProductCard"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { MapPin, Truck, Clock, CreditCard, Store, ChevronRight, Package } from "lucide-react"
import { api, formatPrice, type Shop, type Product } from "@/lib/api"

export default function ShopDetailPage() {
  const { slug } = useParams<{ slug: string }>()
  const [shop, setShop] = useState<Shop | null>(null)
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    (async () => {
      setLoading(true)
      try {
        const shops = (await api.get("/shops")) as Shop[]
        const found = shops.find(
          (s) => s.slug === slug || String(s.id) === slug,
        )
        if (!found) {
          setLoading(false)
          return
        }
        setShop(found)
        const allProducts = (await api.get("/products")) as Product[]
        setProducts(allProducts.filter((p) => p.shop_id === found.id))
      } catch {
        /* ignore */
      }
      setLoading(false)
    })()
  }, [slug])

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <div className="h-48 w-full bg-muted animate-pulse md:h-64 lg:h-80" />
        <div className="mx-auto max-w-7xl px-4 md:px-6">
          <div className="relative -mt-16 mb-8 md:-mt-20">
            <div className="flex flex-col gap-4 md:flex-row md:items-end md:gap-6">
              <Skeleton className="h-24 w-24 rounded-2xl md:h-32 md:w-32" />
              <div className="flex-1 space-y-3 pb-2">
                <Skeleton className="h-5 w-24" />
                <Skeleton className="h-8 w-72" />
                <Skeleton className="h-4 w-48" />
              </div>
            </div>
          </div>
          <div className="grid gap-8 lg:grid-cols-3 mb-12">
            <div className="lg:col-span-1 space-y-6">
              <Skeleton className="h-40 rounded-2xl" />
              <Skeleton className="h-56 rounded-2xl" />
            </div>
            <div className="lg:col-span-2">
              <Skeleton className="h-8 w-48 mb-6" />
              <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
                {[1, 2, 3, 4, 5, 6].map((i) => (
                  <div key={i} className="rounded-2xl border border-border bg-card overflow-hidden">
                    <Skeleton className="aspect-square w-full" />
                    <div className="p-4 space-y-3">
                      <Skeleton className="h-4 w-3/4" />
                      <Skeleton className="h-3 w-1/2" />
                      <Skeleton className="h-8 w-full" />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (!shop) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="text-center">
          <Store className="mx-auto h-12 w-12 text-muted-foreground/50" />
          <h2 className="mt-4 text-xl font-semibold text-foreground">Shop not found</h2>
          <p className="mt-2 text-muted-foreground">
            The shop you&apos;re looking for doesn&apos;t exist or has been removed.
          </p>
          <Link
            href="/search"
            className="mt-6 inline-flex items-center gap-1 text-sm text-primary hover:underline"
          >
            Browse all shops
            <ChevronRight className="h-4 w-4" />
          </Link>
        </div>
      </div>
    )
  }

  const modes = shop.fulfillment_modes
    ? shop.fulfillment_modes.replace(/,/g, " + ").replace(/_/g, " ")
    : null
  const payments = shop.payment_methods
    ? shop.payment_methods.replace(/,/g, ", ").replace(/_/g, " ")
    : null

  return (
    <div className="min-h-screen bg-background">
      {/* Banner */}
      <div className="relative h-48 w-full md:h-64 lg:h-80">
        {shop.banner_image ? (
          <Image
            src={shop.banner_image}
            alt={shop.name}
            fill
            className="object-cover"
            priority
          />
        ) : (
          <div className="h-full w-full bg-gradient-to-br from-primary/20 to-primary/5" />
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
      </div>

      <div className="mx-auto max-w-7xl px-4 md:px-6">
        {/* Shop Header */}
        <div className="relative -mt-16 mb-8 md:-mt-20">
          <div className="flex flex-col gap-4 md:flex-row md:items-end md:gap-6">
            {/* Logo */}
            <div className="relative h-24 w-24 flex-shrink-0 overflow-hidden rounded-2xl border-4 border-card bg-card shadow-lg md:h-32 md:w-32">
              <div className="flex h-full w-full items-center justify-center bg-muted">
                <Store className="h-10 w-10 text-muted-foreground/40" />
              </div>
            </div>

            {/* Info */}
            <div className="flex-1 pb-2">
              <div className="mb-2 flex flex-wrap items-center gap-2">
                {shop.category && (
                  <Badge className="bg-primary/10 text-primary hover:bg-primary/20">
                    {shop.category.charAt(0).toUpperCase() + shop.category.slice(1)}
                  </Badge>
                )}
                {modes?.toLowerCase().includes("delivery") && (
                  <Badge variant="secondary" className="gap-1">
                    <Truck className="h-3 w-3" />
                    Delivery
                  </Badge>
                )}
              </div>
              <h1 className="text-2xl font-bold text-foreground md:text-3xl">
                {shop.name}
              </h1>
              <p className="mt-1 text-sm text-muted-foreground">
                {shop.description || `Quality products from ${shop.name}`}
              </p>
              {shop.location_area && (
                <div className="mt-2 flex items-center gap-1 text-sm text-muted-foreground">
                  <MapPin className="h-4 w-4" />
                  {shop.location_area}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Breadcrumb */}
        <nav className="mb-6 flex items-center gap-2 text-sm text-muted-foreground">
          <Link href="/" className="hover:text-primary">
            Home
          </Link>
          <ChevronRight className="h-4 w-4" />
          <Link href="/search" className="hover:text-primary">
            Shops
          </Link>
          <ChevronRight className="h-4 w-4" />
          <span className="text-foreground">{shop.name}</span>
        </nav>

        <div className="grid gap-8 lg:grid-cols-3 mb-12">
          {/* Sidebar */}
          <div className="lg:col-span-1">
            <div className="sticky top-24 space-y-6">
              {/* About */}
              {shop.description && (
                <div className="rounded-2xl border border-border bg-card p-6">
                  <h2 className="mb-3 flex items-center gap-2 font-semibold text-foreground">
                    <Store className="h-5 w-5 text-primary" />
                    About
                  </h2>
                  <p className="text-sm leading-relaxed text-muted-foreground">
                    {shop.description}
                  </p>
                </div>
              )}

              {/* Business Info */}
              <div className="space-y-4 rounded-2xl border border-border bg-card p-6">
                <h2 className="font-semibold text-foreground">Business Info</h2>

                {shop.operating_hours && (
                  <div className="flex items-start gap-3">
                    <Clock className="mt-0.5 h-5 w-5 text-muted-foreground" />
                    <div>
                      <p className="text-sm font-medium text-foreground">
                        Operating Hours
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {shop.operating_hours}
                      </p>
                    </div>
                  </div>
                )}

                {modes && (
                  <div className="flex items-start gap-3">
                    <Truck className="mt-0.5 h-5 w-5 text-muted-foreground" />
                    <div>
                      <p className="text-sm font-medium text-foreground">
                        Fulfillment
                      </p>
                      <p className="text-sm text-muted-foreground">{modes}</p>
                    </div>
                  </div>
                )}

                {shop.delivery_fee != null && (
                  <div className="flex items-start gap-3">
                    <Truck className="mt-0.5 h-5 w-5 text-muted-foreground" />
                    <div>
                      <p className="text-sm font-medium text-foreground">
                        Delivery Fee
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {formatPrice(shop.delivery_fee)}
                      </p>
                    </div>
                  </div>
                )}

                {payments && (
                  <div className="flex items-start gap-3">
                    <CreditCard className="mt-0.5 h-5 w-5 text-muted-foreground" />
                    <div>
                      <p className="text-sm font-medium text-foreground">
                        Payment Methods
                      </p>
                      <p className="text-sm text-muted-foreground">{payments}</p>
                    </div>
                  </div>
                )}

                {shop.pickup_address && (
                  <div className="flex items-start gap-3">
                    <MapPin className="mt-0.5 h-5 w-5 text-muted-foreground" />
                    <div>
                      <p className="text-sm font-medium text-foreground">
                        Pickup Address
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {shop.pickup_address}
                      </p>
                    </div>
                  </div>
                )}

                {shop.location_area && (
                  <div className="flex items-start gap-3">
                    <MapPin className="mt-0.5 h-5 w-5 text-muted-foreground" />
                    <div>
                      <p className="text-sm font-medium text-foreground">
                        Location
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {shop.location_area}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Products */}
          <div className="lg:col-span-2">
            <div className="mb-6 flex items-center justify-between">
              <h2 className="text-xl font-bold text-foreground">
                Products ({products.length})
              </h2>
            </div>

            {products.length === 0 ? (
              <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-border py-16 text-center">
                <Package className="h-12 w-12 text-muted-foreground/50" />
                <p className="mt-4 text-lg font-medium text-foreground">
                  No products yet
                </p>
                <p className="mt-1 text-sm text-muted-foreground">
                  This shop hasn&apos;t listed any products yet.
                </p>
              </div>
            ) : (
              <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
                {products.map((product) => (
                  <ProductCard key={product.id} product={product} />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
