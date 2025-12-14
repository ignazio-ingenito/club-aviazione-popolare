
import { getFeedBySlug, getSubMenuByUrl } from "@/lib/server"
import { sanitizeHtml } from "@/lib/directus"

import { PageHero } from "@/components/page/hero"
import Article from "@/components/article"

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
    <div className="pb-8 select-none text-muted-foreground [&_p]:py- [&_table]:w-full [&_table]:inline-table [&_table]:mt-4 [&_table_tr]:border-y [&_table_tr]:leading-10">
      <Article
        params={{ category, title, cover, author, date, content, icon: "trophy" }}
      />
    </div>
  )
}
