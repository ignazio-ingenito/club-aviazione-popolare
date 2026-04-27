import Link from "next/link"
import Image from "next/image"

import { Feed } from "@/lib/types"
import { DEFAULT_COVER, getImageUrl, sanitizeHtml } from "@/lib/directus"

import { Badge } from "../ui/badge"
import { Card, CardContent } from "../ui/card"

import { ArrowRight } from "lucide-react"

import * as cheerio from 'cheerio'
interface FeaturedCardProps {
    feed: Feed
}

const removeTags = (html: string) => {
    const $ = cheerio.load(html)
    $("img, h1, h2, h3, h4, h5, h6").remove()
    $("div,p,span").contents().unwrap()
    return $.html().replaceAll(/&nbsp;/g, " ")
}

const FeaturedCard = ({
    feed: { id, slug, content, title, cover },
}: FeaturedCardProps) => {
    const coverUrl = getImageUrl(cover)
    const html = removeTags(sanitizeHtml(content))


    const { width, height, focal_point_x, focal_point_y, title: coverTitle } = cover || DEFAULT_COVER

    // Check if focal point is provided, otherwise default to center (50%)
    const focalPointXPercentage = focal_point_x && focal_point_x >= 0 && focal_point_x <= width
        ? (focal_point_x / width) * 100
        : 50 // Default to center if focal point is missing or invalid

    const focalPointYPercentage = focal_point_y && focal_point_y >= 0 && focal_point_y <= height
        ? (focal_point_y / height) * 100
        : 50 // Default to center if focal point is missing or invalid

    return (
        <Link href={`/news/${slug}`} className="block rounded-xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2">
            <Card key={id} className="relative overflow-hidden group flex h-[25rem] sm:h-84 mb-1 hover:shadow-lg transition-shadow">
                <div className="relative w-2/5 shrink-0 overflow-hidden">
                    <Image
                        src={coverUrl}
                        width={width}
                        height={height}
                        alt={coverTitle}
                        loading="lazy"
                        quality={90}
                        sizes="40vw"
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                        style={{
                            objectPosition: `${focalPointXPercentage}% ${focalPointYPercentage}%`
                        }}
                    />
                </div>
                <Badge className="absolute top-4 right-4 rounded-xs font-semibold">
                    in Evidenza
                </Badge>
                <CardContent className="px-6 pt-10 pb-4 flex flex-col flex-1 min-w-0">
                    <section className="text-xl font-bold mb-2 text-accent group-hover:text-primary transition-colors line-clamp-2">
                        {title}
                    </section>
                    <section className="mt-2 mb-4 text-ellipsis text-muted-foreground line-clamp-7"
                        dangerouslySetInnerHTML={{ __html: html }}>
                    </section>
                    <section className="w-full flex justify-end text-primary group-hover:underline cursor-pointer shrink-0 mt-auto">
                        <span className="text-sm text-primary inline-flex items-center">
                            Leggi l&apos;articolo
                            <ArrowRight className="ml-2 size-4" />
                        </span>
                    </section>
                </CardContent>
            </Card >
        </Link>
    )
}

export default FeaturedCard
