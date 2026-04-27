
import { notFound } from "next/navigation"

import { getCategory, getFeed, getFeedBySlug, getSubMenuByUrl } from "@/lib/server"

import Article from "@/components/article"
import { PageTitle } from "@/components/page/title"
import { PageHero } from "@/components/page/hero"
import { Cover } from "@/components/page/cover"
import Gallery from "@/components/gallery"

interface Props {
  params: Promise<{
    id: string
  }>
}

const isNumericId = (value: string) => /^\d+$/.test(value)

export default async function index({ params }: Props) {
  const { id } = await params

  let feed = null

  if (isNumericId(id)) {
    try {
      feed = await getFeed(id)
    } catch (_err) {
      // Fallback to slug lookup below.
    }
  }

  if (!feed?.id) {
    feed = await getFeedBySlug(id)
  }

  if (!feed?.id) {
    notFound()
  }

  const categoryKey = feed.category?.key || "news"
  const categoryFromPath = await getCategory(categoryKey)
  const newsSubmenu = await getSubMenuByUrl("/news")
  const feedSubmenu = await getSubMenuByUrl(`/feed/${categoryKey}`)

  const { author, title, category, content, cover, date, description, cover_offset_x, cover_offset_y, gallery, original_uri, slug } = feed
  const icon = newsSubmenu?.icon || feedSubmenu?.icon

  return (
    <>
      <PageHero
        title={category?.title || categoryFromPath?.title}
        description={description?.length ? description : categoryFromPath?.description}
      />
      <div className="px-4 sm:px-8">
        <div className="max-w-5xl m-auto py-8 flex flex-col gap-y-8">
          <PageTitle title={title} icon={icon} />
          <div className="w-full flex justify-center">
            <Cover cover={cover} className={`h-auto w-full max-h-120 object-cover`} offset_x={cover_offset_x} offset_y={cover_offset_y} />
          </div>
          {
            original_uri && (
              <div className="text-sm text-gray-500 mt-4">
                Original article: <a href={original_uri} target="_blank" rel="noopener noreferrer" className="text-blue-500 underline">{original_uri}</a>
              </div>
            )
          }
          <Article
            title={title}
            cover={cover}
            author={author}
            date={date}
            content={content}
          />
          {
            gallery && slug && <Gallery slug={slug} exclude={cover?.id ? [cover?.id] : []} />
          }
        </div>
      </div>
    </>
  )
}
