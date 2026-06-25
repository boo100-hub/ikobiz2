import { Shield, Truck, MapPin, Clock } from "lucide-react"

const features = [
  {
    icon: Shield,
    title: "Trusted Sellers",
    description: "All shops are verified and rated by real customers. Shop with confidence knowing you&apos;re buying from legitimate local businesses.",
  },
  {
    icon: MapPin,
    title: "Local First",
    description: "Support businesses in your community. Discover shops near you and help grow your local economy.",
  },
  {
    icon: Truck,
    title: "Flexible Delivery",
    description: "Choose delivery to your doorstep or pick up from the shop. Whatever works best for you.",
  },
  {
    icon: Clock,
    title: "Quick Response",
    description: "Connect directly with sellers via WhatsApp for instant communication and fast order processing.",
  },
]

export function WhyIkobiz() {
  return (
    <section className="py-16 md:py-24">
      <div className="mx-auto max-w-7xl px-4 md:px-6">
        {/* Header */}
        <div className="text-center mb-12">
          <h2 className="text-2xl font-bold text-foreground md:text-3xl">
            Why Choose Ikobiz?
          </h2>
          <p className="mt-2 text-muted-foreground max-w-2xl mx-auto">
            We&apos;re building the future of local commerce in Africa, one shop at a time
          </p>
        </div>

        {/* Features Grid */}
        <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-4">
          {features.map((feature) => {
            const Icon = feature.icon
            return (
              <div
                key={feature.title}
                className="text-center p-6"
              >
                <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10 mb-4">
                  <Icon className="h-8 w-8 text-primary" />
                </div>
                <h3 className="text-lg font-semibold text-foreground mb-2">
                  {feature.title}
                </h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {feature.description}
                </p>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
