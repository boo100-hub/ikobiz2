"use client"

import Link from "next/link"
import { MessageCircle, CheckCircle, Search, ShoppingBag, MessageSquare, Truck } from "lucide-react"
import { Button } from "@/components/ui/button"

const steps = [
  "Message the Ikobiz number on WhatsApp",
  "Tell the AI what you're looking for — in plain English",
  "Browse recommendations, compare options, ask questions",
  "Place your order with delivery or pickup preference",
  "Seller confirms and coordinates fulfillment via WhatsApp",
]

export function WhatsAppFeature() {
  return (
    <section className="py-16 md:py-24 bg-[#D1FAE5]">
      <div className="mx-auto max-w-7xl px-4 md:px-6">
        <div className="grid gap-12 items-center lg:grid-cols-2">
          {/* Content */}
          <div>
            <div className="inline-flex items-center gap-2 rounded-full bg-[#25D366]/20 px-4 py-2 text-sm font-medium text-[#128C7E] mb-6">
              <MessageCircle className="h-4 w-4" />
              WhatsApp Commerce
            </div>

            <h2 className="text-3xl font-bold text-foreground md:text-4xl text-balance">
              Shop Directly on WhatsApp
            </h2>

            <p className="mt-4 text-lg text-muted-foreground leading-relaxed">
              No app download, no account creation. Just message the Ikobiz number on WhatsApp and an AI shopping assistant helps you find products, compare options, and place orders — all in one conversation.
            </p>

            <ul className="mt-8 space-y-4">
              {steps.map((step) => (
                <li key={step} className="flex items-center gap-3">
                  <CheckCircle className="h-5 w-5 text-[#25D366] flex-shrink-0" />
                  <span className="text-foreground">{step}</span>
                </li>
              ))}
            </ul>

            <Link href="https://wa.me/254700000000" target="_blank" rel="noopener noreferrer">
              <Button
                className="mt-8 h-12 px-6 gap-2 bg-[#25D366] hover:bg-[#128C7E] text-white font-medium rounded-xl"
              >
                <MessageCircle className="h-5 w-5" />
                Start Shopping on WhatsApp
              </Button>
            </Link>
          </div>

          {/* Phone Mockup */}
          <div className="relative">
            <div className="relative aspect-square max-w-md mx-auto">
              <div className="absolute inset-0 rounded-[3rem] bg-secondary shadow-2xl overflow-hidden">
                <div className="absolute top-0 left-1/2 -translate-x-1/2 w-1/3 h-7 bg-secondary rounded-b-3xl" />
                <div className="h-full w-full p-3 pt-10">
                  <div className="h-full w-full rounded-[2.2rem] bg-[#ECE5DD] overflow-hidden">
                    {/* WhatsApp Header */}
                    <div className="bg-[#075E54] px-4 py-3 flex items-center gap-3">
                      <div className="h-10 w-10 rounded-full bg-white/20 flex items-center justify-center">
                        <ShoppingBag className="h-5 w-5 text-white" />
                      </div>
                      <div>
                        <div className="text-white font-medium text-sm">Ikobiz Shop</div>
                        <div className="text-white/70 text-xs">online</div>
                      </div>
                    </div>

                    {/* Chat Messages */}
                    <div className="p-3 space-y-2">
                      <div className="bg-[#DCF8C6] rounded-lg p-2 px-3 max-w-[75%] ml-auto shadow-sm">
                        <p className="text-sm text-gray-800">Gaming chair under 15k?</p>
                        <span className="text-[10px] text-gray-500">10:30 AM</span>
                      </div>

                      <div className="bg-white rounded-lg p-2 px-3 max-w-[75%] shadow-sm">
                        <p className="text-sm text-gray-800">4 options found near you:</p>
                        <p className="text-xs text-gray-700 mt-1 leading-snug">
                          1. ProGamer X200 — KES 12,500{'\n'}
                          2. ComfortSeat — KES 14,000{'\n'}
                          3. AeroChair — KES 11,000{'\n'}
                          4. DeskKing V3 — KES 13,800
                        </p>
                        <span className="text-[10px] text-gray-500">10:30 AM</span>
                      </div>

                      <div className="bg-[#DCF8C6] rounded-lg p-2 px-3 max-w-[75%] ml-auto shadow-sm">
                        <p className="text-sm text-gray-800">#1 details + delivery to Rongai?</p>
                        <span className="text-[10px] text-gray-500">10:31 AM</span>
                      </div>

                      <div className="bg-white rounded-lg p-2 px-3 max-w-[75%] shadow-sm">
                        <p className="text-sm text-gray-800">ProGamer X200 — KES 12,500</p>
                        <p className="text-xs text-gray-700 mt-1 leading-snug">
                          In stock (Black/Red) ✓{'\n'}
                          Delivers to Rongai — KES 300
                        </p>
                        <span className="text-[10px] text-gray-500">10:31 AM</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Decorative elements */}
              <div className="absolute -right-4 -bottom-4 h-24 w-24 rounded-full bg-[#25D366]/30 blur-xl" />
              <div className="absolute -left-4 top-1/4 h-16 w-16 rounded-full bg-primary/30 blur-xl" />
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
