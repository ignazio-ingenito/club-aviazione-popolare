import { UUID } from "crypto"
import { LucideIcon } from "lucide-react"

export type Category = {
  id: number
  description: string
  feeds: Feed[]
  status: string
  sort: number
  title: string
}

export type Chapter = {
  name: string
  founded: number
  president: string
  website: string
  description: string
  link: string
  location: string
  members: number
  aircrafts: number
  highlights: string
}

export type Feed = {
  id: number
  author?: string
  category: Category
  content?: string
  date?: Date
  featured?: boolean
  slug?: string
  sort?: number
  status: string
  title?: string
}

export type Meeting = {
  id: number
  year: number
  place: string
  date: string
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
  content_title?: string
  content?: string
  sections?: PageSection[]
  status: string
  sort: number
  user_created: UUID
  date_created: Date
  user_updated: UUID
  date_updated: Date
  description?: string
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