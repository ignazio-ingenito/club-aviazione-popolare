import { Facebook, Instagram, Twitter, Menu } from "lucide-react"

type SocialsProps = {
    css?: string
    isScrolled: boolean
    facebookUrl?: string
    instagramUrl?: string
    twitterUrl?: string
}

export function HeaderSocials({ css, isScrolled, facebookUrl, instagramUrl, twitterUrl }: SocialsProps) {
    return (
        <div className={`${css}`}>
            {instagramUrl && (
                <a
                    href={instagramUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={`${isScrolled ? "text-accent" : "text-white hover:text-accent"
                        } flex items-center gap-1 hover:scale-110 transition-all`}
                    aria-label="Apri Twitter"
                >
                    <Instagram className="h-4 w-4" />
                </a>
            )}
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
    )
}