"use client"

import { useEffect, useRef, useState } from "react"
import Image from "next/image"
import Link from "next/link"

import type { NewsListItem } from "@/lib/news-list"
import { ArrowRight, Calendar, Rss, User } from "lucide-react"
import { Badge } from "../ui/badge"
import { Card, CardContent } from "../ui/card"

interface InfiniteNewsListProps {
  excludeIds?: number[]
  initialHasMore: boolean
  initialItems: NewsListItem[]
  pageSize: number
}

export const NewsListCard = ({
  imagePosition = "top",
  item,
}: {
  imagePosition?: "left" | "top"
  item: NewsListItem
}) => (
  <Link
    href={`/news/${item.id}`}
    className="block h-full rounded-xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
  >
    <Card
      className={`h-full overflow-hidden group hover:shadow-lg transition-shadow flex hover:cursor-pointer ${imagePosition === "left" ? "flex-col sm:flex-row" : "flex-col max-h-[400px]"
        }`}
    >
      <div
        className={`relative shrink-0 overflow-hidden ${imagePosition === "left" ? "h-48 sm:h-auto sm:w-2/5" : "h-[9.6rem] sm:h-[12rem]"
          }`}
      >
        <Image
          src={item.coverUrl}
          width={item.width}
          height={item.height}
          alt={item.coverTitle}
          loading="lazy"
          quality={90}
          sizes={
            imagePosition === "left"
              ? "(max-width: 640px) 100vw, 40vw"
              : "(max-width: 768px) 100vw, (max-width: 1280px) 50vw, 33vw"
          }
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          style={{
            objectPosition: `${item.focalPointXPercentage}% ${item.focalPointYPercentage}%`,
          }}
        />
        <Badge className="absolute top-4 right-4 bg-background/90 text-[#0056a4] hover:bg-background/90">
          {item.categoryTitle}
        </Badge>
      </div>
      <CardContent className="px-6 pt-4 pb-6 flex flex-col flex-1 min-w-0 min-h-0">
        <span className="text-xl font-bold mb-2 text-accent group-hover:text-primary transition-colors line-clamp-2">
          {item.title}
        </span>
        <div className="flex shrink-0">
          <div className="flex items-center gap-2 text-sm text-muted-foreground mb-3">
            <Calendar className="h-4 w-4" />
            <span>
              {new Date(item.date)
                .toLocaleDateString("it", {
                  year: "numeric",
                  month: "short",
                  day: "numeric",
                })
                .replaceAll(/\s+/g, "-")
                .toLowerCase()}
            </span>
          </div>
          <div className="flex-1 flex items-center justify-end gap-2 text-sm text-muted-foreground mb-3">
            <User className="h-4 w-4" />
            <span className="truncate">{item.author}</span>
          </div>
        </div>
        <p className="mb-4 text-sm text-muted-foreground leading-6 line-clamp-4 whitespace-normal break-words">
          {item.content}
        </p>
        <span className="inline-flex items-center mt-auto shrink-0 text-sm font-medium text-primary group-hover:underline">
          Leggi di più
          <ArrowRight className="ml-1 h-3 w-3" />
        </span>
      </CardContent>
    </Card>
  </Link>
)

export default function InfiniteNewsList({
  excludeIds = [],
  initialHasMore,
  initialItems,
  pageSize,
}: InfiniteNewsListProps) {
  const [items, setItems] = useState(initialItems)
  const [hasMore, setHasMore] = useState(initialHasMore)
  const [loading, setLoading] = useState(false)
  const sentinelRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    if (!hasMore || loading) return

    const target = sentinelRef.current
    if (!target) return

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (!entry.isIntersecting) return
        setLoading(true)
        const params = new URLSearchParams({
          exclude: excludeIds.join(","),
          limit: String(pageSize),
          offset: String(items.length),
        })
        fetch(`/api/news?${params}`)
          .then((response) => response.json())
          .then((payload: { items: NewsListItem[]; hasMore: boolean }) => {
            setItems((current) => [...current, ...payload.items])
            setHasMore(payload.hasMore)
          })
          .finally(() => setLoading(false))
      },
      { rootMargin: "400px 0px" }
    )

    observer.observe(target)
    return () => observer.disconnect()
  }, [excludeIds, hasMore, items.length, loading, pageSize])

  if (!items.length) {
    return (
      <div className="w-full flex items-center justify-center gap-x-2">
        <Rss className="size-8 rotate-y-180" />
        <div className="py-8 text-3xl font-semibold">Nessuna news...</div>
      </div>
    )
  }

  return (
    <>
      <div className="py-4 grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-2">
        {items.map((item) => (
          <NewsListCard key={item.id} item={item} />
        ))}
      </div>
      <div ref={sentinelRef} className="h-10" />
      {loading && (
        <p className="pb-6 text-center text-sm text-muted-foreground">
          Caricamento...
        </p>
      )}
    </>
  )
}
