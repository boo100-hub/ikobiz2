"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import Image from "next/image"
import Link from "next/link"
import { api, formatPrice, type CartItem } from "@/lib/api"
import { useAuth } from "@/lib/auth"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import {
  ChevronRight,
  Truck,
  Store,
  CreditCard,
  Smartphone,
  Banknote,
  Check,
  MapPin,
} from "lucide-react"
import { toast } from "sonner"

function getItemPrice(item: CartItem): number {
  if (item.product) return item.product.price
  return 0
}

function getItemTitle(item: CartItem): string {
  if (item.product) return item.product.title
  return `Item #${item.id}`
}

function getItemImage(item: CartItem): string {
  if (item.product?.image_url) return item.product.image_url
  return '/placeholder.svg'
}

const steps = ["Delivery", "Payment", "Confirm"]

export default function CheckoutPage() {
  const router = useRouter()
  const { isLoggedIn } = useAuth()
  const [items, setItems] = useState<CartItem[]>([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [currentStep, setCurrentStep] = useState(0)
  const [deliveryMethod, setDeliveryMethod] = useState("delivery")
  const [paymentMethod, setPaymentMethod] = useState("mpesa")
  const [formData, setFormData] = useState({
    fullName: "",
    phone: "",
    email: "",
    address: "",
    city: "Nairobi",
    notes: "",
  })

  useEffect(() => {
    if (!isLoggedIn) { setLoading(false); return }
    api.get('/cart', true).then(data => {
      const cart = data?.items || (Array.isArray(data) ? data : [])
      setItems(cart)
    }).catch(() => {}).finally(() => setLoading(false))
  }, [isLoggedIn])

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value })
  }

  const nextStep = () => setCurrentStep(Math.min(steps.length - 1, currentStep + 1))
  const prevStep = () => setCurrentStep(Math.max(0, currentStep - 1))

  const subtotal = items.reduce((sum, item) => sum + getItemPrice(item) * item.quantity, 0)
  const deliveryFee = deliveryMethod === "delivery" ? 500 : 0
  const total = subtotal + deliveryFee

  const handleConfirm = async () => {
    setSubmitting(true)
    try {
      const result = await api.post('/checkout', {
        fulfillment_method: deliveryMethod,
        delivery_area: deliveryMethod === 'delivery' ? formData.address + ', ' + formData.city : null,
        payment_method: paymentMethod,
        customer_phone: formData.phone,
      }, true)
      toast.success('Order placed successfully!')
      const orderId = result.order_id || result.id || Date.now()
      router.push('/orders/' + orderId)
    } catch (e: any) {
      toast.error(e.message || 'Checkout failed. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  if (!isLoggedIn) return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-center space-y-4">
        <h1 className="text-2xl font-bold">Checkout</h1>
        <p className="text-muted-foreground">Please log in to continue.</p>
        <Link href="/auth/login">
          <Button>Login</Button>
        </Link>
      </div>
    </div>
  )

  if (loading) return <div className="loading" />

  return (
    <div className="flex min-h-screen flex-col">
      <main className="flex-1 bg-background">
        <div className="mx-auto max-w-4xl px-4 py-8 md:px-6">
          <nav className="mb-6 flex items-center gap-2 text-sm text-muted-foreground">
            <Link href="/cart" className="hover:text-primary">Cart</Link>
            <ChevronRight className="h-4 w-4" />
            <span className="text-foreground">Checkout</span>
          </nav>

          <h1 className="text-2xl font-bold text-foreground md:text-3xl mb-8">
            Checkout
          </h1>

          <div className="mb-8">
            <div className="flex items-center justify-between">
              {steps.map((step, index) => (
                <div key={step} className="flex items-center">
                  <div className="flex flex-col items-center">
                    <div
                      className={`flex h-10 w-10 items-center justify-center rounded-full border-2 transition-colors ${
                        index <= currentStep
                          ? "border-primary bg-primary text-primary-foreground"
                          : "border-border bg-card text-muted-foreground"
                      }`}
                    >
                      {index < currentStep ? (
                        <Check className="h-5 w-5" />
                      ) : (
                        <span>{index + 1}</span>
                      )}
                    </div>
                    <span className={`mt-2 text-sm ${
                      index <= currentStep ? "text-primary font-medium" : "text-muted-foreground"
                    }`}>
                      {step}
                    </span>
                  </div>
                  {index < steps.length - 1 && (
                    <div className={`mx-4 h-0.5 w-16 md:w-24 transition-colors ${
                      index < currentStep ? "bg-primary" : "bg-border"
                    }`} />
                  )}
                </div>
              ))}
            </div>
          </div>

          <div className="grid gap-8 lg:grid-cols-3">
            <div className="lg:col-span-2">
              {currentStep === 0 && (
                <div className="rounded-2xl border border-border bg-card p-6 space-y-6">
                  <h2 className="text-lg font-semibold text-foreground">Delivery Method</h2>

                  <RadioGroup value={deliveryMethod} onValueChange={setDeliveryMethod}>
                    <label className={`flex items-center gap-4 p-4 rounded-xl border cursor-pointer transition-colors ${
                      deliveryMethod === "delivery" ? "border-primary bg-primary/5" : "border-border hover:bg-muted"
                    }`}>
                      <RadioGroupItem value="delivery" id="delivery" />
                      <Truck className="h-5 w-5 text-primary" />
                      <div className="flex-1">
                        <p className="font-medium">Home Delivery</p>
                        <p className="text-sm text-muted-foreground">Delivered to your doorstep</p>
                      </div>
                      <span className="font-medium">KSh 500</span>
                    </label>
                    <label className={`flex items-center gap-4 p-4 rounded-xl border cursor-pointer transition-colors ${
                      deliveryMethod === "pickup" ? "border-primary bg-primary/5" : "border-border hover:bg-muted"
                    }`}>
                      <RadioGroupItem value="pickup" id="pickup" />
                      <Store className="h-5 w-5 text-primary" />
                      <div className="flex-1">
                        <p className="font-medium">Shop Pickup</p>
                        <p className="text-sm text-muted-foreground">Pick up from seller location</p>
                      </div>
                      <span className="font-medium text-green-600">Free</span>
                    </label>
                  </RadioGroup>

                  <div className="border-t border-border pt-6 space-y-4">
                    <h3 className="font-medium text-foreground">Contact Information</h3>
                    <div className="grid gap-4 sm:grid-cols-2">
                      <div className="space-y-2">
                        <Label htmlFor="fullName">Full Name</Label>
                        <Input
                          id="fullName"
                          name="fullName"
                          placeholder="John Doe"
                          value={formData.fullName}
                          onChange={handleInputChange}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="phone">Phone Number</Label>
                        <Input
                          id="phone"
                          name="phone"
                          placeholder="+254 712 345 678"
                          value={formData.phone}
                          onChange={handleInputChange}
                        />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="email">Email (Optional)</Label>
                      <Input
                        id="email"
                        name="email"
                        type="email"
                        placeholder="john@example.com"
                        value={formData.email}
                        onChange={handleInputChange}
                      />
                    </div>
                  </div>

                  {deliveryMethod === "delivery" && (
                    <div className="border-t border-border pt-6 space-y-4">
                      <h3 className="font-medium text-foreground flex items-center gap-2">
                        <MapPin className="h-4 w-4 text-primary" />
                        Delivery Address
                      </h3>
                      <div className="space-y-2">
                        <Label htmlFor="address">Street Address</Label>
                        <Input
                          id="address"
                          name="address"
                          placeholder="123 Kimathi Street, CBD"
                          value={formData.address}
                          onChange={handleInputChange}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="city">City</Label>
                        <Input
                          id="city"
                          name="city"
                          value={formData.city}
                          onChange={handleInputChange}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="notes">Delivery Notes (Optional)</Label>
                        <Input
                          id="notes"
                          name="notes"
                          placeholder="Gate code, landmarks, etc."
                          value={formData.notes}
                          onChange={handleInputChange}
                        />
                      </div>
                    </div>
                  )}

                  <Button onClick={nextStep} className="w-full h-12 bg-primary hover:bg-[#059669] text-primary-foreground">
                    Continue to Payment
                  </Button>
                </div>
              )}

              {currentStep === 1 && (
                <div className="rounded-2xl border border-border bg-card p-6 space-y-6">
                  <h2 className="text-lg font-semibold text-foreground">Payment Method</h2>

                  <RadioGroup value={paymentMethod} onValueChange={setPaymentMethod}>
                    <label className={`flex items-center gap-4 p-4 rounded-xl border cursor-pointer transition-colors ${
                      paymentMethod === "mpesa" ? "border-primary bg-primary/5" : "border-border hover:bg-muted"
                    }`}>
                      <RadioGroupItem value="mpesa" id="mpesa" />
                      <Smartphone className="h-5 w-5 text-green-600" />
                      <div className="flex-1">
                        <p className="font-medium">M-Pesa</p>
                        <p className="text-sm text-muted-foreground">Pay via M-Pesa mobile money</p>
                      </div>
                    </label>
                    <label className={`flex items-center gap-4 p-4 rounded-xl border cursor-pointer transition-colors ${
                      paymentMethod === "card" ? "border-primary bg-primary/5" : "border-border hover:bg-muted"
                    }`}>
                      <RadioGroupItem value="card" id="card" />
                      <CreditCard className="h-5 w-5 text-blue-600" />
                      <div className="flex-1">
                        <p className="font-medium">Card Payment</p>
                        <p className="text-sm text-muted-foreground">Visa, Mastercard, or other cards</p>
                      </div>
                    </label>
                    <label className={`flex items-center gap-4 p-4 rounded-xl border cursor-pointer transition-colors ${
                      paymentMethod === "cod" ? "border-primary bg-primary/5" : "border-border hover:bg-muted"
                    }`}>
                      <RadioGroupItem value="cod" id="cod" />
                      <Banknote className="h-5 w-5 text-amber-600" />
                      <div className="flex-1">
                        <p className="font-medium">Cash on Delivery</p>
                        <p className="text-sm text-muted-foreground">Pay when you receive your order</p>
                      </div>
                    </label>
                  </RadioGroup>

                  {paymentMethod === "mpesa" && (
                    <div className="rounded-xl bg-green-50 p-4 border border-green-200">
                      <p className="text-sm text-green-800">
                        You will receive an M-Pesa prompt on your phone to complete the payment after confirming your order.
                      </p>
                    </div>
                  )}

                  <div className="flex gap-4">
                    <Button variant="outline" onClick={prevStep} className="flex-1 h-12">
                      Back
                    </Button>
                    <Button onClick={nextStep} className="flex-1 h-12 bg-primary hover:bg-[#059669] text-primary-foreground">
                      Review Order
                    </Button>
                  </div>
                </div>
              )}

              {currentStep === 2 && (
                <div className="rounded-2xl border border-border bg-card p-6 space-y-6">
                  <h2 className="text-lg font-semibold text-foreground">Review Your Order</h2>

                  <div className="space-y-4">
                    {items.map((item) => (
                      <div key={item.id} className="flex gap-4">
                        <div className="relative h-16 w-16 overflow-hidden rounded-lg bg-muted flex-shrink-0">
                          <Image src={getItemImage(item)} alt={getItemTitle(item)} fill className="object-cover" />
                        </div>
                        <div className="flex-1">
                          <p className="font-medium text-foreground line-clamp-1">{getItemTitle(item)}</p>
                          <p className="text-sm text-muted-foreground">Qty: {item.quantity}</p>
                        </div>
                        <p className="font-medium text-foreground">
                          {formatPrice(getItemPrice(item) * item.quantity)}
                        </p>
                      </div>
                    ))}
                  </div>

                  <div className="border-t border-border pt-4 space-y-3">
                    <h3 className="font-medium text-foreground">Delivery</h3>
                    <p className="text-sm text-muted-foreground">
                      {deliveryMethod === "delivery"
                        ? `${formData.address}, ${formData.city}`
                        : "Shop Pickup"}
                    </p>
                    <p className="text-sm text-muted-foreground">{formData.phone}</p>
                  </div>

                  <div className="border-t border-border pt-4 space-y-3">
                    <h3 className="font-medium text-foreground">Payment</h3>
                    <p className="text-sm text-muted-foreground">
                      {paymentMethod === "mpesa" && "M-Pesa"}
                      {paymentMethod === "card" && "Card Payment"}
                      {paymentMethod === "cod" && "Cash on Delivery"}
                    </p>
                  </div>

                  <div className="flex gap-4">
                    <Button variant="outline" onClick={prevStep} className="flex-1 h-12" disabled={submitting}>
                      Back
                    </Button>
                    <Button
                      onClick={handleConfirm}
                      className="flex-1 h-12 bg-primary hover:bg-[#059669] text-primary-foreground"
                      disabled={submitting}
                    >
                      {submitting ? 'Placing Order...' : `Place Order - ${formatPrice(total)}`}
                    </Button>
                  </div>
                </div>
              )}
            </div>

            <div className="lg:col-span-1">
              <div className="sticky top-24 rounded-2xl border border-border bg-card p-6 space-y-4">
                <h3 className="font-semibold text-foreground">Order Summary</h3>

                <div className="space-y-3 max-h-48 overflow-auto">
                  {items.map((item) => (
                    <div key={item.id} className="flex gap-3">
                      <div className="relative h-12 w-12 overflow-hidden rounded-lg bg-muted flex-shrink-0">
                        <Image src={getItemImage(item)} alt={getItemTitle(item)} fill className="object-cover" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-foreground line-clamp-1">{getItemTitle(item)}</p>
                        <p className="text-xs text-muted-foreground">x{item.quantity}</p>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="border-t border-border pt-4 space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Subtotal</span>
                    <span>{formatPrice(subtotal)}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Delivery</span>
                    <span>{deliveryFee === 0 ? "Free" : formatPrice(deliveryFee)}</span>
                  </div>
                  <div className="flex justify-between font-semibold pt-2 border-t border-border">
                    <span>Total</span>
                    <span className="text-primary">{formatPrice(total)}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
