
import { getFeedBySlug, sanitizeHtml } from "@/lib/server"

import { PageHero } from "@/components/page/hero"
import { PageTitle } from "@/components/page/title"

interface Props {
  params: {
    slug: string
  }
}

export default async function index({ params }: Props) {
  const { slug } = params
  const feed = await getFeedBySlug(slug)
  const { author, title, category, date, content } = feed

  return (
    <>
      <PageHero title={title} description={category.description} />

      <div className="p-8 flex flex-col max-w-7xl m-auto">
        <PageTitle title={title} icon="trophy" />

        <div className="select-none text-muted-foreground [&_table]:w-full [&_table]:inline-table [&_table]:mt-4 [&_table_tr]:border-y [&_table_tr]:leading-10 "
          dangerouslySetInnerHTML={{ __html: sanitizeHtml((content) ?? "") }}
        />
      </div>
    </>
  )
}
