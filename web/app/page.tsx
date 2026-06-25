import { HeroSection } from "@/components/home/hero-section"
import { FeaturedShops } from "@/components/home/featured-shops"
import { PopularCategories } from "@/components/home/popular-categories"
import { WhyIkobiz } from "@/components/home/why-ikobiz"
import { WhatsAppFeature } from "@/components/home/whatsapp-feature"

export default function HomePage() {
  return (
    <>
      <HeroSection />
      <FeaturedShops />
      <PopularCategories />
      <WhyIkobiz />
      <WhatsAppFeature />
    </>
  )
}
