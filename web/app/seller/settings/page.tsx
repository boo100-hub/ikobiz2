'use client'

import { useEffect, useState, useRef } from 'react'
import { api, type Shop } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'
import { Skeleton } from '@/components/ui/skeleton'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Store,
  MapPin,
  Truck,
  Clock,
  CreditCard,
  Phone,
  Save,
} from 'lucide-react'
import { toast } from 'sonner'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'

const FULFILLMENT_OPTIONS = [
  { value: 'pickup', label: 'Pickup' },
  { value: 'seller_delivery', label: 'Delivery' },
]

const PAYMENT_OPTIONS = [
  { value: 'mpesa', label: 'M-Pesa' },
  { value: 'cash_on_delivery', label: 'Cash on Delivery' },
  { value: 'bank_transfer', label: 'Bank Transfer' },
]

const CATEGORIES = [
  'food', 'electronics', 'fashion', 'health', 'home',
  'sports', 'services', 'agriculture', 'other',
]

export default function SellerSettingsPage() {
  const [shop, setShop] = useState<Shop | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [uploading, setUploading] = useState(false)
  const bannerInput = useRef<HTMLInputElement>(null)
  const [form, setForm] = useState({
    name: '',
    description: '',
    banner_image: '',
    category: '',
    location_area: '',
    latitude: '',
    longitude: '',
    fulfillment_modes: [] as string[],
    delivery_radius_km: '',
    delivery_fee: '',
    operating_hours: '',
    payment_methods: [] as string[],
    pickup_address: '',
    phone: '',
  })

  useEffect(() => {
    api.get('/seller/shops', true)
      .then((data) => {
        if (Array.isArray(data) && data.length > 0) {
          const s = data[0]
          setShop(s)
          setForm({
            name: s.name || '',
            description: s.description || '',
            banner_image: s.banner_image || '',
            category: s.category || '',
            location_area: s.location_area || '',
            latitude: (s as any).latitude?.toString() || '',
            longitude: (s as any).longitude?.toString() || '',
            fulfillment_modes: (s.fulfillment_modes || '').split(',').filter(Boolean),
            delivery_radius_km: s.delivery_radius_km?.toString() || '',
            delivery_fee: s.delivery_fee?.toString() || '',
            operating_hours: s.operating_hours || '',
            payment_methods: (s.payment_methods || '').split(',').filter(Boolean),
            pickup_address: s.pickup_address || '',
            phone: s.phone || '',
          })
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const toggleArray = (field: 'fulfillment_modes' | 'payment_methods', value: string) => {
    setForm(prev => ({
      ...prev,
      [field]: prev[field].includes(value)
        ? prev[field].filter(v => v !== value)
        : [...prev[field], value],
    }))
  }

  const update = (field: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
    setForm(prev => ({ ...prev, [field]: e.target.value }))

  const handleBannerUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    try {
      const token = localStorage.getItem('ikobiz_token')
      const fd = new FormData()
      fd.append('file', file)
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
      setForm(prev => ({ ...prev, banner_image: data.url }))
    } catch (err: any) {
      toast.error(err.message || 'Image upload failed')
    } finally {
      setUploading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!shop?.id) return
    setSaving(true)
    try {
      await api.put(`/shops/${shop.id}`, {
        name: form.name,
        description: form.description || null,
        banner_image: form.banner_image || null,
        category: form.category || null,
        location_area: form.location_area || null,
        latitude: form.latitude ? Number(form.latitude) : null,
        longitude: form.longitude ? Number(form.longitude) : null,
        fulfillment_modes: form.fulfillment_modes.join(',') || null,
        delivery_radius_km: form.delivery_radius_km ? Number(form.delivery_radius_km) : null,
        delivery_fee: form.delivery_fee ? Number(form.delivery_fee) : null,
        operating_hours: form.operating_hours || null,
        payment_methods: form.payment_methods.join(',') || null,
        pickup_address: form.pickup_address || null,
        phone: form.phone || null,
      }, true)
      toast.success('Shop settings saved successfully')
      const data = await api.get('/seller/shops', true)
      if (Array.isArray(data) && data.length > 0) {
        const s = data[0]
        setShop(s)
        setForm({
          name: s.name || '',
          description: s.description || '',
          banner_image: s.banner_image || '',
          category: s.category || '',
          location_area: s.location_area || '',
          latitude: (s as any).latitude?.toString() || '',
          longitude: (s as any).longitude?.toString() || '',
          fulfillment_modes: (s.fulfillment_modes || '').split(',').filter(Boolean),
          delivery_radius_km: s.delivery_radius_km?.toString() || '',
          delivery_fee: s.delivery_fee?.toString() || '',
          operating_hours: s.operating_hours || '',
          payment_methods: (s.payment_methods || '').split(',').filter(Boolean),
          pickup_address: s.pickup_address || '',
          phone: s.phone || '',
        })
      }
    } catch (err: any) {
      toast.error(err?.message || 'Failed to save shop settings')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto py-8 px-4 space-y-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-4 w-72" />
        <div className="space-y-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-10 w-full" />
          ))}
        </div>
      </div>
    )
  }

  if (!shop) {
    return (
      <div className="max-w-2xl mx-auto py-8 px-4 text-center">
        <Store className="mx-auto h-12 w-12 text-muted-foreground" />
        <h2 className="mt-4 text-lg font-semibold">No shop found</h2>
        <p className="text-muted-foreground text-sm mt-1">
          You don&apos;t have a shop yet. Create one to get started.
        </p>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto py-8 px-4">
      <div className="flex items-center gap-3 mb-6">
        <Store className="h-6 w-6" />
        <div>
          <h1 className="text-2xl font-bold">Shop Settings</h1>
          <p className="text-sm text-muted-foreground">
            Manage your shop details, fulfillment, and payment options.
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-8">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Store className="h-5 w-5" /> Basic Information
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-2">
              <Label htmlFor="name">Shop Name</Label>
              <Input id="name" value={form.name} onChange={update('name')} required />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="description">Description</Label>
              <Textarea id="description" value={form.description} onChange={update('description')} rows={3} placeholder="Describe your shop..." />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label htmlFor="category">Category</Label>
                <Select value={form.category} onValueChange={(v) => setForm(prev => ({ ...prev, category: v }))}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select category" />
                  </SelectTrigger>
                  <SelectContent>
                    {CATEGORIES.map(c => (
                      <SelectItem key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="grid gap-2">
                <Label htmlFor="location_area">
                  <span className="flex items-center gap-1"><MapPin className="h-3.5 w-3.5" /> Location Area</span>
                </Label>
                <Input id="location_area" value={form.location_area} onChange={update('location_area')} placeholder="e.g. Westlands" />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label htmlFor="latitude">
                  <span className="flex items-center gap-1"><MapPin className="h-3.5 w-3.5" /> Latitude</span>
                </Label>
                <Input id="latitude" type="number" step="any" value={form.latitude} onChange={update('latitude')} placeholder="-1.286389" />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="longitude">Longitude</Label>
                <Input id="longitude" type="number" step="any" value={form.longitude} onChange={update('longitude')} placeholder="36.817223" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Truck className="h-5 w-5" /> Fulfillment
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-3">
              <Label>Fulfillment Modes</Label>
              <div className="flex gap-4">
                {FULFILLMENT_OPTIONS.map(opt => (
                  <label key={opt.value} className="flex items-center gap-2 cursor-pointer">
                    <Checkbox
                      checked={form.fulfillment_modes.includes(opt.value)}
                      onCheckedChange={() => toggleArray('fulfillment_modes', opt.value)}
                    />
                    {opt.label}
                  </label>
                ))}
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label htmlFor="delivery_radius_km">Delivery Radius (km)</Label>
                <Input id="delivery_radius_km" type="number" min={0} step={0.5} value={form.delivery_radius_km} onChange={update('delivery_radius_km')} placeholder="e.g. 10" />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="delivery_fee">Delivery Fee (KES)</Label>
                <Input id="delivery_fee" type="number" min={0} value={form.delivery_fee} onChange={update('delivery_fee')} placeholder="e.g. 200" />
              </div>
            </div>
            <div className="grid gap-2">
              <Label htmlFor="operating_hours">
                <span className="flex items-center gap-1"><Clock className="h-3.5 w-3.5" /> Operating Hours</span>
              </Label>
              <Input id="operating_hours" value={form.operating_hours} onChange={update('operating_hours')} placeholder='{"mon-fri":"8:00-18:00","sat":"9:00-15:00"}' />
              <p className="text-xs text-muted-foreground">JSON format: day-range to hours.</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <CreditCard className="h-5 w-5" /> Payment & Contact
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-3">
              <Label>Payment Methods</Label>
              <div className="flex flex-wrap gap-4">
                {PAYMENT_OPTIONS.map(opt => (
                  <label key={opt.value} className="flex items-center gap-2 cursor-pointer">
                    <Checkbox
                      checked={form.payment_methods.includes(opt.value)}
                      onCheckedChange={() => toggleArray('payment_methods', opt.value)}
                    />
                    {opt.label}
                  </label>
                ))}
              </div>
            </div>
            <div className="grid gap-2">
              <Label htmlFor="pickup_address">Pickup Address</Label>
              <Textarea id="pickup_address" value={form.pickup_address} onChange={update('pickup_address')} rows={2} placeholder="e.g. Moi Avenue, Ambassador Building, Nairobi" />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="phone">
                <span className="flex items-center gap-1"><Phone className="h-3.5 w-3.5" /> Contact Phone</span>
              </Label>
              <Input id="phone" type="tel" value={form.phone} onChange={update('phone')} placeholder="e.g. 254700000001" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Store className="h-5 w-5" /> Shop Banner
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div
              onClick={() => bannerInput.current?.click()}
              className="relative flex items-center justify-center overflow-hidden rounded-lg border-2 border-dashed p-4 cursor-pointer min-h-[100px]"
            >
              {form.banner_image ? (
                <img src={form.banner_image} alt="Banner" className="w-full h-24 object-cover rounded-md" />
              ) : (
                <div className="text-center text-muted-foreground text-sm">
                  {uploading ? 'Uploading...' : 'Click to upload banner image'}
                </div>
              )}
              <input ref={bannerInput} type="file" accept="image/jpeg,image/png,image/webp" onChange={handleBannerUpload} className="hidden" />
            </div>
            {form.banner_image && (
              <div className="flex gap-2">
                <Input type="url" value={form.banner_image} onChange={update('banner_image')} placeholder="Or paste image URL" className="text-sm" />
                <Button type="button" variant="outline" size="sm" onClick={() => setForm(prev => ({ ...prev, banner_image: '' }))}>
                  Remove
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        <div className="flex gap-3">
          <Button type="submit" disabled={saving}>
            <Save className="h-4 w-4" />
            {saving ? 'Saving...' : 'Save Settings'}
          </Button>
        </div>
      </form>
    </div>
  )
}
