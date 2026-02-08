import Image from "next/image"
import { DEFAULT_COVER, getImageUrl } from "@/lib/directus"

import type { Cover as CoverType } from "@/lib/types"

interface CoverProps {
  cover?: Partial<CoverType>
  className?: string
  description?: string
  offset_x?: number
  offset_y?: number
}

export const Cover = ({ cover, className, description, offset_x, offset_y }: CoverProps) => {
  if (!cover) return null
  const width = cover.width ?? DEFAULT_COVER.width
  const height = cover.height ?? DEFAULT_COVER.height

  return (
    <Image
      priority
      src={getImageUrl(cover, width, height)}
      width={width}
      height={height}
      alt={description || ""}
      className={`object-cover rounded-xs ${className ?? ""}`}
      style={offset_x !== undefined && offset_y !== undefined ? { objectPosition: `${offset_x}% ${offset_y}%` } : {}}
    />
  )
}

export const PageCover = Cover
