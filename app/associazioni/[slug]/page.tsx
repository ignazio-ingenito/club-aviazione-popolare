import { getChapterByKeyOrSlug, getPage } from "@/lib/server"
import { sanitizeHtml } from "@/lib/directus"
import { notFound } from "next/navigation"

import { PageHero } from "@/components/page/hero"
import { Cover } from "@/components/page/cover"

interface Props {
  params: Promise<{
    slug: string
  }>
}

export default async function index({ params }: Props) {
  const { slug } = await params
  const chapter = await getChapterByKeyOrSlug(slug)
  if (!chapter?.id) {
    notFound()
  }

  const { description, name } = chapter
  const { cover, description: pageDescription } = await getPage("associazioni")

  return (
    <>
      <PageHero title={name} description={pageDescription} />
      <div className="px-4 sm:px-8">
        <div className="max-w-5xl m-auto py-8 flex flex-col gap-y-8">
          <div className="w-full flex justify-center">
            <Cover cover={cover} className="h-auto w-full max-h-120 object-contain" />
          </div>

          <div
            className="article text-muted-foreground text-md [&_h4]:mt-6 [&_h4]:mb-2"
            dangerouslySetInnerHTML={{ __html: sanitizeHtml(description ?? "") }}
          />
        </div>
      </div>
    </>
  )
}
