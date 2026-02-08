"use client"

import Image from "next/image"
import Link from "next/link"
import { useState } from "react"

import { ThemeToggle } from "@/components/theme-toggle"
import { Button } from "@/components/ui/button"
import { Sheet, SheetContent, SheetTitle, SheetTrigger } from "@/components/ui/sheet"
import { useScrolled } from "@/lib/useScrolled"

import darkLogo from "@/app/public/logo-dark.svg"
import lightLogo from "@/app/public/logo-light.svg"
import {
    Accordion,
    AccordionContent,
    AccordionItem,
    AccordionTrigger,
} from "@/components/ui/accordion"
import {
    NavigationMenu,
    NavigationMenuContent,
    NavigationMenuItem,
    NavigationMenuLink,
    NavigationMenuList,
    NavigationMenuTrigger,
} from "@/components/ui/navigation-menu"
import { MenuItem } from "@/lib/types"
import { Menu } from "lucide-react"
import { HeaderContacts } from "./contacts"
import { HeaderSocials } from "./socials"
import { LucideIcon } from "../lucide-icon"

export type HeaderProps = {
    title?: string
    description?: string
    phone?: string
    email?: string
    facebookUrl?: string
    instagramUrl?: string
    twitterUrl?: string
    menu?: MenuItem[]
}

