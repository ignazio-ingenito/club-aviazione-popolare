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
        <Card key={id} className="relative p-6 pb-4 mb-1">
            <Badge className="absolute top-2 right-2 rounded-xs font-semibold">
                in Evidenza
            </Badge>
            <CardContent className="overflow-hidden p-0 m-0">
                <section className="pt-3 pb-1 text-2xl text-accent whitespace-nowrap overflow-hidden text-ellipsis uppercase">
                    {title}
                </section>
                <section className="h-54 overflow-hidden line-clamp-9 text-ellipsis">
                    <Image
                        src={coverUrl}
                        width={width}
                        height={height}
                        alt={coverTitle}
                        loading="lazy"
                        className="float-left object-cover pr-2 pt-2 w-[40%]"
                        style={{
                            objectPosition: `${focalPointXPercentage}% ${focalPointYPercentage}%`
                        }}
                    />
                    <div
                        className="text-muted-foreground"
                        dangerouslySetInnerHTML={{ __html: html }}
                    />
                </section>
                <section className="pt-4 p-0 flex items-center justify-end text-primary hover:underline cursor-pointer">
                    <Link href={`/news/${slug}`} className="text-sm inline-flex items-center">
                        Leggi l'articolo completo
                        <ArrowRight className="ml-2 size-4" />
                    </Link>
                </section>
            </CardContent>
        </Card >
    )
}

export default FeaturedCard