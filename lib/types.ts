import { UUID } from "crypto"
import { LucideIcon } from "lucide-react"

export type Category = {
  key: string
  title: string
  description?: string
  feeds: Feed[]
  status: string
  sort: number
  user_created: UUID
  date_created: Date
  user_updated: UUID
  date_updated: Date
}

export type Chapter = {
  id: number
  slug?: string
  name: string
  founded: number
  president: string
  website: string
  description: string
  location: string
  members: number
  aircrafts: number
  highlights: string
  user_created: UUID
  date_created: Date
  user_updated: UUID
  date_updated: Date  
}

export type Cover = {
  id: string
  title: string
  width: number
  height: number
  focal_point_x: number
  focal_point_y: number
  user_created: UUID
  date_created: Date
  user_updated: UUID
  date_updated: Date
}

export type Feed = {
  id: number
  author?: string
  category: Category
  cover?: Cover
  content?: string
  date?: Date
  featured?: boolean
  slug?: string
  sort?: number
  status: string
  title?: string
  user_created: UUID
  date_created: Date
  user_updated: UUID
  date_updated: Date    
}

export type Meeting = {
  id: number
  year: number
  place: string
  date: string
  user_created: UUID
  date_created: Date
  user_updated: UUID
  date_updated: Date    
}

export type Metadata = {
  title: string
  description?: string
  phone?: string
  email?: string
  address?: string
  facebook?: string
  twitter?: string
  instagram?: string
  map_type: string
}

export type Page = {
  id: number
  key: string
  title: string
  content?: string
  description?: string
  cover?: Cover
  sections?: PageSection[]
  status: string
  sort: number
  user_created: UUID
  date_created: Date
  user_updated: UUID
  date_updated: Date
}

export type PageSection = {
  id: number
  key: string
  title: string
  content?: string
  status: string
  sort: number
  user_created: UUID
  date_created: Date
  user_updated: UUID
  date_updated: Date
  description?: string
}

export type SubMenuItem = {
  id: number
  title: string
  url: string
  icon: string
  menu: number
  status: string
  sort: number
  user_created: UUID
  date_created: Date
  user_updated: UUID
  date_updated: Date
}

export type MenuItem = {
  id: number
  title: string
  url: string
  submenu?: SubMenuItem[]
  status: string
  sort: number
  user_created: UUID
  date_created: Date
  user_updated: UUID
  date_updated: Date
}

export type MenuIconsMap = Record<string, LucideIcon>

export type DirectusResponse<T> = {
  data: T
}
