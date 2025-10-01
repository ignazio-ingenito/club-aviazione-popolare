import Link from "next/link"
import { Hero } from "@/components/hero"
import { News } from "@/components/home/news"
import { Button } from "@/components/ui/button"
import { HeaderHome } from "@/components/header-home-cli"
import { SiteFooter } from "@/components/site-footer"
import { getMetadata } from "@/lib/utils"

import { HowToStart } from "@/components/home/how-to-start"
import { BecomeMember } from "@/components/home/become-member"

export default async function HomePage() {
  const meta = await getMetadata()

  return (
    <div className="flex min-h-screen flex-col">
      <HeaderHome title={meta.title}
        description={meta.description}
        phone={meta.phone}
        email={meta.email}
        facebookUrl={meta.facebook}
        twitterUrl={meta.twitter} />

      <main className="flex-1 w-full max-w-7xl m-auto">
        {/* Hero Section */}
        <Hero />

        {/* Latest News Section */}
        <News />

        {/* Come Iniziare Section */}
        <HowToStart />

        {/* Diventa Socio Section */}
        <BecomeMember />
      </main>

      <SiteFooter />
    </div>
  )
}
