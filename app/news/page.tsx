import Link from "next/link"
import * as cheerio from "cheerio"

import { Badge } from "@/components/ui/badge"
import { PageHero } from "@/components/page/hero"
import { Card, CardContent } from "@/components/ui/card"

import { Feed } from "@/lib/types"
import { formatDate, getCategory, getFeeds } from "@/lib/server"
import { getImageUrl, sanitizeHtml } from "@/lib/directus"

import { Calendar, ArrowRight, Rss } from "lucide-react"

interface FeaturedCardProps {
  feed: Feed
}
const FeaturedCard = ({
  feed: { id, content, title, cover },
}: FeaturedCardProps) => {
  const coverUrl = getImageUrl(cover, 0, 600)
  const html = sanitizeHtml(content)

  return (
    <Card className="relative text-ellipsis hover:shadow-md transition-shadow overflow-hidden">
      <CardContent className="relative pt-6 flex flex-col justify-center overflow-hidden">
        <h3 className="overflow-hidden m-0 pt-4 pb-1 text-2xl text-accent whitespace-nowrap text-ellipsis">
          {title}
        </h3>
        <section className="max-h-[250px] overflow-hidden text-ellipsis">
          <img
            src={coverUrl}
            alt={`${title}`}
            className="float-left object-cover pr-2 mt-1 w-[40%]"
          />
          <div
            className="text-muted-foreground"
            dangerouslySetInnerHTML={{ __html: html }}
          />
        </section>
        <section className="absolute top-2 right-2 flex gap-x-1 text-xs">
          <Badge className="rounded-xs  cursor-pointer font-normal">
            in Evidenza
          </Badge>
        </section>
        <Link
          href={`/news/${id}`}
          className="mt-2 inline-flex items-center text-primary justify-end text-sm hover:underline"
        >
          Leggi l'articolo completo
          <ArrowRight className="ml-2 h-4 w-4" />
        </Link>
      </CardContent>
    </Card>
  )
}

interface FeedCardProps {
  feed: Feed
}
const FeedCard = ({
  feed: { id, content, category, date, title, cover },
}: FeedCardProps) => {
  const coverUrl = getImageUrl(cover, 440, 600)

  return (
    <Card
      key={id}
      className="overflow-hidden group hover:shadow-lg transition-shadow flex flex-col cursor-pointer"
    >
      <div className="relative h-48 overflow-hidden">
        <img
          src={`http://localhost:8055/assets/8f79eaaf-1e06-459c-8c81-18f02c8c72f3`}
          alt={title}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
        />
        <Badge className="absolute top-4 right-4 bg-background/90 text-foreground">
          <span>{category.title}</span>
        </Badge>
      </div>
      <CardContent className="flex flex-col flex-1 max">
        <h3 className="text-xl my-0 py-0 pt-2 group-hover:text-primary transition-colors line-clamp-1 font-semibold text-accent">
          {title}
        </h3>
        <div className="flex items-center justify-end gap-2 text-sm text-muted-foreground mb-3">
          <Calendar className="h-4 w-4" />
          <span>{formatDate(date || new Date())}</span>
        </div>
        <div
          className="text-sm text-muted-foreground leading-relaxed mb-4 flex-1 line-clamp-3 [&_img]:hidden [&_h2]:text-base h-[260px] overflow-hidden"
          dangerouslySetInnerHTML={{
            __html: sanitizeHtml(content),
          }}
        />
        <Link
          href={`/news/${id}`}
          className="inline-flex items-center text-sm font-medium text-primary hover:underline"
        >
          Leggi di più
          <ArrowRight className="ml-1 h-3 w-3" />
        </Link>
      </CardContent>
    </Card>
  )
}

const Newsletter = () => (
  <section className="w-full flex justify-center my-6 py-14 bg-primary text-primary-foreground">
    <div className="max-w-4xl text-center">
      <h3 className="text-3xl font-bold mb-6">Resta Sempre Aggiornato</h3>
      <p className="text-lg leading-relaxed mb-8 opacity-90 max-w-xl">
        Iscriviti alla nostra newsletter per ricevere le ultime news, gli
        aggiornamenti e gli eventi e del CAP.
      </p>
      <div className="flex flex-col sm:flex-row gap-y-4 gap-x-1 justify-center max-w-md mx-auto">
        <input
          type="email"
          placeholder="Inserici la tua email..."
          className="flex-1 px-4 py-3 rounded-l-lg text-foreground bg-background/90 focus:outline-none "
        />
        <button className="px-6 py-3 bg-orange-500 rounded-r-lg font-medium hover:bg-secondary/90 transition-colors">
          Iscriviti
        </button>
      </div>
    </div>
  </section>
)

export default async function NewsPage() {
  const { title, description } = await getCategory("news")
  let feeds = await getFeeds("news")
  const featured = feeds.filter(({ featured }) => featured === true).slice(0, 2)
  feeds = feeds.filter(({ featured }) => featured === false)

  return (
    <>
      <PageHero title={title} description={description} />

      <div className="flex flex-col max-w-5xl mx-4 lg:mx-auto ">
        {/* Featured Articles */}
        <div className="grid grid-cols-1 pt-4 md:grid-cols-2 justify-center gap-4">
          {featured.map((feed) => (
            <FeaturedCard key={feed.id} feed={feed} />
          ))}
        </div>

        {/* Articles */}
        {feeds.length > 0 ? (
          <section className="max-w-5xl m-auto bg-muted/50">
            <h3 className="text-3xl font-bold mb-4">Tutte le News</h3>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {feeds.map((feed) => (
                <FeedCard key={feed.id} feed={feed} />
              ))}
            </div>
          </section>
        ) : (
          <div className="w-full flex items-center justify-center gap-2 text-muted-foreground">
            <Rss className="size-6 rotate-y-180" />
            <h3 className="text-3xl mb-8">Nessuna news...</h3>
          </div>
        )}
      </div>

      <Newsletter />
    </>
  )
}
