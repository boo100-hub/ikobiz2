import Link from "next/link"
import Image from "next/image"
import { MapPin, Truck } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import type { Shop } from "@/lib/api"

export function ShopCard({ shop }: { shop: Shop }) {
  return (
    <Link href={`/shop/${shop.slug || shop.id}`}>
      <article className="group overflow-hidden rounded-2xl border border-border bg-card shadow-sm transition-all duration-200 hover:shadow-lg hover:-translate-y-1">
        <div className="relative h-40 w-full overflow-hidden bg-muted">
          {shop.banner_image ? (
            <Image
              src={shop.banner_image}
              alt={shop.name}
              fill
              className="object-cover transition-transform duration-300 group-hover:scale-105"
            />
          ) : (
            <div className="flex h-full items-center justify-center text-muted-foreground/30">
              <Truck className="h-12 w-12" />
            </div>
          )}
          {shop.delivery_fee !== undefined && shop.delivery_fee >= 0 && (
            <Badge className="absolute right-3 top-3 bg-primary text-primary-foreground gap-1">
              <Truck className="h-3 w-3" />
              Delivery
            </Badge>
          )}
        </div>
        <div className="p-4 space-y-3">
          <div className="flex items-start justify-between gap-2">
            <div>
              <h3 className="font-semibold text-foreground group-hover:text-primary transition-colors line-clamp-1">
                {shop.name}
              </h3>
              {shop.category && (
                <p className="text-sm text-muted-foreground">{shop.category}</p>
              )}
            </div>
          </div>
          {shop.location_area && (
            <div className="flex items-center gap-1 text-sm text-muted-foreground">
              <MapPin className="h-4 w-4" />
              <span className="line-clamp-1">{shop.location_area}</span>
            </div>
          )}
          {shop.description && (
            <p className="text-sm text-muted-foreground line-clamp-2">{shop.description}</p>
          )}
        </div>
      </article>
    </Link>
  )
}
