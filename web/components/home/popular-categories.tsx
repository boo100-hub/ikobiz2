import Link from "next/link"
import { 
  Smartphone, 
  ShoppingBag, 
  Home, 
  Apple, 
  Dumbbell, 
  BookOpen,
  Car,
  Sparkles
} from "lucide-react"

const categories = [
  {
    name: "Electronics",
    icon: Smartphone,
    href: "/search?category=electronics",
    color: "bg-blue-100 text-blue-600",
  },
  {
    name: "Fashion",
    icon: ShoppingBag,
    href: "/search?category=fashion",
    color: "bg-pink-100 text-pink-600",
  },
  {
    name: "Home & Living",
    icon: Home,
    href: "/search?category=home",
    color: "bg-orange-100 text-orange-600",
  },
  {
    name: "Groceries",
    icon: Apple,
    href: "/search?category=groceries",
    color: "bg-green-100 text-green-600",
  },
  {
    name: "Health & Fitness",
    icon: Dumbbell,
    href: "/search?category=health",
    color: "bg-red-100 text-red-600",
  },
  {
    name: "Books & Stationery",
    icon: BookOpen,
    href: "/search?category=books",
    color: "bg-purple-100 text-purple-600",
  },
  {
    name: "Automotive",
    icon: Car,
    href: "/search?category=automotive",
    color: "bg-slate-100 text-slate-600",
  },
  {
    name: "Beauty",
    icon: Sparkles,
    href: "/search?category=beauty",
    color: "bg-rose-100 text-rose-600",
  },
]

export function PopularCategories() {
  return (
    <section className="py-16 md:py-24 bg-muted/50">
      <div className="mx-auto max-w-7xl px-4 md:px-6">
        {/* Header */}
        <div className="text-center mb-12">
          <h2 className="text-2xl font-bold text-foreground md:text-3xl">
            Popular Categories
          </h2>
          <p className="mt-2 text-muted-foreground">
            Browse shops by category to find exactly what you need
          </p>
        </div>

        {/* Categories Grid */}
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 lg:grid-cols-8">
          {categories.map((category) => {
            const Icon = category.icon
            return (
              <Link
                key={category.name}
                href={category.href}
                className="group flex flex-col items-center gap-3 rounded-2xl bg-card p-6 shadow-sm border border-border transition-all duration-200 hover:shadow-md hover:-translate-y-1"
              >
                <div className={`flex h-14 w-14 items-center justify-center rounded-2xl ${category.color} transition-transform group-hover:scale-110`}>
                  <Icon className="h-6 w-6" />
                </div>
                <span className="text-sm font-medium text-foreground text-center">
                  {category.name}
                </span>
              </Link>
            )
          })}
        </div>
      </div>
    </section>
  )
}
