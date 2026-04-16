import * as cheerio from "cheerio"

import { DEFAULT_COVER, getImageUrl } from "@/lib/directus"
import type { Feed } from "@/lib/types"

export type NewsListItem = {
  id: number
  author?: string
  categoryTitle: string
  content: string
  coverTitle: string
  coverUrl: string
  date: string
  focalPointXPercentage: number
  focalPointYPercentage: number
  height: number
  title?: string
  width: number
}

const sanitizePreview = (html: string = "") => {
  const $ = cheerio.load(html)
  $("img, h1, h2, h3, h4, h5, h6").remove()
  $("div,p,span").contents().unwrap()
  return $.html().replaceAll(/&nbsp;/g, " ")
}

export const toNewsListItem = (feed: Feed): NewsListItem => {
  const cover = feed.cover || DEFAULT_COVER
  const { width, height, focal_point_x, focal_point_y, title: coverTitle } = cover
  const focalPointXPercentage =
    focal_point_x && focal_point_x >= 0 && focal_point_x <= width
      ? (focal_point_x / width) * 100
      : 50
  const focalPointYPercentage =
    focal_point_y && focal_point_y >= 0 && focal_point_y <= height
      ? (focal_point_y / height) * 100
      : 50

  return {
    id: feed.id,
    author: feed.author,
    categoryTitle: feed.category.title,
    content: sanitizePreview(feed.content || ""),
    coverTitle,
    coverUrl: getImageUrl(cover),
    date: (feed.date || new Date()).toISOString(),
    focalPointXPercentage,
    focalPointYPercentage,
    height,
    title: feed.title,
    width,
  }
}
