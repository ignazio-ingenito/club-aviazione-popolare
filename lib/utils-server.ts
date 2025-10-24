import sanitize from "sanitize-html"
import { twMerge } from "tailwind-merge"
import { clsx, type ClassValue } from "clsx"
import { unstable_noStore as noStore } from "next/cache"
import { MenuIconsMap, MenuItem, Metadata, Page } from "./utils-types"
import { createDirectus, readItem, readItems, readSingleton, rest } from "@directus/sdk"
import {
  BookText,
  Calendar1,
  Coins,
  Drill,
  GraduationCap,
  HardHat,
  Home,
  LibraryBig,
  MapPinHouse,
  MessagesSquare,
  Network,
  Newspaper,
  NotebookText,
  Plane,
  PlaneTakeoff,
  Rss,
  Share2,
  Speech,
  TrafficCone,
  Trophy,
  UserPlus2,
  Wrench
} from "lucide-react"
import ShieldUser from "lucide-react/dist/esm/icons/shield-user"
import { Engine } from "@/components/svg/Engine"


export const cn = (...inputs: ClassValue[]) => twMerge(clsx(inputs))
export const directus = createDirectus(process.env.DIRECTUS_URL ?? "http://localhost:8055").with(rest())

export const getMetadata = async (): Promise<Metadata> => {
  noStore() // prevent caching
  return await directus.request(readSingleton("metadata")) as Metadata
}

export const getMenu = async (): Promise<MenuItem[]> => {
  noStore() // prevent caching
  const menu = await directus.request(readItems("site_menu", {
    fields: ["*", "submenu.*"],
    filter: { status: { _eq: "published" } },
    sort: ["sort"],
    deep: { submenu: { filter: { status: { _eq: 'published' } }, sort: ['sort'] } },
  }))
  return menu as MenuItem[]
}

export const getPage = async (key: string): Promise<Page> => {
  noStore() // prevent caching
  // return await directus.request(readItem("pages", key)) as Page
  const page = await directus.request(readItem("pages", key, {
    fields: ["*", "sections.*"],
    filter: { status: { _eq: "published" } },
    deep: { sections: { filter: { status: { _eq: 'published' } }, sort: ['sort'] } },
  }))
  return page as Page
}

// solo per componenti server
export const sanitizeHtml = (html: string) => {
  return sanitize(html, {
    allowedTags: sanitize.defaults.allowedTags.concat(["img"]),
    allowedAttributes: {
      ...sanitize.defaults.allowedAttributes,
      img: ["src", "alt", "title", "width", "height", "loading", "decoding"],
      a: ["href", "name", "target", "rel"],
    },
    // se vuoi forzare rel noopener su link esterni:
    transformTags: {
      a: (tagName: string, attribs: any) => ({
        tagName: "a",
        attribs: {
          ...attribs,
          rel: attribs.target === "_blank" ? "noopener noreferrer" : attribs.rel,
        },
      }),
    },
  })
}

export const getMenuIcons = (): MenuIconsMap => ({
  "/": Home,
  "/albo-storico": NotebookText,
  "/cosa-facciamo": TrafficCone,
  "/costruire-un-aereo": Wrench,
  "/diventa-uno-di-noi": UserPlus2,
  "/la-nostra-storia": LibraryBig,
  "/le-nostre-sezioni": MapPinHouse,
  "/organigramma": Network,
  "/corsi": GraduationCap,
  "/eventi": Calendar1,
  "/storie": Speech,
  "/trofeo-caproni": Trophy,
  "/trofeo-rotondi": Trophy,
  "/trofeo-aldinio": Trophy,
  "/efficency-race": Trophy,
  "/news": Rss,
  "/notiziari": Newspaper,
  "/le-storie-dei-soci": Speech,
  "/riviste": BookText,
  "/convenzioni": Coins,
  "/costruzioni": Drill,
  "/flotta": Plane,
  "/impianti": Share2,
  "/manutenzione": Wrench,
  "/motori": Engine,
  "/prove-di-volo": PlaneTakeoff,
  "/seminari-tecnici": MessagesSquare,
  "/sicurezza": HardHat,
  "/sport-aviation": Newspaper,
  "/tecnici": ShieldUser,
})