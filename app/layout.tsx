import { ReactNode, Suspense } from "react"
import { getMetadata } from "@/lib/utils-server"
import { ThemeProvider } from "@/components/theme-provider"
import { Montserrat } from "next/font/google"

import favicon from "@/app/public/favicon.svg"
import "./globals.css"

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
  const { title, description } = await getMetadata()

  return (
    <html lang="it" suppressHydrationWarning className={`${montserrat.variable}`}>
      <head>
        <link rel="icon" href={favicon.src} />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>{title}</title>
        <meta name="description" content={description} />
      </head>
      <body className={`font-sans antialiased`}>
        <Suspense fallback={null}>
          <ThemeProvider attribute="class" defaultTheme="system" enableSystem storageKey="cap-theme" disableTransitionOnChange>
            {children}
          </ThemeProvider>
        </Suspense>
      </body>
    </html>
  )
}

export default RootLayout