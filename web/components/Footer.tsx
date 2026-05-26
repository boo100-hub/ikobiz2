'use client'

import Link from 'next/link'
import { useAuth } from '@/lib/auth'

export default function Footer() {
  const { isLoggedIn } = useAuth()

  return (
    <footer className="site-footer">
      <div className="footer-grid">
        <div>
          <h4>Ikobiz Market</h4>
          <p style={{ fontSize: '0.85rem' }}>Africa&apos;s premier marketplace connecting buyers with trusted sellers.</p>
        </div>
        <div>
          <h4>Quick Links</h4>
          <ul>
            <li><Link href="/">Shops</Link></li>
            <li><Link href="/market">Secondary Market</Link></li>
            {isLoggedIn && <li><Link href="/cart">Cart</Link></li>}
          </ul>
        </div>
        <div>
          <h4>Sell With Us</h4>
          <ul>
            <li><Link href="/auth/register">Open a Shop</Link></li>
            <li><Link href="/dashboard">Seller Dashboard</Link></li>
          </ul>
        </div>
        <div>
          <h4>Contact</h4>
          <ul>
            <li><a href="https://wa.me/254700000000" target="_blank">WhatsApp</a></li>
            <li><a href="mailto:support@ikobiz.co.ke">Email Us</a></li>
          </ul>
        </div>
      </div>
      <div className="footer-bottom">
        &copy; {new Date().getFullYear()} Ikobiz Marketplace. All rights reserved.
      </div>
    </footer>
  )
}
