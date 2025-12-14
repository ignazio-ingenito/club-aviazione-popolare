import Link from "next/link"
import Image from "next/image"

import { PageHero } from "@/components/page/hero"
import { Card, CardContent } from "@/components/ui/card"
import { getCategory, getFeeds } from "@/lib/server"
import { getImageUrl, sanitizeHtml } from "@/lib/directus"

import { Feed } from "../../../lib/types"

import { ArrowRight } from "lucide-react"

interface Props {
  params: {
    category: string
  }
}

export default async function index({ params }: Props) {
  const { category: id } = params

  const rows = (await getFeeds(id)) as Feed[]
  const { title, description } = await getCategory(id)

  return (
    <>
      <PageHero title={title} description={description} />

      <div className="px-2 py-8 flex flex-col gap-y-8 max-w-5xl m-auto">
        <div className="pb-1 grid gap-4 grid-cols-[repeat(auto-fit,minmax(320px,360px))] justify-center overflow-hidden">
          {rows.map(({ id, category, title, date, content, cover }) => (
            <Link
              key={id}
              legacyBehavior
              href={`/feed/${category.id}/${id}`}
              className="text-sm font-medium text-primary inline-flex items-center"
            >
              <Card
                key={id}
                className="h-full max-w-[460px] transition-shadow border-0 dark:border shadow-sm hover:shadow-lg hover:cursor-pointer"
              >
                <CardContent className="p-6">
                  <div className="flex items-start gap-4 mb-2">
                    <div
                      className="flex flex-col items-center justify-center bg-primary text-primary-foreground rounded-lg p-3 min-w-18"
                      data-date={date?.toISOString().slice(0, 10)}
                    >
                      <span className="text-2xl font-bold leading-none">
                        {date?.getDate()}
                      </span>
                      <span className="text-xs uppercase">
                        {date?.toLocaleString("it", { month: "short" })}
                      </span>
                      <span className="text-xs uppercase">
                        {date?.getFullYear()}
                      </span>
                    </div>
                    <div className="flex-1">
                      <div className="text-2xl text-muted-foreground mb-2">
                        {title}
                      </div>
                    </div>
                  </div>

                  <div className="h-50 overflow-hidden text-ellipsis">
                    <Image
                      src={getImageUrl(cover, 150, 150)}
                      alt={title || ""}
                      width={150}
                      height={150}
                      className="float-right ml-4"
                    />
                    <span
                      className="text-sm text-muted-foreground"
                      dangerouslySetInnerHTML={{
                        __html: sanitizeHtml(content || ""),
                      }}
                    />
                  </div>
                  <p className="mt-2 mb-0 flex items-center justify-end text-sm font-medium text-primary">
                    Leggi di più <ArrowRight className="ml-1 h-3 w-3" />
                  </p>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      </div>
    </>
  )
}
