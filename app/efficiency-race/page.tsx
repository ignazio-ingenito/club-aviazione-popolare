import { getFeedBySlug, getSubMenuByUrl } from "@/lib/server"

import Article from "@/components/article"
import { PageTitle } from "@/components/page/title"
import { PageHero } from "@/components/page/hero"
import { Cover } from "@/components/page/cover"
import Gallery from "@/components/gallery"

export default async function index() {
  const slug = "efficiency-race"
  const { icon } = await getSubMenuByUrl("/efficiency-race")
  const { author, title, category, date, content, cover } = await getFeedBySlug(slug)

  return (
    <>
      <PageHero title={category.title} description={category.description} />
      <div className="px-4 sm:px-8">
        <div className="max-w-5xl m-auto py-8 flex flex-col gap-y-8">
          <PageTitle title={title} icon={icon} />
          <div className="w-full flex justify-center">
            <Cover cover={cover} className="h-auto w-full max-h-120 object-contain" />
          </div>

          <Article
            title={title}
            cover={cover}
            author={author}
            date={date}
            content={content}
          />

          <Gallery slug={slug} exclude={cover?.id ? [cover?.id] : []} />
        </div>
      </div>
    </>
  )
}
