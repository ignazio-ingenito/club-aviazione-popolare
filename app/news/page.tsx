import Link from "next/link"
import * as cheerio from 'cheerio'

import { Badge } from "@/components/ui/badge"
import { PageHero } from "@/components/page/hero"
import { Card, CardContent } from "@/components/ui/card"

import { Feed } from "@/lib/types"
import { getCategory, getFeeds, sanitizeHtml } from "@/lib/server"

import { Calendar, ArrowRight, User, Rss } from "lucide-react"

function parseFeatured(html: string): [string, string] {
  const $ = cheerio.load(html)
  const cover = $("img").first().attr("src") || `${process.env.WEB_NEWS_COVER}`
  $("img").remove()

  return [cover, $.html()]
}

const formatDate = (date: Date | undefined): string =>
  (date ? date : new Date())
    .toLocaleDateString("it", { day: "2-digit", month: "short", year: "numeric" })
    .replaceAll(/\s+/g, "-")

interface FeaturedCardProps {
  feed: Feed
}
const FeaturedCard = ({ feed: { id, content, category, date, title } }: FeaturedCardProps) => {
  const [cover, html] = parseFeatured(sanitizeHtml(content ?? ""))

  return (
    <Card className="relative text-ellipsis hover:shadow-md transition-shadow overflow-hidden">
      <CardContent className="relative pt-6 flex flex-col justify-center overflow-hidden">
        <h2 className="overflow-hidden m-0 pt-2 pb-3 text-2xl text-accent whitespace-nowrap text-ellipsis">{title}</h2>
        <section className="h-[245px] overflow-hidden text-ellipsis">
          <img src={cover} alt={`${title}`} className="float-left object-cover pr-2 mt-1 w-[40%]" />
          <div
            className="text-muted-foreground"
            dangerouslySetInnerHTML={{ __html: html }}
          />
        </section>
        <section className="absolute top-2 right-2 flex gap-x-1 text-xs">
          <Badge className="rounded-xs cursor-pointer font-normal">in Evidenza</Badge>
          {/* <Badge className="rounded-full cursor-pointer font-normal">{category.title}</Badge> */}
          {/* <Badge className="flex items-center py-1 gap-x-1 rounded-full cursor-pointer font-normal">{formatDate(date)}</Badge> */}
        </section>
        <Link
          href={`/news/${id}`}
          className="my-4 inline-flex items-center text-primary justify-end text-sm hover:underline"
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
const FeedCard = ({ feed: { id, author, content, category, date, title } }: FeedCardProps) => <Card
  key={id}
  className="overflow-hidden group hover:shadow-lg transition-shadow flex flex-col"
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
  <CardContent className="p-6 flex flex-col flex-1">
    <div className="flex items-center gap-2 text-sm text-muted-foreground mb-3">
      <Calendar className="h-4 w-4" />
      <span>
        {date ? new Date(date).toLocaleDateString("it", { day: "2-digit", month: "short", year: "numeric" }) : ""}
      </span>
    </div>
    <h3 className="text-xl font-bold mb-3 group-hover:text-primary transition-colors line-clamp-2">
      {title}
    </h3>
    <div className="flex items-center gap-2 text-sm text-muted-foreground mb-3">
      <User className="h-4 w-4" />
      <span>{author}</span>
    </div>
    <div
      className="text-sm text-muted-foreground leading-relaxed mb-4 flex-1 line-clamp-3"
      dangerouslySetInnerHTML={{ __html: parseFeatured(sanitizeHtml(content)) }}
    />
    <Link
      href={`/news/${id}`}
      className="inline-flex items-center text-sm font-medium text-primary hover:underline"
    >
      Leggi di più
      <ArrowRight className="ml-1 h-3 w-3" />
    </Link>
  </CardContent>
</Card >

const Newsletter = () => <section className="w-full flex justify-center py-16 bg-primary text-primary-foreground">
  <div className="max-w-4xl text-center">
    <h2 className="text-3xl font-bold mb-6">Resta Sempre Aggiornato</h2>
    <p className="text-lg leading-relaxed mb-8 opacity-90 max-w-xl">
      Iscriviti alla nostra newsletter per ricevere le ultime news, gli aggiornamenti e gli eventi e del CAP.
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

export default async function NewsPage() {
  const { title, description } = await getCategory("news")
  let feeds = await getFeeds("news")
  const featured = feeds.filter(({ featured }) => featured === true).slice(0, 4)
  feeds = feeds.filter(({ featured }) => featured === false)

  return (
    <>
      <PageHero title={title} description={description} />

      {/* max-w-7xl m-auto */}
      <div className="flex flex-col">
        {/* Featured Articles */}
        {/* <div className="w-full py-4 flex gap-4 flex-wrap justify-center overflow-hidden bg-muted/50"> */}
        <div className="grid md:grid-cols-2 xl:grid-cols-4 justify-center gap-4 p-4">
          {
            featured.map((feed) => <FeaturedCard key={feed.id} feed={feed} />)
          }
        </div>

        {/* Articles */}
        {
          feeds.length > 0
            ? <section className="bg-muted/50">
              <h2 className="text-3xl font-bold mb-8">Tutte le News</h2>
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
                {feeds.map((feed) => <FeedCard key={feed.id} feed={feed} />)}
              </div>
            </section>
            : <div className="w-full flex items-center justify-center gap-2 text-muted-foreground">
              <Rss className="size-6 rotate-y-180" />
              <h2 className="text-3xl mb-8">Nessuna news...</h2>
            </div>
        }
      </div >

      <Newsletter />
    </>
  )
}