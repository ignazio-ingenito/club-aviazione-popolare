import { Hero } from "@/components/hero"
import { News } from "@/components/home/news"
import { SiteFooter } from "@/components/site-footer"
import { getMetadata, getMenu } from "@/lib/server"

import { HowToStart } from "@/components/home/how-to-start"
import { BecomeMember } from "@/components/home/become-member"
import { Header } from "@/components/header"

export default async function HomePage() {
  const meta = await getMetadata()
  const menu = await getMenu()

  return (
    <div className="home-page flex min-h-screen flex-col">
      <Header
        title={meta.title}
        description={meta.description}
        menu={menu}
        phone={meta.phone}
        email={meta.email}
        facebookUrl={meta.facebook}
        instagramUrl={meta.instagram}
        twitterUrl={meta.twitter}
      />

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
