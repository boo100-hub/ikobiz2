"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Store,
  MapPin,
  Truck,
  CreditCard,
  CheckCircle,
  ArrowRight,
  ArrowLeft,
  Upload,
  Sparkles,
} from "lucide-react"
import { toast } from "sonner"
import { api } from "@/lib/api"
import { useAuth } from "@/lib/auth"

const STEPS = [
  { id: 1, title: "Shop Info", icon: Store },
  { id: 2, title: "Location", icon: MapPin },
  { id: 3, title: "Fulfillment", icon: Truck },
  { id: 4, title: "Complete", icon: CheckCircle },
]

const CATEGORIES = [
  { value: "electronics", label: "Electronics" },
  { value: "fashion", label: "Fashion" },
  { value: "home", label: "Home & Kitchen" },
  { value: "groceries", label: "Groceries" },
  { value: "beauty", label: "Beauty" },
  { value: "sports", label: "Sports" },
  { value: "books", label: "Books & Stationery" },
  { value: "services", label: "Services" },
  { value: "agriculture", label: "Agriculture" },
  { value: "other", label: "Other" },
]

const KENYAN_AREAS = [
  "Nairobi CBD", "Westlands", "Kilimani", "Karen", "Langata",
  "Eastlands", "South B", "South C", "Ngong Road", "Thika Road",
  "Mombasa Island", "Nyali", "Bamburi", "Kisumu CBD", "Milimani",
  "Nakuru CBD", "Eldoret", "Rongai", "Kawangware", "Githurai",
  "Kitengela", "Athi River", "Ruaka", "Kikuyu", "Limuru",
]

const PAYMENT_METHODS = [
  { value: "mpesa", label: "M-Pesa" },
  { value: "cash_on_delivery", label: "Cash on Delivery" },
  { value: "bank_transfer", label: "Bank Transfer" },
]

