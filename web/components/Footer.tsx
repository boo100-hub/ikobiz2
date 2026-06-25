import Link from "next/link"
import { Store, Facebook, Twitter, Instagram } from "lucide-react"

export function Footer() {
  return (
    <footer className="bg-secondary text-secondary-foreground">
      <div className="mx-auto max-w-7xl px-4 py-12 md:px-6 lg:py-16">
        <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-4">
          <div className="space-y-4">
            <Link href="/" className="flex items-center gap-2">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary">
                <Store className="h-5 w-5 text-primary-foreground" />
              </div>
              <span className="text-xl font-bold">Ikobiz</span>
            </Link>
            <p className="text-sm text-secondary-foreground/70 leading-relaxed">
              Shop Local. Sell Smarter. Discover trusted local shops near you and support your community.
            </p>
            <div className="flex gap-4">
              <a href="#" className="text-secondary-foreground/70 hover:text-primary transition-colors">
                <Facebook className="h-5 w-5" />
              </a>
              <a href="#" className="text-secondary-foreground/70 hover:text-primary transition-colors">
                <Twitter className="h-5 w-5" />
              </a>
              <a href="#" className="text-secondary-foreground/70 hover:text-primary transition-colors">
                <Instagram className="h-5 w-5" />
              </a>
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="font-semibold">For Buyers</h3>
            <nav className="flex flex-col gap-2">
              <Link href="/search" className="text-sm text-secondary-foreground/70 hover:text-primary transition-colors">
                Browse Shops
              </Link>
              <Link href="/search" className="text-sm text-secondary-foreground/70 hover:text-primary transition-colors">
                Categories
              </Link>
              <Link href="/orders" className="text-sm text-secondary-foreground/70 hover:text-primary transition-colors">
                Track Orders
              </Link>
            </nav>
          </div>

          <div className="space-y-4">
            <h3 className="font-semibold">For Sellers</h3>
            <nav className="flex flex-col gap-2">
              <Link href="/seller/onboarding" className="text-sm text-secondary-foreground/70 hover:text-primary transition-colors">
                Start Selling
              </Link>
              <Link href="/seller/dashboard" className="text-sm text-secondary-foreground/70 hover:text-primary transition-colors">
                Seller Dashboard
              </Link>
            </nav>
          </div>

          <div className="space-y-4">
            <h3 className="font-semibold">Company</h3>
            <nav className="flex flex-col gap-2">
              <Link href="/about" className="text-sm text-secondary-foreground/70 hover:text-primary transition-colors">
                About Us
              </Link>
              <Link href="/contact" className="text-sm text-secondary-foreground/70 hover:text-primary transition-colors">
                Contact
              </Link>
              <Link href="/privacy" className="text-sm text-secondary-foreground/70 hover:text-primary transition-colors">
                Privacy Policy
              </Link>
              <Link href="/terms" className="text-sm text-secondary-foreground/70 hover:text-primary transition-colors">
                Terms of Service
              </Link>
            </nav>
          </div>
        </div>

        <div className="mt-12 border-t border-secondary-foreground/10 pt-8">
          <p className="text-center text-sm text-secondary-foreground/50">
            &copy; {new Date().getFullYear()} Ikobiz Platform. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  )
}
