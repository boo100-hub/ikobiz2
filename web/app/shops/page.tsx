'use client'

import { Suspense, useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { api, type Shop, type Product } from '@/lib/api'
import { ShopCard } from '@/components/ShopCard'
import { ProductCard } from '@/components/ProductCard'

function SearchResultsContent() {
  const searchParams = useSearchParams()
  const query = searchParams.get('q') || ''

  const [shops, setShops] = useState<Shop[]>([])
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!query.trim()) {
      setLoading(false)
      return
    }
    const q = query.toLowerCase()
    Promise.all([
      api.get('/shops').catch(() => []),
      api.get('/products').catch(() => []),
    ]).then(([shopData, prodData]) => {
      const allShops = Array.isArray(shopData) ? shopData : []
      const allProducts = Array.isArray(prodData) ? prodData : []

      const matchingShops = allShops.filter((s: Shop) =>
        s.name.toLowerCase().includes(q) ||
        (s.description || '').toLowerCase().includes(q) ||
        (s.location_area || '').toLowerCase().includes(q) ||
        (s.category || '').toLowerCase().includes(q)
      )

      const matchingShopIds = new Set(matchingShops.map((s: Shop) => s.id))
      const matchingProducts = allProducts.filter((p: Product) =>
        p.title.toLowerCase().includes(q) ||
        (p.description || '').toLowerCase().includes(q) ||
        (p.shop_name || '').toLowerCase().includes(q) ||
        matchingShopIds.has(p.shop_id)
      )

      setShops(matchingShops)
      setProducts(matchingProducts)
    }).catch(() => {}).finally(() => setLoading(false))
  }, [query])

  if (loading) return <div className="loading" />

  return (
    <div className="container section" style={{ paddingTop: '2rem' }}>
      <h1 style={{ marginBottom: '0.5rem' }}>
        {query ? `Results for "${query}"` : 'Search Shops & Products'}
      </h1>
      <p style={{ color: 'var(--gray-400)', marginBottom: '2rem' }}>
        {shops.length + products.length} result(s) found
      </p>

      {shops.length > 0 && (
        <>
          <div className="section-header"><h2>Shops ({shops.length})</h2></div>
          <div className="shop-grid" style={{ marginBottom: '2rem' }}>
            {shops.map(s => <ShopCard key={s.id} shop={s} />)}
          </div>
        </>
      )}

      {products.length > 0 && (
        <>
          <div className="section-header"><h2>Products ({products.length})</h2></div>
          <div className="shop-grid">
            {products.map(p => <ProductCard key={p.id} product={p} />)}
          </div>
        </>
      )}

      {shops.length === 0 && products.length === 0 && query && (
        <div style={{ textAlign: 'center', padding: '3rem 1rem' }}>
          <p>No shops or products found for "{query}".</p>
          <p style={{ color: 'var(--gray-400)', fontSize: '0.9rem' }}>Try different keywords or browse all shops from the homepage.</p>
        </div>
      )}

      {!query && shops.length === 0 && (
        <div style={{ textAlign: 'center', padding: '3rem 1rem' }}>
          <p>Type something in the search bar to find shops and products.</p>
        </div>
      )}
    </div>
  )
}

export default function SearchResultsPage() {
  return (
    <Suspense fallback={<div className="loading" />}>
      <SearchResultsContent />
    </Suspense>
  )
}
