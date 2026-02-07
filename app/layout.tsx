import { ReactNode, Suspense } from "react"
import { getMenu, getMetadata } from "@/lib/server"

import { Header } from "@/components/header"
import { SiteFooter } from "@/components/site-footer"
import { ThemeProvider } from "@/components/theme-provider"

import "./globals.css"
import { Montserrat } from "next/font/google"
import favicon from "@/app/public/favicon.svg"

export const dynamic = "force-dynamic"

const montserrat = Montserrat({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
  variable: "--font-montserrat",
  display: "swap",
})

const RootLayout = async ({
  children,
}: Readonly<{
  children: ReactNode
}>) => {
  const menu = await getMenu()
  const { description, email, facebook, instagram, phone, title, twitter } = await getMetadata()

  return (
    <html lang="it" suppressHydrationWarning className={`${montserrat.variable}`}>
      <head>
        <link rel="icon" href={favicon.src} />
        <meta name="description" content={description} />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>{title}</title>
      </head>
      <body className={`font-sans antialiased`}>
        <Suspense fallback={null}>
          <ThemeProvider attribute="class" defaultTheme="system" enableSystem storageKey="cap-theme" disableTransitionOnChange>
            <div className="flex min-h-screen flex-col">
              <Header
                title={title}
                description={description}
                menu={menu}
                phone={phone}
                email={email}
                facebookUrl={facebook}
                instagramUrl={instagram}
                twitterUrl={twitter}
              />

              <main className="bg-background">
                {children}
              </main>

              <SiteFooter />
            </div>
          </ThemeProvider>
        </Suspense>
      </body>
    </html>
  )
}

export default RootLayout
