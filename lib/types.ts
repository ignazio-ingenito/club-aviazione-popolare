import { UUID } from "crypto"
import { LucideIcon } from "lucide-react"

export type Metadata = {
  title: string
  description?: string
  phone?: string
  email?: string
  address?: string
  facebook?: string
  twitter?: string
  instagram?: string
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