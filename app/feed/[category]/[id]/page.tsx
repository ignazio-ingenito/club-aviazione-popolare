import { getFeed, getSubMenuByUrl } from "@/lib/server"

import Article from "@/components/article"

interface Props {
  params: {
    id: string
  }
}

export default async function index({ params }: Props) {
  const { id: id_feed } = params
  const { author, title, category, date, content, cover } = await getFeed(
    id_feed
  )
  const { icon } = await getSubMenuByUrl("/feed/corsi")

  return (
    <div className="pb-8">
      <Article
        params={{ category, title, cover, author, date, content, icon }}
      />
    </div>
  )
}
