import Link from 'next/link'
import Image from "next/image"

import { Feed } from "@/lib/types"
import { formatDate } from "@/lib/server"

import { Badge } from "../ui/badge"
import { Card, CardContent } from "../ui/card"
import { DEFAULT_COVER, getImageUrl } from "@/lib/directus"

import { Calendar, ArrowRight, User } from "lucide-react"

import * as cheerio from 'cheerio'

interface NewsCardProps {
    feed: Feed
}

function sanitizeHtml(html: string) {
    // Get all text inside p,div tags skip img, h1, h2, h3, h4, h5, h6 using cheerio
    const $ = cheerio.load(html)
    $("img, h1, h2, h3, h4, h5, h6").remove()
    $("div,p,span").contents().unwrap()
    return $.html().replaceAll(/&nbsp;/g, " ")
}

const NewsCard = ({
    feed: { id, author, content, category, date, title, cover }
}: NewsCardProps) => {
    const { width, height, focal_point_x, focal_point_y, title: coverTitle } = cover || DEFAULT_COVER

    // Check if focal point is provided, otherwise default to center (50%)
    const focalPointXPercentage = focal_point_x && focal_point_x >= 0 && focal_point_x <= width
        ? (focal_point_x / width) * 100
        : 50 // Default to center if focal point is missing or invalid

    const focalPointYPercentage = focal_point_y && focal_point_y >= 0 && focal_point_y <= height
        ? (focal_point_y / height) * 100
        : 50 // Default to center if focal point is missing or invalid

    return (
        <Card
            key={id}
            className="overflow-hidden group hover:shadow-lg transition-shadow flex flex-col hover:cursor-pointer"
        >
            <div className="relative h-48 shrink-0 overflow-hidden">
                <Image
                    src={getImageUrl(cover)}
                    width={width}
                    height={height}
                    alt={coverTitle}
                    loading="lazy"
                    quality={90}
                    sizes="(max-width: 768px) 100vw, (max-width: 1280px) 50vw, 33vw"
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    style={{
                        objectPosition: `${focalPointXPercentage}% ${focalPointYPercentage}%`
                    }}
                />
                <Badge className="absolute top-4 right-4 bg-background/90 text-[#0056a4] hover:bg-background/90">
                    {category.title}
                </Badge>
            </div>
            <CardContent className="p-6 flex flex-col flex-1">
                <div className="flex">
                    <div className="flex items-center gap-2 text-sm text-muted-foreground mb-3">
                        <Calendar className="h-4 w-4" />
                        <span>
                            {formatDate(date || new Date())}
                        </span>
                    </div>
                    <div className="flex-1 flex items-center justify-end gap-2 text-sm text-muted-foreground mb-3">
                        <User className="h-4 w-4" />
                        <span>{author}</span>
                    </div>
                </div>
                <span className="text-xl font-bold mt-1 mb-3 text-accent group-hover:text-primary transition-colors line-clamp-1">
                    {title}
                </span>
                {/* text-sm text-muted-foreground leading-relaxed mb-4 flex-1 line-clamp-3 */}
                <div
                    className="overflow-hidden text-sm text-muted-foreground leading-relaxed line-clamp-5 max-h-[8.5rem] block whitespace-normal break-words"
                    dangerouslySetInnerHTML={{ __html: sanitizeHtml(content || "") }}
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

export default NewsCard
