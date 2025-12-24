
import { getFeedBySlug, getSubMenuByUrl } from "@/lib/server"
import { sanitizeHtml } from "@/lib/directus"

import { PageHero } from "@/components/page/hero"
import Article from "@/components/article"
import { PageTitle } from "@/components/page/title"

interface Props {
  params: {
    slug: string
  }
}

export default async function index({ params }: Props) {
  const { slug } = params

  const { author, title, category, date, content, cover } = await getFeedBySlug(
    slug
  )
  return (
    <>
      <PageHero title={category.title} description={category.description} />
      <div className="p4 sm:p-8">
        <div className="max-w-5xl mx-auto flex flex-col gap-y-4">
          <div className="[&_table]:my-8 [&_table]:w-full [&_table_tr]:border-y [&_table_tr]:leading-10">
            <PageTitle title={title} icon="trophy" />
            <Article
              title={title}
              cover={cover}
              author={author}
              date={date}
              content={content}
            />
          </div>
        </div>
      </div>
    </>
  )
}
