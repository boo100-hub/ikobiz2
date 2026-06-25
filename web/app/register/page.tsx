"use client"

import { useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Checkbox } from "@/components/ui/checkbox"
import { Store, Eye, EyeOff, ArrowRight, CheckCircle } from "lucide-react"
import { toast } from "sonner"
import { useAuth } from "@/lib/auth"

export default function RegisterPage() {
  const router = useRouter()
  const { register } = useAuth()
  const [showPassword, setShowPassword] = useState(false)
  const [isSeller, setIsSeller] = useState(false)
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({
    fullName: "",
    email: "",
    phone: "",
    password: "",
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await register(formData.fullName, formData.email, formData.password, isSeller, formData.phone)
      toast.success("Account created successfully!")
      router.push(isSeller ? "/seller/onboarding" : "/")
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Registration failed. Please try again."
      toast.error(message)
    } finally {
      setLoading(false)
    }
  }

  const benefits = [
    "Track your orders in real-time",
    "Save favorite shops and products",
    "Get personalized recommendations",
    "Faster checkout with saved info",
  ]

  return (
    <div className="min-h-screen flex">
      {/* Left Side - Illustration */}
      <div className="hidden lg:flex lg:flex-1 bg-gradient-to-br from-primary/10 via-primary/5 to-accent/10 items-center justify-center p-12">
        <div className="max-w-lg">
          <div className="mb-8">
            <div className="relative mx-auto w-64 h-64">
              {/* Community Illustration */}
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="relative">
                  <div className="h-40 w-40 rounded-full bg-primary/20" />
                  <div className="absolute -top-4 -right-4 h-20 w-20 rounded-full bg-accent/30" />
                  <div className="absolute -bottom-4 -left-4 h-16 w-16 rounded-full bg-primary/30" />
                  <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
                    <Store className="h-20 w-20 text-primary" />
                  </div>
                </div>
              </div>
            </div>
          </div>
          <h2 className="text-2xl font-bold text-foreground mb-4 text-center">
            Join the Ikobiz Community
          </h2>
          <p className="text-muted-foreground leading-relaxed text-center mb-8">
            Create an account to unlock the full shopping experience and connect with local sellers.
          </p>

          <div className="space-y-3">
            {benefits.map((benefit) => (
              <div key={benefit} className="flex items-center gap-3">
                <CheckCircle className="h-5 w-5 text-primary flex-shrink-0" />
                <span className="text-foreground">{benefit}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right Side - Form */}
      <div className="flex-1 flex flex-col justify-center px-4 py-12 sm:px-6 lg:px-20 xl:px-24">
        <div className="mx-auto w-full max-w-sm">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 mb-8">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary">
              <Store className="h-5 w-5 text-primary-foreground" />
            </div>
            <span className="text-2xl font-bold text-foreground">Ikobiz</span>
          </Link>

          <h1 className="text-2xl font-bold text-foreground">
            Create your account
          </h1>
          <p className="mt-2 text-muted-foreground">
            Join thousands of shoppers on Ikobiz
          </p>

          <form onSubmit={handleSubmit} className="mt-8 space-y-5">
            <div className="space-y-2">
              <Label htmlFor="fullName">Full Name</Label>
              <Input
                id="fullName"
                type="text"
                placeholder="John Doe"
                className="h-12"
                value={formData.fullName}
                onChange={(e) => setFormData({ ...formData, fullName: e.target.value })}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                className="h-12"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="phone">Phone Number</Label>
              <Input
                id="phone"
                type="tel"
                placeholder="+254 712 345 678"
                className="h-12"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="Create a strong password"
                  className="h-12 pr-10"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                </button>
              </div>
              <p className="text-xs text-muted-foreground">
                Must be at least 8 characters
              </p>
            </div>

            <div className="flex items-center gap-2">
              <Checkbox
                id="isSeller"
                checked={isSeller}
                onCheckedChange={(checked) => setIsSeller(checked === true)}
              />
              <Label htmlFor="isSeller" className="text-sm cursor-pointer">
                I want to register as a seller
              </Label>
            </div>

            <Button
              type="submit"
              className="w-full h-12 gap-2"
              disabled={loading}
            >
              {loading ? "Creating account..." : "Create Account"}
              <ArrowRight className="h-4 w-4" />
            </Button>

            <p className="text-xs text-center text-muted-foreground">
              By creating an account, you agree to our{" "}
              <Link href="/terms" className="text-primary hover:underline">Terms of Service</Link>
              {" "}and{" "}
              <Link href="/privacy" className="text-primary hover:underline">Privacy Policy</Link>
            </p>
          </form>

          <p className="mt-6 text-center text-sm text-muted-foreground">
            Already have an account?{" "}
            <Link href="/auth/login" className="font-medium text-primary hover:underline">
              Sign in
            </Link>
          </p>

          <div className="mt-8">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-border" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="bg-background px-4 text-muted-foreground">
                  Want to sell on Ikobiz?
                </span>
              </div>
            </div>
            <button
              type="button"
              onClick={() => {
                setIsSeller(true)
                document.getElementById("fullName")?.focus()
              }}
              className="mt-4 block w-full"
            >
              <Button variant="outline" className="w-full h-12" type="button">
                Register as a Seller
              </Button>
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
