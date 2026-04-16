import { FaFacebook, FaInstagram, FaTwitter } from "react-icons/fa"

type SocialsProps = {
    className?: string
    isScrolled: boolean
    facebookUrl?: string
    instagramUrl?: string
    twitterUrl?: string
    textColor?: string
    scrolledTextColor?: string
    scrolledTextColorHover?: string
}

export function HeaderSocials({
    className,
    isScrolled,
    facebookUrl,
    instagramUrl,
    twitterUrl,
    textColor,
    scrolledTextColor,
    scrolledTextColorHover
}: SocialsProps) {
    const css = isScrolled ? `${textColor}` : `${scrolledTextColor} hover:${scrolledTextColorHover}`
    return (
        <div className={`header-socials ${className}`}>
            {instagramUrl && (
                <a
                    href={instagramUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={`${css} flex items-center gap-1 hover:scale-150 transition-all ease-in-out duration-300`}
                    aria-label="Apri Instagram"
                >
                    <FaInstagram className="h-4 w-4" />
                </a>
            )}
            {facebookUrl && (
                <a
                    href={facebookUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={`${css} flex items-center gap-1 hover:scale-150 transition-all ease-in-out duration-300`}
                    aria-label="Apri Facebook"
                >
                    <FaFacebook className="h-4 w-4" />
                </a>
            )}
            {twitterUrl && (
                <a
                    href={twitterUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={`${css} flex items-center gap-1 hover:scale-150 transition-all ease-in-out duration-300`}
                    aria-label="Apri Twitter"
                >
                    <FaTwitter className="h-4 w-4" />
                </a>
            )}
        </div>
    )
}