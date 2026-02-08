import Link from "next/link"
import Image from "next/image"
import * as cheerio from 'cheerio'

import { PageHero } from "@/components/page/hero"
import { Card, CardContent } from "@/components/ui/card"
import { getCategory, getFeeds } from "@/lib/server"
import { getImageUrl } from "@/lib/directus"

import { Feed } from "../../../lib/types"

import { ArrowRight } from "lucide-react"

interface Props {
  params: Promise<{
    category: string
  }>
}

const sanitizeHtml = (html: string) => {
  const $ = cheerio.load(html)
  $("img").remove()
  return $.html()
}

export default async function index({ params }: Props) {
  const { category } = await params

  const rows = (await getFeeds(category)) as Feed[]
  const { key, title: categoryTitle } = await getCategory(category)

  return (
    <>
      <PageHero title={key} description={categoryTitle} />

      <div className="px-4 sm:px-8">
        <div className="max-w-5xl m-auto py-8 grid gap-4 grid-cols-[repeat(auto-fit,minmax(320px,1fr))] justify-center overflow-hidden">
          {rows.map(({ id, slug, title, date, content, cover }) => (
            <Link
              key={id}
              href={`/feed/${category}/${slug}`}
              className="block h-full w-full min-w-0 text-sm font-medium text-primary"
            >
              <Card className="h-full w-full min-w-0 transition-shadow border-0 dark:border shadow-sm hover:shadow-lg hover:cursor-pointer">
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
                      src={getImageUrl(cover, 160, 160)}
                      alt={title || ""}
                      width={160}
                      height={160}
                      className="float-right ml-4"
                    />
                    <div
                      className="text-sm text-muted-foreground"
                      dangerouslySetInnerHTML={{
                        __html: sanitizeHtml(content ?? ""),
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
