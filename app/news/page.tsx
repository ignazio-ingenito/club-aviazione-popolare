
import { PageHero } from "@/components/page/hero"

import { getCategory, getFeeds } from "@/lib/server"

import { Rss } from "lucide-react"
import FeaturedCard from "@/components/news/fatured-card"
import Newsletter from "@/components/news/news-letter"
import NewsCard from "@/components/news/news-card"
import { Feed } from "@/lib/types"

export default async function NewsPage() {
  const { title, description } = await getCategory("news")
  const all: Feed[] = await getFeeds("news")
  const featured: Feed[] = all.filter(({ featured }) => featured === true).slice(0, 4)
  const news: Feed[] = all.filter(({ featured }) => featured === false)

  return (
    <>
      <PageHero title={title} description={description} />

      <div className="px-4 sm:px-8">
        <div className="max-w-5xl m-auto flex flex-col">
          {/* Featured Articles */}
          <section>
            <h3 className="text-3xl font-bold mb-2">In evidenza...</h3>
            <div className="grid grid-cols-[repeat(auto-fit,minmax(320px,1fr))] gap-x-2 h-86 overflow-hidden">
              {featured.map((feed) => (
                <FeaturedCard key={feed.id} feed={feed} />
              ))}
            </div>
          </section>

          {/* News */}
          <section>
            {news.length > 0 ? (
              <>
                <h3 className="text-3xl font-bold">Tutte le News...</h3>
                <div className="py-4 grid grid-cols-[repeat(auto-fit,minmax(350px,1fr))] gap-2">
                  {news.map((feed) =>
                    <NewsCard key={feed.id} feed={feed} />
                  )}
                </div>
              </>
            ) : (
              <div className="w-full flex items-center justify-center gap-x-2">
                <Rss className="size-8 rotate-y-180" />
                <div className="py-8 text-3xl font-semibold">Nessuna news...</div>
              </div>
            )}
          </section>
        </div>
      </div>

      <Newsletter />
    </>
  )
}
