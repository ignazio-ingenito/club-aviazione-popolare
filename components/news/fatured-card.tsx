import Link from "next/link"
import Image from "next/image"

import { Feed } from "@/lib/types"
import { DEFAULT_COVER, getImageUrl, sanitizeHtml } from "@/lib/directus"

import { Badge } from "../ui/badge"
import { Card, CardContent } from "../ui/card"

import { ArrowRight } from "lucide-react"

interface FeaturedCardProps {
    feed: Feed
}

const FeaturedCard = ({
    feed: { id, slug, content, title, cover },
}: FeaturedCardProps) => {
    const coverUrl = getImageUrl(cover)
    const html = sanitizeHtml(content)
    const { width, height, focal_point_x, focal_point_y, title: coverTitle } = cover || DEFAULT_COVER

    // Check if focal point is provided, otherwise default to center (50%)
    const focalPointXPercentage = focal_point_x && focal_point_x >= 0 && focal_point_x <= width
        ? (focal_point_x / width) * 100
        : 50 // Default to center if focal point is missing or invalid

    const focalPointYPercentage = focal_point_y && focal_point_y >= 0 && focal_point_y <= height
        ? (focal_point_y / height) * 100
        : 50 // Default to center if focal point is missing or invalid

    return (
        <Card key={id} className="relative overflow-hidden group flex min-h-[25rem] sm:min-h-0 mb-1 hover:shadow-lg transition-shadow">
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
            <CardContent className="overflow-hidden px-6 pt-10 pb-4 flex flex-col flex-1 min-w-0">
                <section className="text-xl font-bold mb-2 text-accent group-hover:text-primary transition-colors line-clamp-2">
                    {title}
                </section>
                <section className="mt-2 flex-1 overflow-hidden line-clamp-7 text-ellipsis">
                    <div
                        className="text-muted-foreground"
                        dangerouslySetInnerHTML={{ __html: html }}
                    />
                </section>
                <section className="pt-4 p-0 flex items-center justify-end text-primary hover:underline cursor-pointer">
                    <Link href={`/news/${slug}`} className="text-sm inline-flex items-center">
                        Leggi l&apos;articolo completo
                        <ArrowRight className="ml-2 size-4" />
                    </Link>
                </section>
            </CardContent>
        </Card >
    )
}

export default FeaturedCard
