
import { PageHero } from "@/components/page/hero"

import { getCategory, getFeeds } from "@/lib/server"

import FeaturedCard from "@/components/news/fatured-card"
import InfiniteNewsList from "@/components/news/infinite-news-list"
import Newsletter from "@/components/news/news-letter"
import { toNewsListItem } from "@/lib/news-list"
import { Feed } from "@/lib/types"

const NEWS_PAGE_SIZE = 9

export default async function NewsPage() {
  const { title, description } = await getCategory("news")
  const all: Feed[] = await getFeeds("news")
  const markedFeatured: Feed[] = all.filter(({ featured }) => featured === true)
  const featured: Feed[] = markedFeatured.length > 0
    ? markedFeatured.slice(0, 4)
    : all.slice(0, 2)
  const featuredIds = new Set(featured.map(({ id }) => id))
  const news: Feed[] = all.filter(({ id }) => !featuredIds.has(id))
  const initialNews = news.slice(0, NEWS_PAGE_SIZE).map(toNewsListItem)

  return (
    <>
      <PageHero title={title} description={description} />

      <div className="px-4 sm:px-8">
        <div className="max-w-5xl m-auto flex flex-col">
          {/* Featured Articles */}
          <section>
            <h3 className="text-3xl font-bold mb-2">In evidenza...</h3>
            <div className="grid grid-cols-[repeat(auto-fit,minmax(320px,1fr))] gap-2 sm:h-84 sm:overflow-hidden">
              {featured.map((feed) => (
                <FeaturedCard key={feed.id} feed={feed} />
              ))}
            </div>
          </section>

          {/* News */}
          <section>
            <h3 className="text-3xl font-bold">Tutte le News...</h3>
            <InfiniteNewsList
              excludeIds={[...featuredIds]}
              initialHasMore={news.length > NEWS_PAGE_SIZE}
              initialItems={initialNews}
              pageSize={NEWS_PAGE_SIZE}
            />
          </section>
        </div>
      </div>

      <Newsletter />
    </>
  )
}
