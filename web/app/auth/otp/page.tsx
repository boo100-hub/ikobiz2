"use client"

import { useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Store, ArrowRight, MessageSquare, Smartphone, CheckCircle } from "lucide-react"
import { toast } from "sonner"
import { useAuth } from "@/lib/auth"

export default function OtpLoginPage() {
  const router = useRouter()
  const { login } = useAuth()
  const [step, setStep] = useState<"phone" | "otp">("phone")
  const [phone, setPhone] = useState("")
  const [code, setCode] = useState("")
  const [loading, setLoading] = useState(false)

  const requestOtp = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!phone || phone.length < 10) {
      toast.error("Please enter a valid phone number")
      return
    }
    setLoading(true)
    try {
      const res = await fetch("http://127.0.0.1:8000/auth/otp/request", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phone }),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || "Failed to send OTP")
      }
      toast.success("Verification code sent to your WhatsApp!")
      setStep("otp")
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Something went wrong"
      toast.error(message)
    } finally {
      setLoading(false)
    }
  }

  const verifyOtp = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!code || code.length < 4) {
      toast.error("Please enter the verification code")
      return
    }
    setLoading(true)
    try {
      const res = await fetch("http://127.0.0.1:8000/auth/otp/verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phone, code }),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || "Invalid code")
      }
      const data = await res.json()
      localStorage.setItem("ikobiz_token", data.access_token)
      // Fetch user profile
      const userRes = await fetch("http://127.0.0.1:8000/auth/me", {
        headers: { Authorization: "Bearer " + data.access_token },
      })
      if (userRes.ok) {
        const user = await userRes.json()
        localStorage.setItem("ikobiz_user", JSON.stringify(user))
      }
      toast.success("Signed in successfully!")
      router.push("/")
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Invalid code"
      toast.error(message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex">
      <div className="flex-1 flex flex-col justify-center px-4 py-12 sm:px-6 lg:px-20 xl:px-24">
        <div className="mx-auto w-full max-w-sm">
          <Link href="/" className="flex items-center gap-2 mb-8">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary">
              <Store className="h-5 w-5 text-primary-foreground" />
            </div>
            <span className="text-2xl font-bold text-foreground">Ikobiz</span>
          </Link>

          {step === "phone" ? (
            <>
              <h1 className="text-2xl font-bold text-foreground">Sign in with WhatsApp</h1>
              <p className="mt-2 text-muted-foreground">
                Enter your phone number and we&apos;ll send you a verification code
              </p>

              <form onSubmit={requestOtp} className="mt-8 space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="phone">Phone Number</Label>
                  <div className="relative">
                    <Smartphone className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                    <Input
                      id="phone"
                      type="tel"
                      placeholder="+254 712 345 678"
                      className="h-12 pl-10"
                      value={phone}
                      onChange={(e) => setPhone(e.target.value)}
                      required
                    />
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Enter the phone number linked to your WhatsApp
                  </p>
                </div>

                <Button type="submit" className="w-full h-12 gap-2" disabled={loading}>
                  <MessageSquare className="h-4 w-4" />
                  {loading ? "Sending code..." : "Send Verification Code"}
                </Button>
              </form>
            </>
          ) : (
            <>
              <div className="flex items-center gap-3 mb-2">
                <CheckCircle className="h-5 w-5 text-green-500" />
                <span className="text-sm text-muted-foreground">Code sent to {phone}</span>
              </div>
              <h1 className="text-2xl font-bold text-foreground">Enter verification code</h1>
              <p className="mt-2 text-muted-foreground">
                Check your WhatsApp messages for the code
              </p>

              <form onSubmit={verifyOtp} className="mt-8 space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="code">Verification Code</Label>
                  <Input
                    id="code"
                    type="text"
                    inputMode="numeric"
                    placeholder="000000"
                    className="h-12 text-center text-2xl tracking-widest"
                    value={code}
                    onChange={(e) => setCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                    required
                    autoFocus
                  />
                </div>

                <Button type="submit" className="w-full h-12 gap-2" disabled={loading}>
                  {loading ? "Verifying..." : "Verify & Sign In"}
                  <ArrowRight className="h-4 w-4" />
                </Button>

                <button
                  type="button"
                  onClick={() => { setStep("phone"); setCode("") }}
                  className="w-full text-sm text-primary hover:underline"
                >
                  Use a different number
                </button>
              </form>
            </>
          )}

          <div className="mt-6 text-center">
            <p className="text-sm text-muted-foreground">
              Or{" "}
              <Link href="/auth/login" className="font-medium text-primary hover:underline">
                sign in with email
              </Link>
            </p>
          </div>
        </div>
      </div>

      <div className="hidden lg:flex lg:flex-1 bg-gradient-to-br from-primary/10 via-primary/5 to-accent/10 items-center justify-center p-12">
        <div className="max-w-lg text-center">
          <div className="mb-8">
            <div className="relative mx-auto w-64 h-64">
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="relative">
                  <div className="h-40 w-40 rounded-full bg-primary/20" />
                  <div className="absolute top-4 right-0 h-16 w-16 rounded-2xl bg-accent/30 rotate-12" />
                  <div className="absolute bottom-4 left-0 h-12 w-12 rounded-xl bg-primary/30 -rotate-12" />
                  <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
                    <MessageSquare className="h-20 w-20 text-primary" />
                  </div>
                </div>
              </div>
            </div>
          </div>
          <h2 className="text-2xl font-bold text-foreground mb-4">
            Shop via WhatsApp
          </h2>
          <p className="text-muted-foreground leading-relaxed">
            Sign in with your phone number to link your WhatsApp account. 
            Browse, shop, and track orders seamlessly between web and WhatsApp.
          </p>
        </div>
      </div>
    </div>
  )
}
