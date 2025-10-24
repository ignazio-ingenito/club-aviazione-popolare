import Link from "next/link"
import { getMetadata } from "@/lib/utils-server"

import { Mail, Phone, MapPin, Facebook, Twitter, Instagram } from "lucide-react"

export const SiteFooter = async () => {
  const { title, description, phone, email, address, facebook, twitter, instagram } = await getMetadata()
  const telHref = phone ? `tel:${phone.replace(/\s+/g, "")}` : undefined
  const mailHref = email ? `mailto:${email}` : undefined

  return (
    <footer className="border-t bg-muted/50">
      <div className="py-8">
        <div className="grid grid-cols-1 md:flex gap-y-8 max-w-7xl m-auto px-4">
          {/* About */}
          <div className="basis-1/3 px-1">
            <h3 className="font-bold text-lg mb-4">{title}</h3>
            <p className="text-sm text-muted-foreground leading-relaxed">
              {description ?? ""}
            </p>
          </div>

          {/* Contact */}
          <div className="basis-1/3 px-1">
            <h3 className="font-bold text-lg mb-4">Contatti</h3>
            <div className="space-y-3 text-sm">
              <a
                href={telHref}
                className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors"
              >
                <Phone className="h-4 w-4" />
                <span>{phone}</span>
              </a>
              <a
                href={mailHref}
                className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors"
              >
                <Mail className="h-4 w-4" />
                <span className="overflow-hidden overflow-ellipsis">{email}</span>
              </a>
              <div className="flex items-start gap-2 text-muted-foreground">
                <MapPin className="h-4 w-4 mt-0.5" />
                <span>{address}</span>
              </div>
            </div>
          </div>

          {/* Links */}
          <div className="basis-1/3 px-1">
            <h3 className="font-bold text-lg mb-4">Link Utili</h3>
            <div className="space-y-2 text-sm">
              <Link href="/chi-siamo" className="block text-muted-foreground hover:text-foreground transition-colors">
                Chi Siamo
              </Link>
              <Link href="/eventi" className="block text-muted-foreground hover:text-foreground transition-colors">
                Eventi
              </Link>
              <Link href="/contatti" className="block text-muted-foreground hover:text-foreground transition-colors">
                Contatti
              </Link>
              <Link href="/area-soci" className="block text-muted-foreground hover:text-foreground transition-colors">
                Area Soci
              </Link>
            </div>
            <div className="flex items-center gap-3 mt-4">
              <a
                href={facebook || "https://facebook.com"}
                target="_blank"
                rel="noopener noreferrer"
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                <Facebook className="h-5 w-5" />
                <span className="sr-only">Facebook</span>
              </a>
              <a
                href={instagram || "https://www.instagram.com"}
                target="_blank"
                rel="noopener noreferrer"
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                <Instagram className="h-5 w-5" />
                <span className="sr-only">Instagram</span>
              </a>
              <a
                href={twitter || "https://twitter.com"}
                target="_blank"
                rel="noopener noreferrer"
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                <Twitter className="h-5 w-5" />
                <span className="sr-only">Twitter</span>
              </a>
            </div>
          </div>
        </div>

        <div className="mt-8 pt-8 border-t text-center text-sm text-muted-foreground">
          <p>© {new Date().getFullYear()} {title}. Tutti i diritti riservati.</p>
        </div>
      </div>
    </footer>
  )
}
