"use client"

import Link from "next/link"
import Image from "next/image"
import { useState } from "react"
import { useWindowScroll } from "react-use"

import { Button } from "@/components/ui/button"
import { ThemeToggle } from "@/components/theme-toggle"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"

import { useScrolled } from "@/lib/useScrolled"
import darkLogo from "@/app/public/logo-dark.svg"
import lightLogo from "@/app/public/logo-light.svg"
import { Mail, Phone, Facebook, Twitter, Menu, Home, UserPlus2, Wrench, MapPinHouse, Network, NotebookText, TrafficCone, LibraryBig, GraduationCap, Calendar1, Trophy, Speech } from "lucide-react"
import {
    NavigationMenu,
    NavigationMenuContent,
    NavigationMenuItem,
    NavigationMenuLink,
    NavigationMenuList,
    NavigationMenuTrigger,
} from "@/components/ui/navigation-menu"

export type HeaderHomeProps = {
    title?: string
    description?: string
    phone?: string
    email?: string
    facebookUrl?: string
    twitterUrl?: string
}

export function HeaderHome({
    title = "",
    phone,
    email,
    facebookUrl,
    twitterUrl,
}: HeaderHomeProps) {
    const [open, setOpen] = useState(false)
    const { y } = useWindowScroll()
    const isScrolled = useScrolled({ threshold: 10 })

    const telHref = phone ? `tel:${phone.replace(/\s+/g, "")}` : undefined
    const mailHref = email ? `mailto:${email}` : undefined

    const nav = [
        { name: "Home", href: "/", icon: Home },
        {
            name: "Chi Siamo",
            href: "/chi-siamo",
            submenu: [
                { name: "Albo storico", href: "/albo-storico", icon: NotebookText },
                { name: "Cosa facciamo", href: "/cosa-facciamo", icon: TrafficCone },
                { name: "Costruire un aereo", href: "/costruire-un-aereo", icon: Wrench },
                { name: "Diventa uno di noi", href: "/diventa-uno-di-noi", icon: UserPlus2 },
                { name: "La nostra storia", href: "/la-nostra-storia", icon: LibraryBig },
                { name: "Le nostre sezioni", href: "/le-nostre-sezioni", icon: MapPinHouse },
                { name: "Organigramma", href: "/organigramma", icon: Network },
            ],
        },
        {
            name: "Attività",
            submenu: [
                { name: "Corsi", href: "/corsi", icon: GraduationCap },
                { name: "Eventi", href: "/eventi", icon: Calendar1 },
                { name: "Gare", href: "/gare", icon: Trophy },
                { name: "Storie dei soci", href: "/storie", icon: Speech },
            ],
        },
        { name: "News", href: "/news" },
        { name: "Gallery", href: "/gallery" },
        { name: "Contatti", href: "/contatti" },
        { name: "Area Soci", href: "/area-soci" },
    ]

    return (
        <header
            className={`fixed z-50 top-0 w-full transition-all duration-300 ${isScrolled
                ? "backdrop-blur supports-[backdrop-filter]:bg-background/85 border-b border-border/40 shadow-md"
                : "bg-transparent"
                }`}
        >
            <div className="max-w-7xl px-1 pr-4 m-auto">
                <div className="flex h-16 items-center justify-between gap-4">
                    <Link href="/" className="relative flex items-center" aria-label={`${title} — Home`}>
                        <div className="relative w-[160px] h-[64px] py-1">
                            <Image
                                src={isScrolled ? darkLogo.src : lightLogo.src}
                                alt={title || "Logo"}
                                className="top-0 left-0 object-contain object-center"
                                fill
                                priority
                            />
                        </div>
                    </Link>

                    {/* Desktop navigation */}
                    <nav className="hidden lg:flex items-center gap-1 flex-1 justify-center" aria-label="desktop menu">
                        <NavigationMenu>
                            <NavigationMenuList>
                                {nav.map(({ href, icon: Icon, name, submenu }, n) =>
                                    submenu ? (
                                        <NavigationMenuItem key={name}>
                                            <NavigationMenuTrigger className={`${isScrolled ? "text-accent" : "text-white"} text-sm font-medium bg-transparent cursor-pointer transition-all`}>
                                                {name}
                                            </NavigationMenuTrigger>
                                            <NavigationMenuContent className="p-2">
                                                <div className={`max-w-screen w-[600px] grid grid-flow-col gap-1 ${submenu.length > 4 ? "grid-rows-4" : "grid-rows-2"}`}>
                                                    {submenu.map(({ href, name, icon: Icon }) => (
                                                        <NavigationMenuLink asChild className="p-3 text-accent hover:text-secondary" key={name}>
                                                            <Link href={href}
                                                                className="block select-none p-3 leading-none no-underline outline-none transition-all hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground">
                                                                <div className="text-sm font-medium leading-none flex items-center gap-x-2">
                                                                    {Icon ? <Icon className="size-4" /> : <></>}
                                                                    {name}
                                                                </div>
                                                            </Link>
                                                        </NavigationMenuLink>
                                                    ))}
                                                </div>
                                            </NavigationMenuContent>
                                        </NavigationMenuItem>
                                    ) : (
                                        <NavigationMenuItem key={name}>
                                            <Link href={href} legacyBehavior passHref>
                                                <NavigationMenuLink
                                                    className={`${isScrolled ? "text-accent hover:text-white" : "text-white"} group inline-flex h-10 w-max items-center justify-center rounded-md px-4 py-2 text-sm font-medium text-primary hover:text-secondary hover:bg-accent transition-colors`}>
                                                    {Icon ? (
                                                        <>
                                                            <Icon className="h-4 w-4" />
                                                            <span className="sr-only">{name}</span>
                                                        </>
                                                    ) : (
                                                        <span>{name}</span>
                                                    )}
                                                </NavigationMenuLink>
                                            </Link>
                                        </NavigationMenuItem>
                                    ),
                                )}
                            </NavigationMenuList>
                        </NavigationMenu>
                    </nav>

                    <div className="flex items-center justify-center gap-3 shrink-0">
                        {/* Contacts (desktop XL) */}
                        <div className="hidden xl:flex items-center gap-3">
                            {telHref && (
                                <a
                                    href={telHref}
                                    className={
                                        `${isScrolled ? "text-accent" : "text-white hover:text-accent"} flex items-center gap-1 hover:scale-110 transition-all`
                                    }
                                    aria-label={`Chiama ${phone}`}
                                >
                                    <Phone className="h-4 w-4" />
                                </a>
                            )}
                            {mailHref && (
                                <a
                                    href={mailHref}
                                    className={`${isScrolled ? "text-accent" : "text-white hover:text-accent"
                                        } flex items-center gap-1 hover:scale-110 transition-all`}
                                    aria-label={`Scrivi a ${email}`}
                                >
                                    <Mail className="h-4 w-4" />
                                </a>
                            )}
                        </div>

                        {/* Social */}
                        <div className="hidden md:flex items-center gap-2">
                            {facebookUrl && (
                                <a
                                    href={facebookUrl}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className={`${isScrolled ? "text-accent" : "text-white hover:text-accent"
                                        } flex items-center gap-1 hover:scale-110 transition-all`}
                                    aria-label="Apri Facebook"
                                >
                                    <Facebook className="h-4 w-4" />
                                </a>
                            )}
                            {twitterUrl && (
                                <a
                                    href={twitterUrl}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className={`${isScrolled ? "text-accent" : "text-white hover:text-accent"
                                        } flex items-center gap-1 hover:scale-110 transition-all`}
                                    aria-label="Apri Twitter"
                                >
                                    <Twitter className="h-4 w-4" />
                                </a>
                            )}
                        </div>

                        <ThemeToggle className={isScrolled ? "text-accent" : "text-white"} />

                        {/* Mobile menu */}
                        <Sheet open={open} onOpenChange={setOpen}>
                            <SheetTrigger asChild className="lg:hidden">
                                <Button variant="ghost" size="icon" aria-label="Apri menu">
                                    <Menu className={`h-5 w-5 ${isScrolled ? "text-accent" : "text-white"}`} />
                                </Button>
                            </SheetTrigger>
                            <SheetContent side="right" className="w-[300px] sm:w-[400px]">
                                <nav className="flex flex-col gap-4 mt-8" aria-label="Menu mobile">
                                    {nav.map(({ href, name }) => (
                                        <Link
                                            key={name}
                                            href={href ?? "#"}
                                            onClick={() => setOpen(false)}
                                            className="px-4 py-3 text-lg font-medium text-foreground hover:bg-accent rounded-md transition-colors"
                                        >
                                            {name}
                                        </Link>
                                    ))}
                                    <div className="flex flex-col gap-3 mt-4 pt-4 border-t text-sm text-muted-foreground">
                                        {phone && (
                                            <a href={telHref} className="flex items-center gap-2 hover:text-foreground transition-colors">
                                                <Phone className="h-4 w-4" />
                                                <span>{phone}</span>
                                            </a>
                                        )}
                                        {email && (
                                            <a href={mailHref} className="flex items-center gap-2 hover:text-foreground transition-colors">
                                                <Mail className="h-4 w-4" />
                                                <span>{email}</span>
                                            </a>
                                        )}
                                        {(facebookUrl || twitterUrl) && (
                                            <div className="flex items-center gap-3 mt-2">
                                                {facebookUrl && (
                                                    <a
                                                        href={facebookUrl}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="hover:text-foreground transition-colors"
                                                        aria-label="Facebook"
                                                    >
                                                        <Facebook className="h-5 w-5" />
                                                    </a>
                                                )}
                                                {twitterUrl && (
                                                    <a
                                                        href={twitterUrl}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="hover:text-foreground transition-colors"
                                                        aria-label="Twitter / X"
                                                    >
                                                        <Twitter className="h-5 w-5" />
                                                    </a>
                                                )}
                                            </div>
                                        )}
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
