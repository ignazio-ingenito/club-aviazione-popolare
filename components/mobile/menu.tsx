import { useState } from "react"

import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from "@radix-ui/react-accordion"
import { Sheet, Menu, icons, Link, Phone, Mail, Facebook, Instagram, Twitter } from "lucide-react"
import { HeaderContacts } from "../header/contacts"
import { HeaderSocials } from "../header/socials"
import { ThemeToggle } from "../theme-toggle"
import { Button } from "../ui/button"
import { SheetTrigger, SheetContent } from "../ui/sheet"

type MobileMenuProps = {
    isScrolled: boolean
    phone?: string
    email?: string
    facebookUrl?: string
    instagramUrl?: string
    twitterUrl?: string
}

export function MobileMenu({ isScrolled, phone, email, facebookUrl, instagramUrl, twitterUrl }: MobileMenuProps) {
    const [open, setOpen] = useState(false)
        const [accordionValue, setAccordionValue] = useState<string | undefined>(undefined)
    return (
        <div className="flex items-center justify-center gap-3 shrink-0">
            {/* Contacts (desktop XL) */}
            <HeaderContacts css="hidden xl:flex items-center gap-3" isScrolled={isScrolled} phone={phone} email={email} />

            {/* Social */}
            <HeaderSocials isScrolled={isScrolled} instagramUrl={instagramUrl} />

            <ThemeToggle className={isScrolled ? "text-accent" : "text-white"} />

            {/* Mobile menu */}
            <Sheet open={open} onOpenChange={setOpen}>
                <SheetTrigger asChild className="lg:hidden">
                    <Button variant="ghost" size="icon" aria-label="Apri menu">
                        <Menu className={`h-5 w-5 ${isScrolled ? "text-accent" : "text-white"}`} />
                    </Button>
                </SheetTrigger>
                <SheetContent side="right" className="w-[300px] sm:w-[400px] focus:ring-0 focus:ring-transparent focus:ring-offset-0">
                    <nav className="flex flex-col pt-8 transition-all" aria-label="Menu mobile">
                        <Accordion
                            type="single"
                            collapsible
                            value={accordionValue}
                            onValueChange={(v) => setAccordionValue(v ?? undefined)}
                            className="flex flex-col"
                        >
                            {menu?.map(({ id, url, title, submenu }) => {
                                if (!submenu) return null

                                if (submenu.length > 0) {
                                    return (
                                        <AccordionItem value={`${id}`} key={id}>
                                            <AccordionTrigger>{title}</AccordionTrigger>
                                            {submenu.map(({ id: sid, url: surl, title: stitle }) => {
                                                const Icon = icons[surl || ""]
                                                return (
                                                    <AccordionContent
                                                        key={sid}
                                                        className="flex items-center p-4 gap-x-4 hover:bg-accent hover:text-accent-foreground hover:underline"
                                                    >
                                                        {Icon ? <Icon className="size-5" /> : null}
                                                        <Link className="text-sm transition-all outline-none" href={surl ?? "#"}>
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
                                        <Link className="text-left text-sm font-medium transition-all outline-none hover:underline" href={url ?? "#"}>
                                            {title}
                                        </Link>
                                    </div>
                                )
                            })}
                        </Accordion>
                        <div className="flex flex-col gap-3 pt-10 border-t text-sm text-muted-foreground">
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
                                    {instagramUrl && (
                                        <a
                                            href={instagramUrl}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="hover:text-foreground transition-colors"
                                            aria-label="Instagram"
                                        >
                                            <Instagram className="h-5 w-5" />
                                        </a>
                                    )
                                    }
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
    )
}
