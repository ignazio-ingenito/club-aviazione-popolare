import Link from "next/link"
import Image from "next/image"
import * as cheerio from "cheerio"

import { Card, CardContent } from "@/components/ui/card"
import { getCategory, getFeeds, getSubMenuByUrl } from "@/lib/server"
import { getImageUrl } from "@/lib/directus"

import { PageHero } from "@/components/page/hero"
import { PageTitle } from "@/components/page/title"

import { Feed } from "../../../lib/types"

import { ArrowRight } from "lucide-react"

interface Props {
  params: Promise<{
    category: string
  }>
}

const sanitizeHtml = (html: string) => {
  const $ = cheerio.load(html)
  $("img, script, style, iframe, object, embed, h1, h2, h3, h4, h5, h6").remove()

  // Card preview is wrapped in a Link (<a>), so nested anchors are invalid HTML.
  $("a").each((_, element) => {
    $(element).replaceWith($(element).html() || "")
  })
  return ($("body").html() || "").replaceAll(/&nbsp;/g, " ")
}

export default async function index({ params }: Props) {
  const { category: categoryPath } = await params
  const { key: categoryKey, title: categoryTitle, description: categoryDescription } = await getCategory(categoryPath)
  const feeds = (await getFeeds(categoryKey)) as Feed[]
  const { icon } = await getSubMenuByUrl(`/feed/${categoryKey}`)

  return (
    <>
      <PageHero title={categoryTitle} description={categoryDescription || "description"} />
      <div className="px-4 sm:px-8">
        <div className="max-w-5xl m-auto py-8 grid gap-4 grid-cols-[repeat(auto-fit,minmax(320px,1fr))] justify-center overflow-hidden">
          <div className="col-span-full">
            <PageTitle title={categoryTitle} icon={icon} />
          </div>
          {feeds.map(({ id, slug, title, date, content, cover }) => (
            <Link
              key={id}
              href={`/feed/${categoryKey}/${slug}`}
              className="block h-full w-full min-w-0 text-sm font-medium text-primary"
            >
              <Card className="h-100 w-full min-w-0 overflow-hidden transition-shadow border-0 dark:border shadow-sm hover:shadow-lg hover:cursor-pointer">
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
                      <div className="h-16 overflow-hidden text-2xl text-muted-foreground mb-2">
                        {title}
                      </div>
                    </div>
                  </div>

                  <div className="h-60 overflow-hidden text-ellipsis">
                    <Image
                      src={getImageUrl(cover, 150, 150)}
                      alt={title || ""}
                      width={150}
                      height={150}
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