export function Header({
    title = "",
    phone,
    email,
    facebookUrl,
    instagramUrl,
    twitterUrl,
    menu = [],
}: HeaderProps) {
    const [open, setOpen] = useState(false)
    const [accordionValue, setAccordionValue] = useState<string | undefined>(undefined)
    const isScrolled = useScrolled({ threshold: 10 })
    const menuItems: MenuItem[] = Array.isArray(menu)
        ? menu
        : Array.isArray((menu as unknown as { data?: unknown })?.data)
            ? ((menu as unknown as { data: MenuItem[] }).data ?? [])
            : []

    return (
        <header
            className={`fixed z-50 top-0 w-full transition-all duration-300 ${isScrolled
                ? "backdrop-blur supports-backdrop-filter:bg-background/85 border-b border-border/40 shadow-md"
                : "bg-transparent"
                }`}
        >
            <div className="max-w-7xl mx-8 xl:mx-auto">
                <div className="flex h-16 items-center justify-between gap-4">
                    <Link
                        href="/" className="relative flex items-center" aria-label={`${title} — Home`}>
                        <section className="relative w-40 h-16 py-1">
                            <Image
                                src={isScrolled ? darkLogo.src : lightLogo.src}
                                alt={title || "Logo"}
                                className="top-0 left-0 object-contain object-center"
                                fill
                                priority
                            />
                        </section>
                    </Link>

                    {/* Desktop navigation */}
                    <nav className="hidden lg:flex items-center gap-1 flex-1 justify-center" aria-label="desktop menu">
                        <NavigationMenu>
                            <NavigationMenuList>
                                {menuItems.map(({ id, url, title, submenu }) => {
                                    const submenuItems = Array.isArray(submenu) ? submenu : []
                                    if (submenuItems.length > 0) {
                                        return (
                                            <NavigationMenuItem key={title} data-submenu-len={submenuItems.length}>
                                                <NavigationMenuTrigger className={`${isScrolled ? "text-accent" : "text-white"} text-sm font-medium bg-transparent cursor-pointer transition-all`}>
                                                    {title}
                                                </NavigationMenuTrigger>
                                                <NavigationMenuContent className="p-3">
                                                    <div className={`max-w-screen w-[600px] grid gap-1 grid-flow-col grid-cols-2 grid-rows-${submenuItems.length / 2}`}>
                                                        {submenuItems.map(({ id, url, title, icon }) => {
                                                            return (
                                                                <NavigationMenuLink asChild className="p-3 text-accent hover:text-secondary" key={id}>
                                                                    <Link href={url}
                                                                        className="block select-none p-3 leading-none no-underline outline-none transition-all hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground">
                                                                        <section className="text-sm font-medium leading-none flex items-center gap-x-2">
                                                                            <LucideIcon name={icon} className="size-5" /> {title}
                                                                        </section>
                                                                    </Link>
                                                                </NavigationMenuLink>
                                                            )
                                                        })}
                                                    </div>
                                                </NavigationMenuContent>
                                            </NavigationMenuItem>

                                        )
                                    }
                                    return (
                                        <NavigationMenuItem key={id}>
                                            <NavigationMenuLink asChild>
                                                <Link
                                                    href={url ?? "#"}
                                                    className={`${isScrolled ? "text-accent hover:text-white" : "text-white"} group inline-flex h-10 w-max items-center justify-center rounded-md px-4 py-2 text-sm font-medium text-primary hover:text-secondary hover:bg-accent transition-colors`}
                                                >
                                                    {title}
                                                </Link>
                                            </NavigationMenuLink>
                                        </NavigationMenuItem>
                                    )
                                })}
                            </NavigationMenuList>
                        </NavigationMenu>
                    </nav>

                    <div className="flex items-center justify-center gap-3 shrink-0">
                        {/* Contacts (desktop XL) */}
                        <div className="hidden xl:flex items-center gap-3">
                            <HeaderContacts
                                className="hover:scale-150 transition-all ease-in-out duration-300"
                                isScrolled={isScrolled}
                                phone={phone}
                                email={email}
                                textColor="text-accent"
                                scrolledTextColor="text-white"
                                scrolledTextColorHover="text-accent"
                            />
                        </div>
                        <HeaderSocials
                            className="flex items-center gap-3"
                            isScrolled={isScrolled}
                            facebookUrl={facebookUrl}
                            instagramUrl={instagramUrl}
                            twitterUrl={twitterUrl}
                            textColor="text-accent"
                            scrolledTextColor="text-white"
                            scrolledTextColorHover="text-accent"
                        />

                        <ThemeToggle className={isScrolled ? "text-accent" : "text-white"} />

                        {/* Mobile menu */}
                        <Sheet open={open} onOpenChange={setOpen}>
                            <SheetTrigger asChild className="lg:hidden">
                                <Button variant="ghost" size="icon" aria-label="Apri menu">
                                    <Menu className={`h-5 w-5 ${isScrolled ? "text-accent hover:text-red-500" : "text-white"}`} />
                                </Button>
                            </SheetTrigger>
                            <SheetContent side="right" className="w-[300px] sm:w-[400px] focus:ring-0 focus:ring-transparent focus:ring-offset-0">
                                <SheetTitle className="sr-only">Menu di navigazione</SheetTitle>
                                <nav className="flex flex-col pt-8 transition-all" aria-label="Menu mobile">
                                    <Accordion
                                        type="single"
                                        collapsible
                                        value={accordionValue}
                                        onValueChange={(v) => setAccordionValue(v ?? undefined)}
                                        className="flex flex-col"
                                    >
                                        {menuItems.map(({ id, url, title, submenu }) => {
                                            const submenuItems = Array.isArray(submenu) ? submenu : []

                                            if (submenuItems.length > 0) {
                                                return (
                                                    <AccordionItem value={`${id}`} key={id}>
                                                        <AccordionTrigger>{title}</AccordionTrigger>
                                                        {submenuItems.map(({ id: sid, url: surl, title: stitle, icon }) => {
                                                            return (
                                                                <AccordionContent
                                                                    key={sid}
                                                                    className="flex items-center p-4 gap-x-4 hover:bg-accent hover:text-accent-foreground hover:underline"
                                                                >
                                                                    <LucideIcon name={icon} className="size-5" />
                                                                    <Link
                                                                        className="text-sm transition-all outline-none"
                                                                        href={surl ?? "#"}
                                                                        onClick={() => setOpen(false)}
                                                                    >
                                                                        {stitle}
                                                                    </Link>
                                                                </AccordionContent>
                                                            )
                                                        })}
                                                    </AccordionItem>
                                                )
                                            }

                                            return (
                                                <div key={id} className="py-4 border-b">
                                                    <Link
                                                        className="text-left text-sm font-medium transition-all outline-none hover:underline"
                                                        href={url ?? "#"}
                                                        onClick={() => setOpen(false)}
                                                    >
                                                        {title}
                                                    </Link>
                                                </div>
                                            )
                                        })}
                                    </Accordion>
                                    <div className="flex flex-col gap-3 pt-10 border-t text-sm text-muted-foreground">
                                        <HeaderContacts
                                            className="flex items-center gap-2 hover:text-foreground transition-colors"
                                            isScrolled={isScrolled}
                                            phone={phone}
                                            email={email}
                                            showText={true}
                                            scrolledTextColorHover="hover:text-foreground" />

                                        <HeaderSocials
                                            className="text-foreground flex items-center gap-6 mt-2"
                                            isScrolled={isScrolled}
                                            facebookUrl={facebookUrl}
                                            instagramUrl={instagramUrl}
                                            twitterUrl={twitterUrl}
                                        />
                                    </div>
                                </nav>
                            </SheetContent>
                        </Sheet>
                    </div>
                </div>
            </div>
        </header>
    )
}