export default function SellerOnboardingPage() {
  const router = useRouter()
  const { user, isLoggedIn } = useAuth()
  const [step, setStep] = useState(1)
  const [submitting, setSubmitting] = useState(false)

  const [shop, setShop] = useState({
    name: "",
    category: "",
    description: "",
    location_area: "",
    pickup_address: "",
    phone: "",
    hasDelivery: true,
    hasPickup: true,
    delivery_fee: "",
    delivery_radius_km: "",
    operating_hours: "",
    payment_methods: [] as string[],
  })

  useEffect(() => {
    if (!isLoggedIn) return
    if (user && user.role !== "seller" && user.role !== "admin") {
      router.push("/")
    }
  }, [isLoggedIn, user, router])

  const progress = ((step - 1) / (STEPS.length - 1)) * 100

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target
    setShop((prev) => ({ ...prev, [name]: value }))
  }

  const handleSelectChange = (field: string) => (value: string) => {
    setShop((prev) => ({ ...prev, [field]: value }))
  }

  const togglePaymentMethod = (value: string) => {
    setShop((prev) => ({
      ...prev,
      payment_methods: prev.payment_methods.includes(value)
        ? prev.payment_methods.filter((v) => v !== value)
        : [...prev.payment_methods, value],
    }))
  }

  const canProceed = (): string | null => {
    if (step === 1) {
      if (!shop.name.trim()) return "Shop name is required"
      if (!shop.category) return "Please select a category"
    }
    if (step === 2) {
      if (!shop.location_area.trim()) return "Please enter your location area"
    }
    if (step === 3) {
      if (!shop.hasDelivery && !shop.hasPickup)
        return "Select at least one fulfillment mode"
    }
    return null
  }

  const nextStep = () => {
    const err = canProceed()
    if (err) {
      toast.error(err)
      return
    }
    setStep((prev) => Math.min(prev + 1, STEPS.length))
  }

  const prevStep = () => {
    setStep((prev) => Math.max(prev - 1, 1))
  }

  const handleSubmit = async () => {
    setSubmitting(true)
    try {
      const fulfillmentModes: string[] = []
      if (shop.hasDelivery) fulfillmentModes.push("seller_delivery")
      if (shop.hasPickup) fulfillmentModes.push("pickup")

      const formData = {
        name: shop.name,
        category: shop.category,
        description: shop.description || null,
        location_area: shop.location_area || null,
        pickup_address: shop.pickup_address || null,
        phone: shop.phone || null,
        fulfillment_modes: fulfillmentModes.join(","),
        delivery_radius_km: shop.delivery_radius_km ? Number(shop.delivery_radius_km) : null,
        delivery_fee: shop.delivery_fee ? Number(shop.delivery_fee) : null,
        operating_hours: shop.operating_hours || null,
        payment_methods: shop.payment_methods.join(",") || null,
      }

      await api.post("/shops", formData, true)
      toast.success("Shop created successfully!")
      setStep(STEPS.length)
    } catch (err: any) {
      toast.error(err?.message || "Failed to create shop")
    } finally {
      setSubmitting(false)
    }
  }

  if (!isLoggedIn) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center space-y-4 max-w-sm mx-auto p-8">
          <div className="flex justify-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary">
              <Store className="h-6 w-6 text-primary-foreground" />
            </div>
          </div>
          <h1 className="text-2xl font-bold text-foreground">Get Started</h1>
          <p className="text-muted-foreground">Log in to create your shop</p>
          <Button asChild className="w-full">
            <Link href="/auth/login">Login</Link>
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-40 border-b border-border bg-card">
        <div className="mx-auto flex h-16 max-w-4xl items-center justify-between px-4">
          <Link href="/" className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary">
              <Store className="h-5 w-5 text-primary-foreground" />
            </div>
            <span className="text-lg font-bold text-foreground">Ikobiz</span>
          </Link>
          <span className="text-sm text-muted-foreground">
            Already have a shop?{" "}
            <Link href="/seller/dashboard" className="text-primary hover:underline">
              Go to Dashboard
            </Link>
          </span>
        </div>
      </header>

      <main className="mx-auto max-w-4xl px-4 py-8">
        {/* Progress */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-2xl font-bold text-foreground">Create Your Shop</h1>
            <span className="text-sm text-muted-foreground">
              Step {step} of {STEPS.length}
            </span>
          </div>

          {/* Progress Bar */}
          <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
            <div
              className="h-full bg-primary transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>

          {/* Step Indicators */}
          <div className="flex justify-between mt-4">
            {STEPS.map((s) => {
              const Icon = s.icon
              const isCompleted = step > s.id
              const isCurrent = step === s.id
              return (
                <div
                  key={s.id}
                  className={`flex flex-col items-center ${
                    s.id === 1 ? "items-start" : s.id === STEPS.length ? "items-end" : ""
                  }`}
                >
                  <div
                    className={`flex h-10 w-10 items-center justify-center rounded-full transition-colors ${
                      isCompleted
                        ? "bg-primary text-primary-foreground"
                        : isCurrent
                          ? "bg-primary/20 text-primary border-2 border-primary"
                          : "bg-muted text-muted-foreground"
                    }`}
                  >
                    {isCompleted ? (
                      <CheckCircle className="h-5 w-5" />
                    ) : (
                      <Icon className="h-5 w-5" />
                    )}
                  </div>
                  <span
                    className={`mt-2 text-xs hidden sm:block ${
                      isCurrent ? "text-primary font-medium" : "text-muted-foreground"
                    }`}
                  >
                    {s.title}
                  </span>
                </div>
              )
            })}
          </div>
        </div>

        {/* Step Content */}
        <div className="rounded-2xl border border-border bg-card p-6 md:p-8">
          {/* Step 1: Shop Info */}
          {step === 1 && (
            <div className="space-y-6">
              <div>
                <h2 className="text-xl font-semibold text-foreground">Shop Information</h2>
                <p className="text-muted-foreground mt-1">
                  Tell us about your business
                </p>
              </div>

              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Shop Name</Label>
                  <Input
                    id="name"
                    name="name"
                    placeholder="My Awesome Shop"
                    value={shop.name}
                    onChange={handleInputChange}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="category">Category</Label>
                  <Select
                    value={shop.category}
                    onValueChange={handleSelectChange("category")}
                  >
                    <SelectTrigger id="category" className="w-full">
                      <SelectValue placeholder="Select a category" />
                    </SelectTrigger>
                    <SelectContent>
                      {CATEGORIES.map((c) => (
                        <SelectItem key={c.value} value={c.value}>
                          {c.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="description">Description</Label>
                  <Textarea
                    id="description"
                    name="description"
                    rows={4}
                    placeholder="Tell customers what makes your shop special..."
                    value={shop.description}
                    onChange={handleInputChange}
                  />
                </div>

                <div className="space-y-2">
                  <Label>Shop Logo (Optional)</Label>
                  <div className="flex items-center gap-4">
                    <div className="flex h-20 w-20 items-center justify-center rounded-xl border-2 border-dashed border-border bg-muted">
                      <Store className="h-8 w-8 text-muted-foreground" />
                    </div>
                    <Button variant="outline" size="sm" className="gap-2" disabled>
                      <Upload className="h-4 w-4" />
                      Upload Logo
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Step 2: Location */}
          {step === 2 && (
            <div className="space-y-6">
              <div>
                <h2 className="text-xl font-semibold text-foreground">Location & Contact</h2>
                <p className="text-muted-foreground mt-1">
                  Where is your shop located?
                </p>
              </div>

              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="location_area">Location Area</Label>
                  <Input
                    id="location_area"
                    name="location_area"
                    placeholder="e.g. Westlands, Kawangware"
                    value={shop.location_area}
                    onChange={handleInputChange}
                    list="areas"
                  />
                  <datalist id="areas">
                    {KENYAN_AREAS.map((a) => (
                      <option key={a} value={a} />
                    ))}
                  </datalist>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="pickup_address">Pickup Address</Label>
                  <Input
                    id="pickup_address"
                    name="pickup_address"
                    placeholder="e.g. Moi Avenue, Ambassador Building, G4"
                    value={shop.pickup_address}
                    onChange={handleInputChange}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="phone">Phone Number</Label>
                  <Input
                    id="phone"
                    name="phone"
                    type="tel"
                    placeholder="+254 712 345 678"
                    value={shop.phone}
                    onChange={handleInputChange}
                  />
                  <p className="text-xs text-muted-foreground">
                    Used for WhatsApp delivery coordination with customers
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Step 3: Fulfillment */}
          {step === 3 && (
            <div className="space-y-6">
              <div>
                <h2 className="text-xl font-semibold text-foreground">
                  Fulfillment & Payments
                </h2>
                <p className="text-muted-foreground mt-1">
                  How will you deliver products and accept payments?
                </p>
              </div>

              <div className="space-y-6">
                <div className="space-y-4">
                  <h3 className="font-medium text-foreground flex items-center gap-2">
                    <Truck className="h-5 w-5 text-primary" />
                    Delivery Options
                  </h3>

                  <label className="flex items-center gap-3 cursor-pointer">
                    <Checkbox
                      checked={shop.hasDelivery}
                      onCheckedChange={(checked) =>
                        setShop((prev) => ({ ...prev, hasDelivery: checked === true }))
                      }
                    />
                    <span className="text-sm text-foreground">I offer delivery</span>
                  </label>

                  {shop.hasDelivery && (
                    <div className="ml-7 space-y-3">
                      <div className="grid gap-3 sm:grid-cols-2">
                        <div className="space-y-2">
                          <Label htmlFor="delivery_fee">Delivery Fee (KES)</Label>
                          <Input
                            id="delivery_fee"
                            name="delivery_fee"
                            type="number"
                            min={0}
                            placeholder="e.g. 200"
                            value={shop.delivery_fee}
                            onChange={handleInputChange}
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="delivery_radius_km">Delivery Radius (km)</Label>
                          <Input
                            id="delivery_radius_km"
                            name="delivery_radius_km"
                            type="number"
                            min={0}
                            step={0.5}
                            placeholder="e.g. 10"
                            value={shop.delivery_radius_km}
                            onChange={handleInputChange}
                          />
                        </div>
                      </div>
                    </div>
                  )}

                  <label className="flex items-center gap-3 cursor-pointer">
                    <Checkbox
                      checked={shop.hasPickup}
                      onCheckedChange={(checked) =>
                        setShop((prev) => ({ ...prev, hasPickup: checked === true }))
                      }
                    />
                    <span className="text-sm text-foreground">
                      Customers can pick up from my shop
                    </span>
                  </label>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="operating_hours">Operating Hours (Optional)</Label>
                  <Input
                    id="operating_hours"
                    name="operating_hours"
                    placeholder="Mon - Sat: 8:00 AM - 6:00 PM"
                    value={shop.operating_hours}
                    onChange={handleInputChange}
                  />
                  <p className="text-xs text-muted-foreground">
                    Let customers know when you&apos;re open for business
                  </p>
                </div>

                <div className="space-y-4">
                  <h3 className="font-medium text-foreground flex items-center gap-2">
                    <CreditCard className="h-5 w-5 text-primary" />
                    Payment Methods
                  </h3>

                  <div className="space-y-3">
                    {PAYMENT_METHODS.map((pm) => (
                      <label
                        key={pm.value}
                        className="flex items-center gap-3 cursor-pointer"
                      >
                        <Checkbox
                          checked={shop.payment_methods.includes(pm.value)}
                          onCheckedChange={() => togglePaymentMethod(pm.value)}
                        />
                        <span className="text-sm text-foreground">{pm.label}</span>
                      </label>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Step 4: Complete */}
          {step === 4 && (
            <div className="text-center py-8">
              <div className="flex h-20 w-20 items-center justify-center rounded-full bg-primary/10 mx-auto mb-6">
                <Sparkles className="h-10 w-10 text-primary" />
              </div>
              <h2 className="text-2xl font-bold text-foreground mb-2">
                Your Shop is Ready!
              </h2>
              <p className="text-muted-foreground max-w-md mx-auto mb-8">
                Congratulations! You&apos;ve successfully set up your shop on Ikobiz.
                Now it&apos;s time to add your first products and start selling.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Button asChild className="gap-2">
                  <Link href="/seller/inventory/new">
                    Add Your First Product
                    <ArrowRight className="h-4 w-4" />
                  </Link>
                </Button>
                <Button variant="outline" asChild>
                  <Link href="/seller/dashboard">Go to Dashboard</Link>
                </Button>
              </div>
            </div>
          )}

          {/* Navigation */}
          {step < 4 && (
            <div className="flex justify-between mt-8 pt-6 border-t border-border">
              <Button
                variant="outline"
                onClick={prevStep}
                disabled={step === 1 || submitting}
                className="gap-2"
              >
                <ArrowLeft className="h-4 w-4" />
                Back
              </Button>
              {step < 3 ? (
                <Button onClick={nextStep} className="gap-2">
                  Continue
                  <ArrowRight className="h-4 w-4" />
                </Button>
              ) : (
                <Button
                  onClick={handleSubmit}
                  disabled={submitting}
                  className="gap-2"
                >
                  {submitting ? "Creating Shop..." : "Create Shop"}
                  {!submitting && <ArrowRight className="h-4 w-4" />}
                </Button>
              )}
            </div>
          )}
        </div>

        {/* Help Text */}
        {step < 4 && (
          <p className="text-center text-sm text-muted-foreground mt-6">
            Set up your shop in under 5 minutes. Your progress is saved automatically.
          </p>
        )}
      </main>
    </div>
  )
}
