import Link from 'next/link'
import type { Shop } from '@/lib/api'

export default function ShopCard({ s }: { s: Shop }) {
  const banner = s.banner_image || '/banner-placeholder.svg'
  return (
    <Link href={`/shops/${s.slug}`} className="shop-card">
      <div className="banner">
        <img src={banner} alt={s.name} loading="lazy" onError={e => { (e.target as HTMLImageElement).src = '/banner-placeholder.svg' }} />
      </div>
      <div className="body">
        <img src="/shop-placeholder.svg" alt={s.name} className="logo" />
        <h3>{s.name}</h3>
        <div className="desc">{s.description || `Quality products from ${s.name}`}</div>
      </div>
    </Link>
  )
}
