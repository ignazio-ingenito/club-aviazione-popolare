import { getFeed, getFeedBySlug, getSubMenuByUrl } from "@/lib/server"

import Article from "@/components/article"
import { PageTitle } from "@/components/page/title"
import { PageHero } from "@/components/page/hero"

interface Props {
  params: {
    slug: string
  }
}

export default async function index({ params }: Props) {
  const { slug } = params
  const { author, title, category, date, content, cover } = await getFeedBySlug(slug)
  const { icon } = await getSubMenuByUrl("/feed/corsi")

  return (
    <>
      <PageHero title={category.title} description={category.description} />
      <div className="p4 sm:p-8">
        <div className="max-w-5xl mx-auto flex flex-col gap-y-4">
          <PageTitle title={title} icon={icon} />
          <Article
            title={title}
            cover={cover}
            author={author}
            date={date}
            content={content}
          />
        </div>
      </div>
    </>
  )
}
