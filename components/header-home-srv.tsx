import { getMetadata } from "@/lib/utils"
import { HeaderHome } from "./header-home-cli"

import { getMenuSections } from "@/lib/utils"


export const HomeHeaderServer = async () => {
  const meta = await getMetadata()
  const secs = await getMenuSections()
  console.log(secs)

  return (
    <HeaderHome
      title={meta.title}
      description={meta.description}
      phone={meta.phone}
      email={meta.email}
      facebookUrl={meta.facebook}
      twitterUrl={meta.twitter}
    />
  )
}
