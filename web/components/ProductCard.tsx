import Link from 'next/link'
import { formatPrice, stockClass, stockLabel, type Product } from '@/lib/api'

export default function ProductCard({ p }: { p: Product }) {
  const img = p.image_url || '/placeholder.svg'
  return (
    <div className="product-card">
      <Link href={`/product/${p.id}`}>
        <div className="image-wrap">
          <img src={img} alt={p.title} loading="lazy" onError={e => { (e.target as HTMLImageElement).src = '/placeholder.svg' }} />
        </div>
        <div className="body">
          <div className="shop-name">{p.shop_name || 'Unknown Shop'}</div>
          <div className="title">{p.title}</div>
          <div className="price">{formatPrice(p.price)}</div>
          <span className={`stock-badge ${stockClass(p.stock)}`}>{stockLabel(p.stock)}</span>
        </div>
      </Link>
    </div>
  )
}
