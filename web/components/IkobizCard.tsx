import Link from 'next/link'
import { formatPrice, type IkobizListing } from '@/lib/api'

export default function IkobizCard({ p }: { p: IkobizListing }) {
  const img = p.image_url || '/placeholder.svg'
  const st = p.status || 'OPEN'
  const hasBuyNow = p.buy_now_price != null

  const priceDisplay = hasBuyNow
    ? `${formatPrice(p.buy_now_price!)} <span class="price-sub">or bid from ${formatPrice(p.starting_price)}</span>`
    : `${formatPrice(p.starting_price)} <span class="price-sub">starting bid</span>`

  return (
    <div className="product-card">
      <Link href={`/market/${p.id}`}>
        <div className="image-wrap">
          <img src={img} loading="lazy" onError={e => { (e.target as HTMLImageElement).src = '/placeholder.svg' }} />
        </div>
        <div className="body">
          <div className="badge-row">
            <span className="badge badge-primary">Bid</span>
            {hasBuyNow && <span className="badge badge-success">Buy Now</span>}
            {st === 'CLOSED' && <span className="badge badge-danger">Closed</span>}
            {st === 'SOLD' && <span className="badge badge-danger">Sold</span>}
            {st === 'NEGOTIATING' && <span className="badge badge-warning">Negotiating</span>}
          </div>
          <div className="title">{p.title}</div>
          <div className="price" dangerouslySetInnerHTML={{ __html: priceDisplay }} />
          <div className="seller-info">
            Seller: {p.seller_name || 'Unknown'} {p.quantity > 0 && `· Qty: ${p.quantity}`}
          </div>
        </div>
      </Link>
    </div>
  )
}
