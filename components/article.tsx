import Image from "next/image"
import { DEFAULT_COVER, getImageUrl, sanitizeHtml } from "@/lib/directus"
import { Calendar, User } from "lucide-react"
import type { Cover } from "@/lib/types"

interface ArticleProps {
  title?: string
  cover?: string | Cover
  author?: string
  date?: Date
  content?: string
}

interface ArticleMetaProps {
  author?: string
  date?: Date
}

const ArticleMeta = ({ author, date }: ArticleMetaProps) => {
  return (
    <div className="flex justify-end">
      <div className="justify-end w-fit grid grid-cols-[auto_auto] gap-2 items-center">
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

export default async function Article(
  { title, cover, author, date, content }: ArticleProps) {
  const coverForUrl =
    typeof cover === "string" ? ({ id: cover } as Partial<Cover>) : cover

  return (
    <>
      <ArticleMeta author={author} date={date} />
      <Image
        src={getImageUrl(coverForUrl ?? DEFAULT_COVER, 1024)}
        width={1024}
        height={0}
        alt={title || ""}
        className="object-cover pb-4"
      />
      <div
        className="article leading-relaxed text-muted-foreground"
        dangerouslySetInnerHTML={{ __html: sanitizeHtml(content ?? "") }}
      />
    </>
  )
}
