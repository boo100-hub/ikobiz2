'use client'

import { useEffect, useState, useRef } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useAuth } from '@/lib/auth'
import { api } from '@/lib/api'

const STEPS = [
  { num: 1, label: 'Shop Details', icon: '🏪' },
  { num: 2, label: 'Fulfillment', icon: '🚚' },
  { num: 3, label: 'Payment', icon: '💳' },
  { num: 4, label: 'Products', icon: '📦' },
]

const CATEGORIES = [
  'food', 'electronics', 'fashion', 'health', 'home',
  'sports', 'services', 'agriculture', 'other',
]

const KENYAN_AREAS = [
  'Nairobi CBD', 'Westlands', 'Kilimani', 'Karen', 'Langata',
  'Eastlands', 'South B', 'South C', 'Ngong Road', 'Thika Road',
  'Mombasa Island', 'Nyali', 'Bamburi', 'Kisumu CBD', 'Milimani',
  'Nakuru CBD', 'Eldoret', 'Rongai', 'Kawangware', 'Githurai',
  'Kitengela', 'Athi River', 'Ruaka', 'Kikuyu', 'Limuru',
]

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'

export default function OnboardingPage() {
  const router = useRouter()
  const { user, isLoggedIn, isSeller } = useAuth()
  const [step, setStep] = useState(1)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [shopCreated, setShopCreated] = useState<any>(null)

  const bannerInput = useRef<HTMLInputElement>(null)
  const prodFileInputs = useRef<(HTMLInputElement | null)[]>([])

  const [shop, setShop] = useState({
    name: '', description: '', category: '', location_area: '',
    phone: '', banner_image: '', banner_file: null as File | null,
    fulfillment_modes: [] as string[],
    delivery_radius_km: '', delivery_fee: '',
    operating_hours: '', pickup_address: '',
    payment_methods: [] as string[],
  })

  const [products, setProducts] = useState<Array<{
    title: string; price: string; stock: string; description: string;
    image_url: string; image_file: File | null; uploading: boolean;
  }>>([])

  useEffect(() => {
    if (!isLoggedIn) return
    if (user && user.role !== 'seller' && user.role !== 'admin') {
      router.push('/')
    }
  }, [isLoggedIn, user, router])

  const updateShop = (field: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) =>
    setShop(prev => ({ ...prev, [field]: e.target.value }))

  const toggleArray = (field: 'fulfillment_modes' | 'payment_methods', value: string) => {
    setShop(prev => ({
      ...prev,
      [field]: prev[field].includes(value)
        ? prev[field].filter(v => v !== value)
        : [...prev[field], value],
    }))
  }

  const handleBannerUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setError('')
    const url = await uploadToCloudinary(file)
    if (url) {
      setShop(prev => ({ ...prev, banner_image: url, banner_file: file }))
    }
  }

  const uploadToCloudinary = async (file: File): Promise<string | null> => {
    const token = localStorage.getItem('ikobiz_token')
    const fd = new FormData()
    fd.append('file', file)
    try {
      const r = await fetch(`${API_BASE}/upload/image`, {
        method: 'POST',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: fd,
      })
      if (!r.ok) {
        const errData = await r.json().catch(() => ({}))
        throw new Error(errData.detail || 'Upload failed')
      }
      const data = await r.json()
      return data.url
    } catch (err: any) {
      setError(err.message || 'Image upload failed')
      return null
    }
  }

  const addProduct = () => {
    setProducts(prev => [...prev, {
      title: '', price: '', stock: '1', description: '',
      image_url: '', image_file: null, uploading: false,
    }])
  }

  const updateProduct = (idx: number, field: string, value: string) => {
    setProducts(prev => prev.map((p, i) => i === idx ? { ...p, [field]: value } : p))
  }

  const removeProduct = (idx: number) => {
    setProducts(prev => prev.filter((_, i) => i !== idx))
  }

  const handleProductImage = async (idx: number, file: File) => {
    setProducts(prev => prev.map((p, i) => i === idx ? { ...p, image_file: file, uploading: true } : p))
    const url = await uploadToCloudinary(file)
    if (url) {
      setProducts(prev => prev.map((p, i) => i === idx ? { ...p, image_url: url, uploading: false } : p))
    } else {
      setProducts(prev => prev.map((p, i) => i === idx ? { ...p, uploading: false } : p))
    }
  }

  const canProceed = (): string | null => {
    if (step === 1) {
      if (!shop.name.trim()) return 'Shop name is required'
      if (!shop.category) return 'Please select a category'
      if (!shop.location_area) return 'Please enter your location area'
    }
    if (step === 2) {
      if (shop.fulfillment_modes.length === 0) return 'Select at least one fulfillment mode'
      if (shop.fulfillment_modes.includes('seller_delivery') && !shop.delivery_radius_km) return 'Enter delivery radius'
    }
    if (step === 3) {
      if (shop.payment_methods.length === 0) return 'Select at least one payment method'
    }
    return null
  }

  const handleNext = () => {
    const err = canProceed()
    if (err) { setError(err); return }
    setError('')
    setStep(prev => Math.min(prev + 1, 4))
  }

  const handlePrev = () => {
    setError('')
    setStep(prev => Math.max(prev - 1, 1))
  }

  const handleSubmit = async () => {
    setError('')
    setSubmitting(true)
    try {
      const shopData = {
        name: shop.name,
        description: shop.description || null,
        category: shop.category || null,
        location_area: shop.location_area || null,
        phone: shop.phone || null,
        banner_image: shop.banner_image || null,
        fulfillment_modes: shop.fulfillment_modes.join(',') || null,
        delivery_radius_km: shop.delivery_radius_km ? Number(shop.delivery_radius_km) : null,
        delivery_fee: shop.delivery_fee ? Number(shop.delivery_fee) : null,
        operating_hours: shop.operating_hours || null,
        pickup_address: shop.pickup_address || null,
        payment_methods: shop.payment_methods.join(',') || null,
      }

      const created = await api.post('/shops', shopData, true)
      setShopCreated(created)

      for (const p of products) {
        if (p.title.trim()) {
          await api.post(`/shops/${created.id}/products`, {
            title: p.title,
            price: Number(p.price),
            stock: Number(p.stock) || 1,
            description: p.description || null,
            image_url: p.image_url || null,
            category: shop.category || null,
            status: 'active',
          }, true).catch(err => {
            console.error('Failed to create product:', err)
          })
        }
      }

      router.push('/dashboard?onboarded=1')
    } catch (err: any) {
      setError(err?.message || 'Failed to create shop')
    } finally {
      setSubmitting(false)
    }
  }

  if (!isLoggedIn) {
    return (
      <div className="auth-page">
        <div className="auth-card" style={{ textAlign: 'center' }}>
          <h1>Get Started</h1>
          <p className="subtitle">Log in to create your shop</p>
          <Link href="/auth/login" className="btn btn-primary" style={{ width: '100%', justifyContent: 'center' }}>Login</Link>
        </div>
      </div>
    )
  }

  return (
    <div style={{
      minHeight: '100vh', background: 'var(--gray-50)',
      display: 'flex', flexDirection: 'column',
    }}>
      {/* Top bar */}
      <header style={{
        background: 'white', borderBottom: '1px solid var(--gray-200)',
        padding: '1rem', textAlign: 'center',
      }}>
        <Link href="/" style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--primary)', textDecoration: 'none' }}>
          Ikobiz<span style={{ color: 'var(--secondary)' }}>.</span>
        </Link>
        <span style={{ fontSize: '0.85rem', color: 'var(--gray-400)', marginLeft: '0.75rem' }}>Seller Onboarding</span>
      </header>

      {/* Step indicator */}
      <div style={{
        display: 'flex', justifyContent: 'center', gap: '0.5rem',
        padding: '1.5rem 1rem 0', maxWidth: 700, margin: '0 auto',
        width: '100%',
      }}>
        {STEPS.map(s => {
          const isActive = s.num === step
          const isDone = s.num < step
          return (
            <div key={s.num} style={{
              flex: 1, display: 'flex', flexDirection: 'column',
              alignItems: 'center', gap: '0.35rem',
              opacity: isActive || isDone ? 1 : 0.4,
              transition: '0.3s',
            }}>
              <div style={{
                width: 36, height: 36, borderRadius: '50%',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '0.85rem', fontWeight: 700,
                background: isDone ? 'var(--secondary)' : isActive ? 'var(--primary)' : 'var(--gray-200)',
                color: 'white',
                transition: '0.3s',
              }}>
                {isDone ? '✓' : s.icon}
              </div>
              <span style={{
                fontSize: '0.7rem', fontWeight: isActive ? 600 : 400,
                color: isActive ? 'var(--gray-800)' : 'var(--gray-500)',
                textAlign: 'center', lineHeight: 1.2,
              }}>
                {s.label}
              </span>
            </div>
          )
        })}
      </div>
      {/* Progress bar */}
      <div style={{ maxWidth: 700, margin: '0.75rem auto 0', width: '100%', padding: '0 1rem' }}>
        <div style={{ height: 4, background: 'var(--gray-200)', borderRadius: 2, overflow: 'hidden' }}>
          <div style={{
            height: '100%', width: `${((step - 1) / 3) * 100}%`,
            background: 'linear-gradient(90deg, var(--primary), var(--secondary))',
            borderRadius: 2, transition: '0.4s ease',
          }} />
        </div>
      </div>

      {/* Form */}
      <div style={{ flex: 1, display: 'flex', justifyContent: 'center', padding: '1.5rem 1rem 3rem' }}>
        <div style={{
          width: '100%', maxWidth: 600,
          background: 'white', borderRadius: 'var(--radius-xl)',
          boxShadow: 'var(--shadow-lg)', padding: '2rem',
        }}>
          {error && (
            <div style={{
              background: '#fef2f2', color: '#991b1b', padding: '0.75rem 1rem',
              borderRadius: 'var(--radius)', marginBottom: '1.25rem',
              fontSize: '0.88rem', fontWeight: 500,
            }}>
              {error}
            </div>
          )}

          {step === 1 && (
            <div style={{ animation: 'fadeIn 0.3s ease' }}>
              <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: '0.25rem' }}>
                Tell us about your shop
              </h2>
              <p style={{ fontSize: '0.88rem', color: 'var(--gray-500)', marginBottom: '1.5rem' }}>
                This is what customers will see when they discover you.
              </p>

              {/* Banner image */}
              <div className="form-group">
                <label>Shop Banner</label>
                <div
                  onClick={() => bannerInput.current?.click()}
                  style={{
                    border: '2px dashed var(--gray-300)', borderRadius: 'var(--radius)',
                    padding: '1.5rem', textAlign: 'center', cursor: 'pointer',
                    background: shop.banner_image ? 'transparent' : 'var(--gray-50)',
                    transition: '0.2s', position: 'relative', overflow: 'hidden',
                    minHeight: 120, display: 'flex', alignItems: 'center', justifyContent: 'center',
                  }}
                >
                  {shop.banner_image ? (
                    <img src={shop.banner_image} alt="Banner" style={{
                      width: '100%', height: 120, objectFit: 'cover', borderRadius: 'var(--radius)',
                    }} />
                  ) : (
                    <div style={{ color: 'var(--gray-400)' }}>
                      <div style={{ fontSize: '1.5rem', marginBottom: '0.3rem' }}>🖼️</div>
                      <div style={{ fontSize: '0.85rem' }}>Click to upload banner image</div>
                    </div>
                  )}
                  <input ref={bannerInput} type="file" accept="image/jpeg,image/png,image/webp" onChange={handleBannerUpload} style={{ display: 'none' }} />
                </div>
                {shop.banner_image && (
                  <button
                    onClick={() => { setShop(prev => ({ ...prev, banner_image: '' })); if (bannerInput.current) bannerInput.current.value = '' }}
                    className="btn btn-sm btn-outline"
                    style={{ marginTop: '0.4rem', fontSize: '0.75rem' }}
                  >Remove</button>
                )}
              </div>

              <div className="form-group">
                <label>Shop Name *</label>
                <input type="text" value={shop.name} onChange={updateShop('name')} required
                  placeholder="e.g. Mama Mboga Fresh Produce"
                  style={{ fontSize: '1rem', padding: '0.75rem 1rem' }}
                />
              </div>

              <div className="form-group">
                <label>Description</label>
                <textarea value={shop.description} onChange={updateShop('description')}
                  rows={3} placeholder="Tell customers what you sell..."
                  style={{ fontSize: '0.95rem', padding: '0.75rem 1rem' }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="form-group">
                  <label>Category *</label>
                  <select value={shop.category} onChange={updateShop('category')}
                    style={{ fontSize: '0.95rem', padding: '0.75rem 1rem' }}
                  >
                    <option value="">Select category</option>
                    {CATEGORIES.map(c => (
                      <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label>Location Area *</label>
                  <input
                    type="text" value={shop.location_area} onChange={updateShop('location_area')}
                    placeholder="e.g. Westlands, Kawangware"
                    list="areas"
                    style={{ fontSize: '0.95rem', padding: '0.75rem 1rem' }}
                  />
                  <datalist id="areas">
                    {KENYAN_AREAS.map(a => <option key={a} value={a} />)}
                  </datalist>
                </div>
              </div>

              <div className="form-group">
                <label>Phone Number</label>
                <input type="tel" value={shop.phone} onChange={updateShop('phone')}
                  placeholder="e.g. 254712345678"
                  style={{ fontSize: '0.95rem', padding: '0.75rem 1rem' }}
                />
                <div style={{ fontSize: '0.75rem', color: 'var(--gray-400)', marginTop: '0.25rem' }}>
                  Used for WhatsApp delivery coordination with customers
                </div>
              </div>
            </div>
          )}

          {step === 2 && (
            <div style={{ animation: 'fadeIn 0.3s ease' }}>
              <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: '0.25rem' }}>
                How will you fulfill orders?
              </h2>
              <p style={{ fontSize: '0.88rem', color: 'var(--gray-500)', marginBottom: '1.5rem' }}>
                Set up how customers receive their purchases.
              </p>

              <div className="form-group">
                <label>Fulfillment Modes *</label>
                <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
                  {[
                    { value: 'pickup', label: '🏪 Pickup', desc: 'Customer collects from shop' },
                    { value: 'seller_delivery', label: '🚚 Delivery', desc: 'You deliver to customer' },
                  ].map(opt => (
                    <label key={opt.value} style={{
                      flex: 1, minWidth: 180, cursor: 'pointer',
                      padding: '1rem', borderRadius: 'var(--radius)',
                      border: `2px solid ${shop.fulfillment_modes.includes(opt.value) ? 'var(--primary)' : 'var(--gray-200)'}`,
                      background: shop.fulfillment_modes.includes(opt.value) ? 'var(--primary-light)' : 'white',
                      transition: '0.2s',
                    }}>
                      <input
                        type="checkbox"
                        checked={shop.fulfillment_modes.includes(opt.value)}
                        onChange={() => toggleArray('fulfillment_modes', opt.value)}
                        style={{ display: 'none' }}
                      />
                      <div style={{ fontSize: '1rem', fontWeight: 600 }}>{opt.label}</div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--gray-500)', marginTop: '0.2rem' }}>{opt.desc}</div>
                    </label>
                  ))}
                </div>
              </div>

              {shop.fulfillment_modes.includes('seller_delivery') && (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginTop: '0.5rem' }}>
                  <div className="form-group">
                    <label>Delivery Radius (km)</label>
                    <input type="number" value={shop.delivery_radius_km} onChange={updateShop('delivery_radius_km')}
                      min={0} step={0.5} placeholder="e.g. 10" />
                  </div>
                  <div className="form-group">
                    <label>Delivery Fee (KES)</label>
                    <input type="number" value={shop.delivery_fee} onChange={updateShop('delivery_fee')}
                      min={0} placeholder="e.g. 200" />
                  </div>
                </div>
              )}

              {shop.fulfillment_modes.includes('pickup') && (
                <div className="form-group">
                  <label>Pickup Address</label>
                  <textarea value={shop.pickup_address} onChange={updateShop('pickup_address')}
                    rows={2} placeholder="e.g. Moi Avenue, Ambassador Building, G4, Nairobi" />
                </div>
              )}

              <div className="form-group">
                <label>Operating Hours (optional)</label>
                <input type="text" value={shop.operating_hours} onChange={updateShop('operating_hours')}
                  placeholder='e.g. Mon-Fri 8am-6pm, Sat 9am-3pm' />
                <div style={{ fontSize: '0.75rem', color: 'var(--gray-400)', marginTop: '0.25rem' }}>
                  Let customers know when you&apos;re open for business
                </div>
              </div>
            </div>
          )}

          {step === 3 && (
            <div style={{ animation: 'fadeIn 0.3s ease' }}>
              <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: '0.25rem' }}>
                How will customers pay?
              </h2>
              <p style={{ fontSize: '0.88rem', color: 'var(--gray-500)', marginBottom: '1.5rem' }}>
                Select the payment options you support.
              </p>

              <div className="form-group">
                <label>Payment Methods *</label>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {[
                    { value: 'mpesa', label: '💳 M-Pesa', desc: 'Customers pay to your M-Pesa till/paybill' },
                    { value: 'cash_on_delivery', label: '💵 Cash on Delivery', desc: 'Customer pays when they receive the order' },
                    { value: 'bank_transfer', label: '🏦 Bank Transfer', desc: 'Direct bank deposit or transfer' },
                  ].map(opt => (
                    <label key={opt.value} style={{
                      display: 'flex', alignItems: 'center', gap: '0.75rem',
                      padding: '1rem', borderRadius: 'var(--radius)',
                      border: `2px solid ${shop.payment_methods.includes(opt.value) ? 'var(--primary)' : 'var(--gray-200)'}`,
                      background: shop.payment_methods.includes(opt.value) ? 'var(--primary-light)' : 'white',
                      cursor: 'pointer', transition: '0.2s',
                    }}>
                      <input
                        type="checkbox"
                        checked={shop.payment_methods.includes(opt.value)}
                        onChange={() => toggleArray('payment_methods', opt.value)}
                        style={{ display: 'none' }}
                      />
                      <div style={{ flex: 1 }}>
                        <div style={{ fontWeight: 600, fontSize: '0.95rem' }}>{opt.label}</div>
                        <div style={{ fontSize: '0.8rem', color: 'var(--gray-500)' }}>{opt.desc}</div>
                      </div>
                      <div style={{
                        width: 22, height: 22, borderRadius: 4,
                        border: `2px solid ${shop.payment_methods.includes(opt.value) ? 'var(--primary)' : 'var(--gray-300)'}`,
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        background: shop.payment_methods.includes(opt.value) ? 'var(--primary)' : 'transparent',
                        color: 'white', fontSize: '0.75rem', fontWeight: 700,
                        flexShrink: 0,
                      }}>
                        {shop.payment_methods.includes(opt.value) ? '✓' : ''}
                      </div>
                    </label>
                  ))}
                </div>
              </div>
            </div>
          )}

          {step === 4 && (
            <div style={{ animation: 'fadeIn 0.3s ease' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem' }}>
                <div>
                  <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: '0.25rem' }}>
                    Add your products
                  </h2>
                  <p style={{ fontSize: '0.88rem', color: 'var(--gray-500)' }}>
                    List what you&apos;re selling. You can add more later.
                  </p>
                </div>
                <button onClick={addProduct} className="btn btn-sm btn-outline" style={{ flexShrink: 0 }}>
                  + Add Item
                </button>
              </div>

              {products.length === 0 && (
                <div style={{
                  textAlign: 'center', padding: '2rem', borderRadius: 'var(--radius)',
                  border: '2px dashed var(--gray-300)', background: 'var(--gray-50)',
                }}>
                  <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>📦</div>
                  <p style={{ fontWeight: 600, marginBottom: '0.3rem' }}>No products yet</p>
                  <p style={{ fontSize: '0.85rem', color: 'var(--gray-500)' }}>
                    Click &quot;Add Item&quot; to list your first product
                  </p>
                </div>
              )}

              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                {products.map((p, idx) => (
                  <div key={idx} style={{
                    border: '1px solid var(--gray-200)', borderRadius: 'var(--radius-lg)',
                    padding: '1.25rem', position: 'relative',
                  }}>
                    <button
                      onClick={() => removeProduct(idx)}
                      style={{
                        position: 'absolute', top: '0.5rem', right: '0.5rem',
                        background: 'var(--danger)', color: 'white', border: 'none',
                        width: 24, height: 24, borderRadius: '50%',
                        cursor: 'pointer', fontSize: '0.8rem', display: 'flex',
                        alignItems: 'center', justifyContent: 'center',
                        lineHeight: 1,
                      }}
                      title="Remove product"
                    >×</button>
                    <div style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--gray-500)', marginBottom: '0.75rem' }}>
                      Product #{idx + 1}
                    </div>

                    <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start' }}>
                      <div style={{ flexShrink: 0 }}>
                        <div
                          onClick={() => prodFileInputs.current[idx]?.click()}
                          style={{
                            width: 80, height: 80, borderRadius: 'var(--radius)',
                            border: '2px dashed var(--gray-300)',
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            cursor: 'pointer', overflow: 'hidden',
                            background: p.image_url ? 'transparent' : 'var(--gray-50)',
                          }}
                        >
                          {p.image_url ? (
                            <img src={p.image_url} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                          ) : p.uploading ? (
                            <span style={{ fontSize: '0.7rem', color: 'var(--gray-400)' }}>...</span>
                          ) : (
                            <span style={{ fontSize: '1.5rem' }}>📷</span>
                          )}
                        </div>
                        <input
                          ref={el => { prodFileInputs.current[idx] = el }}
                          type="file"
                          accept="image/jpeg,image/png,image/webp"
                          onChange={e => { const f = e.target.files?.[0]; if (f) handleProductImage(idx, f) }}
                          style={{ display: 'none' }}
                        />
                      </div>
                      <div style={{ flex: 1 }}>
                        <input
                          type="text"
                          value={p.title}
                          onChange={e => updateProduct(idx, 'title', e.target.value)}
                          placeholder="Product name *"
                          style={{
                            width: '100%', padding: '0.55rem 0.75rem', marginBottom: '0.5rem',
                            border: '2px solid var(--gray-200)', borderRadius: 'var(--radius)',
                            fontSize: '0.9rem', fontWeight: 600,
                          }}
                        />
                        <textarea
                          value={p.description}
                          onChange={e => updateProduct(idx, 'description', e.target.value)}
                          placeholder="Brief description"
                          rows={2}
                          style={{
                            width: '100%', padding: '0.5rem 0.75rem', marginBottom: '0.5rem',
                            border: '1px solid var(--gray-200)', borderRadius: 'var(--radius)',
                            fontSize: '0.82rem', resize: 'vertical',
                          }}
                        />
                        <div style={{ display: 'flex', gap: '0.5rem' }}>
                          <div style={{ flex: 1 }}>
                            <div style={{ fontSize: '0.72rem', color: 'var(--gray-500)', marginBottom: '0.2rem' }}>Price (KES) *</div>
                            <input
                              type="number" min={0}
                              value={p.price}
                              onChange={e => updateProduct(idx, 'price', e.target.value)}
                              placeholder="0"
                              style={{
                                width: '100%', padding: '0.5rem 0.65rem',
                                border: '1px solid var(--gray-200)', borderRadius: 'var(--radius)',
                                fontSize: '0.9rem',
                              }}
                            />
                          </div>
                          <div style={{ flex: 1 }}>
                            <div style={{ fontSize: '0.72rem', color: 'var(--gray-500)', marginBottom: '0.2rem' }}>Stock</div>
                            <input
                              type="number" min={0}
                              value={p.stock}
                              onChange={e => updateProduct(idx, 'stock', e.target.value)}
                              placeholder="1"
                              style={{
                                width: '100%', padding: '0.5rem 0.65rem',
                                border: '1px solid var(--gray-200)', borderRadius: 'var(--radius)',
                                fontSize: '0.9rem',
                              }}
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {products.length > 0 && (
                <button onClick={addProduct} className="btn btn-outline" style={{ width: '100%', justifyContent: 'center', marginTop: '1rem' }}>
                  + Add Another Product
                </button>
              )}
            </div>
          )}

          {/* Navigation */}
          <div style={{
            display: 'flex', justifyContent: 'space-between', gap: '0.75rem',
            marginTop: '2rem', paddingTop: '1.25rem',
            borderTop: '1px solid var(--gray-100)',
          }}>
            {step > 1 ? (
              <button onClick={handlePrev} className="btn btn-outline" disabled={submitting}>
                ← Back
              </button>
            ) : (
              <div />
            )}
            {step < 4 ? (
              <button onClick={handleNext} className="btn btn-primary" style={{ padding: '0.7rem 2rem' }}>
                Continue →
              </button>
            ) : (
              <button onClick={handleSubmit} className="btn btn-secondary" disabled={submitting}
                style={{ padding: '0.7rem 2rem', fontSize: '1rem' }}>
                {submitting ? 'Creating Your Shop...' : '🚀 Launch My Shop'}
              </button>
            )}
          </div>
        </div>
      </div>

      <style jsx>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(8px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  )
}
