"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Search } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"

export function HeroSection() {
  const [searchQuery, setSearchQuery] = useState("")
  const router = useRouter()

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      router.push(`/search?q=${encodeURIComponent(searchQuery.trim())}`)
    }
  }

  return (
    <section className="relative overflow-hidden bg-gradient-to-br from-[#D1FAE5] via-background to-background">
      <div className="absolute inset-0 opacity-30">
        <div className="absolute -left-40 -top-40 h-80 w-80 rounded-full bg-primary/20 blur-3xl" />
        <div className="absolute -right-40 top-20 h-96 w-96 rounded-full bg-accent/20 blur-3xl" />
      </div>
      <div className="relative mx-auto max-w-7xl px-4 py-16 md:px-6 md:py-24 lg:py-32">
        <div className="mx-auto max-w-3xl text-center">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full bg-primary/10 px-4 py-2 text-sm font-medium text-primary">
            <span className="h-2 w-2 rounded-full bg-primary animate-pulse" />
            Trusted across Kenya
          </div>
          <h1 className="text-4xl font-bold tracking-tight text-foreground md:text-5xl lg:text-6xl text-balance">
            Discover Trusted Local Shops Near You
          </h1>
          <p className="mt-6 text-lg text-muted-foreground md:text-xl text-pretty leading-relaxed">
            Shop from local businesses, order through web or WhatsApp, and receive products your way. Supporting community commerce across Kenya.
          </p>
          <form onSubmit={handleSearch} className="mt-10 mx-auto max-w-xl">
            <div className="relative flex gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
                <Input
                  type="search"
                  placeholder="Search for shops, products, or categories..."
                  className="h-14 w-full pl-12 pr-4 text-base rounded-2xl border-border bg-card shadow-lg focus-visible:ring-primary"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
              <Button type="submit" className="h-14 px-8 rounded-2xl bg-primary hover:bg-[#059669] text-primary-foreground font-medium shadow-lg">
                Search
              </Button>
            </div>
            <p className="mt-3 text-sm text-muted-foreground">
              Popular: Electronics, Fashion, Groceries, Home & Living
            </p>
          </form>

        </div>
      </div>
    </section>
  )
}
