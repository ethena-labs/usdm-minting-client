import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'USDm Minting API',
  description: 'API documentation for USDm minting and redemption',
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

