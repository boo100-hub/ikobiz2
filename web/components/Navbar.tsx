'use client'

import Link from 'next/link'
import { useAuth } from '@/lib/auth'
import { useState, useEffect } from 'react'
import { api } from '@/lib/api'

export default function Navbar() {
  const { user, isLoggedIn, isSeller, logout } = useAuth()
  const [cartCount, setCartCount] = useState(0)
  const [search, setSearch] = useState('')

  useEffect(() => {
    if (isLoggedIn) {
      api.get('/cart', true).then(items => {
        const itemsArr = Array.isArray(items) ? items : []
        setCartCount(itemsArr.reduce((s: number, i: { quantity: number }) => s + i.quantity, 0))
      }).catch(() => {})
    }
  }, [isLoggedIn])

  return (
    <header className="site-header">
      <nav className="navbar">
        <Link href="/" className="navbar-brand">Ikobiz<span>.</span></Link>
        <div className="navbar-search">
          <span className="search-icon">&#128269;</span>
          <input
            type="text"
            placeholder="Search shops, products..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter' && search.trim()) {
                window.location.href = '/market?q=' + encodeURIComponent(search.trim())
              }
            }}
          />
        </div>
        <div className="navbar-links">
          <Link href="/">Shops</Link>
          <Link href="/market">Secondary Market</Link>
          {isLoggedIn ? (
            <>
              <Link href="/cart" className="nav-icon">
                &#128722;
                {cartCount > 0 && <span className="badge" id="cart-count">{cartCount}</span>}
              </Link>
              {isSeller && <Link href="/dashboard">Dashboard</Link>}
              <a href="#" style={{ color: 'var(--danger)' }} onClick={e => { e.preventDefault(); logout() }}>Logout</a>
              <span style={{ fontSize: '0.82rem', color: 'var(--gray-400)' }}>{user?.username}</span>
            </>
          ) : (
            <>
              <Link href="/auth/login">Login</Link>
              <Link href="/auth/register" className="btn btn-primary btn-sm">Sign Up</Link>
            </>
          )}
        </div>
      </nav>
    </header>
  )
}
