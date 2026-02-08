import Image from "next/image"
import { DEFAULT_COVER, getImageUrl } from "@/lib/directus"

import type { Cover as CoverType } from "@/lib/types"

interface CoverProps {
  cover?: Partial<CoverType>
  className?: string
  description?: string
}

export const Cover = ({ cover, className, description }: CoverProps) => {
  if (!cover) return null
  const width = cover.width ?? DEFAULT_COVER.width
  const height = cover.height ?? DEFAULT_COVER.height

  return (
    <Image
      src={getImageUrl(cover, width, height)}
      width={width}
      height={height}
      alt={description || ""}
      className={`object-cover rounded-xs ${className ?? ""}`}
      priority
    />
  )
}

export const PageCover = Cover
