import { HomeHero } from "@/components/home/hero"
import { News } from "@/components/home/news"

import { HowToStart } from "@/components/home/how-to-start"
import { BecomeMember } from "@/components/home/become-member"

export default async function HomePage() {

  return (
    <>
      {/* Hero Section */}
      <HomeHero />

      <div className="px-8 flex flex-col gap-y-8 max-w-7xl m-auto">
        {/* Latest News Section */}
        <News />

        {/* Come Iniziare Section */}
        <HowToStart />

        {/* Diventa Socio Section */}
        <BecomeMember />
      </div>
    </>
  )
}
