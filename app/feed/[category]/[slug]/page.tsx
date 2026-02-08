import { getCategory, getFeedBySlug, getSubMenuByUrl } from "@/lib/server"

import Article from "@/components/article"
import { PageTitle } from "@/components/page/title"
import { PageHero } from "@/components/page/hero"
import { Cover } from "@/components/page/cover"
import Gallery from "@/components/gallery"

interface Props {
  params: Promise<{
    slug: string
  }>
}

export default async function index({ params }: Props) {
  const { slug } = await params
  const { author, title, category, content, cover, date, description, cover_offset_x, cover_offset_y } = await getFeedBySlug(slug)
  const { icon } = await getSubMenuByUrl(`/feed/${category.key}`)


  return (
    <>
      <PageHero title={category.title} description={description?.length ? description : category.description} />
      <div className="px-4 sm:px-8">
        <div className="max-w-5xl m-auto py-8 flex flex-col gap-y-8">
          <PageTitle title={title} icon={icon} />
          <div className="w-full flex justify-center">
            <Cover cover={cover} className={`h-auto w-full max-h-120 object-cover`} offset_x={cover_offset_x} offset_y={cover_offset_y} />
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
