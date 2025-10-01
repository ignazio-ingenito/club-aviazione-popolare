"use client"

import Link from "next/link"
import Image from "next/image"

import { Button } from "@/components/ui/button"
import { ThemeToggle } from "@/components/theme-toggle"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"

import darkLogo from "@/app/public/logo-dark.svg"
import { Mail, Phone, Facebook, Twitter, Menu, Home } from "lucide-react"
import { useState } from "react"

export type HeaderPageProps = {
    title?: string
    description?: string
    phone?: string
    email?: string
    facebookUrl?: string
    twitterUrl?: string
}

export function HeaderPage({
    title = "",
    phone,
    email,
    facebookUrl,
    twitterUrl,
}: HeaderPageProps) {
    const telHref = phone ? `tel:${phone.replace(/\s+/g, "")}` : undefined
    const mailHref = email ? `mailto:${email}` : undefined
    const [open, setOpen] = useState(false)

    const nav = [
        { name: "Chi Siamo", href: "/chi-siamo" },
        { name: "Eventi", href: "/eventi" },
        { name: "La Flotta", href: "/flotta" },
        { name: "News", href: "/news" },
        { name: "Contatti", href: "/contatti" },
        { name: "Area Soci", href: "/area-soci" },
    ]

    return (
        <header
            className="sticky top-0 z-10 w-full transition-all duration-300 backdrop-blur supports-[backdrop-filter]:bg-background/85 border-b border-border/40 shadow-md"
        >
            <div className="container max-w-7xl px-1 pr-4">
                <div className="flex h-16 items-center justify-between gap-4">
                    <Link href="/" className="relative flex items-center" aria-label={`${title} — Home`}>
                        {/* Logo */}
                        <div className="relative w-[160px] h-[64px] py-1">
                            <Image
                                src={darkLogo.src}
                                alt={title || "Logo"}
                                className="top-0 left-0 object-contain object-center"
                                fill
                                priority
                            />
                        </div>
                    </Link>

                    {/* Desktop navigation */}
                    <nav className="lg:flex items-center gap-1 flex-1 justify-center" aria-label="Principale">
                        <Link
                            href="/"
                            aria-label="Home"
                            className="px-3 py-2 hover:scale-125 transition-all text-primary dark:text-secondary"
                        >
                            <Home className="h-4 w-4" />
                        </Link>
                        {nav.map((item) => (
                            <Link
                                key={item.name}
                                href={item.href}
                                className="px-3 py-2 text-sm font-medium rounded-md transition-all hover:scale-110 text-primary dark:text-secondary"
                            >
                                {item.name}
                            </Link>
                        ))}
                    </nav>

                    <div className="flex items-center justify-center gap-3 shrink-0">
                        {/* Contacts (desktop XL) */}
                        <div className="hidden xl:flex items-center gap-3">
                            {telHref && (
                                <a
                                    href={telHref}
                                    className="text-primary dark:text-secondary flex items-center gap-1 hover:scale-110 transition-all"
                                    aria-label={`Chiama ${phone}`}
                                >
                                    <Phone className="h-4 w-4" />
                                </a>
                            )}
                            {mailHref && (
                                <a
                                    href={mailHref}
                                    className="text-primary dark:text-secondary flex items-center gap-1 hover:scale-110 transition-all"
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
                                    className="text-primary dark:text-secondary flex items-center gap-1 hover:scale-110 transition-all"
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
                                    className="text-primary dark:text-secondary flex items-center gap-1 hover:scale-110 transition-all"
                                    aria-label="Apri Twitter"
                                >
                                    <Twitter className="h-4 w-4" />
                                </a>
                            )}
                        </div>

                        <ThemeToggle className="text-primary dark:text-secondary" />

                        {/* Mobile menu */}
                        <Sheet open={open} onOpenChange={setOpen}>
                            <SheetTrigger asChild className="lg:hidden">
                                <Button variant="ghost" size="icon" aria-label="Apri menu">
                                    <Menu className="h-5 w-5 text-accent" />
                                </Button>
                            </SheetTrigger>
                            <SheetContent side="right" className="w-[300px] sm:w-[400px]">
                                <nav className="flex flex-col gap-4 mt-8" aria-label="Menu mobile">
                                    {nav.map((item) => (
                                        <Link
                                            key={item.name}
                                            href={item.href}
                                            onClick={() => setOpen(false)}
                                            className="px-4 py-3 text-lg font-medium text-foreground hover:bg-accent rounded-md transition-colors"
                                        >
                                            {item.name}
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
        </header >
    )
}
