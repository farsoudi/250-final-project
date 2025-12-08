import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Scope Attendance',
  description: 'Attendance tracking system for Scope CS Club',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}

