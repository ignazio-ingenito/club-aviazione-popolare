import Image from "next/image"
import { Category } from "@/lib/types"
import { DEFAULT_COVER, sanitizeHtml } from "@/lib/directus"
import { PageHero } from "@/components/page/hero"
import { PageTitle } from "@/components/page/title"
import { Calendar, User } from "lucide-react"

interface ArticleProps {
  params: {
    category: Category
    title?: string
    cover?: string
    author?: string
    date?: Date
    content?: string
    icon?: string
  }
}

const ArticleMeta = ({ author, date }: { author?: string; date?: Date }) => {
  return (
    <div className="flex justify-end">
      <div className="justify-end w-fit grid grid-cols-[auto_auto] gap-x-2 items-center">
        <User className="size-4 text-accent" />
        <span className="text-muted-foreground">{author}</span>
        <Calendar className="size-4 text-accent" />
        <span className="text-muted-foreground">
          {new Date(date || "").toLocaleDateString("it", {
            year: "numeric",
            month: "long",
            day: "numeric",
          })}
        </span>
      </div>
    </div>
  )
}

export default async function Article({
  params: { category, title, cover, author, date, content, icon },
}: ArticleProps) {
  return (
    <>
      <PageHero title={category.title} description={category.description} />

      <div className="mx-4 min-[800px]:mx-auto max-w-3xl flex flex-col gap-y-4 pt-8 ">
        <PageTitle title={title} icon={icon} />
        <ArticleMeta author={author} date={date} />

        <Image
          src={`${process.env.DIRECTUS_URL}/assets/${cover || DEFAULT_COVER}`}
          width={1024}
          height={0}
          alt={title || ""}
          className="object-cover"
        />
        <div
          className="article prose prose-article leading-loose dark:prose-articleDark text-muted-foreground gall"
          dangerouslySetInnerHTML={{ __html: sanitizeHtml(content ?? "") }}
        />
      </div>
    </>
  )
}
