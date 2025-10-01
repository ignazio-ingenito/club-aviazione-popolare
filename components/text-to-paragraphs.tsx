import { Fragment } from "react"

const urlRe = /\bhttps?:\/\/[^\s<]+/gi
const emailRe = /\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/gi

function linkify(line: string): React.ReactNode[] {
    const parts: React.ReactNode[] = []
    let lastIndex = 0

    function pushText(slice: string) {
        if (!slice) return
        parts.push(slice)
    }

    // Unifica url+email in un’unica passata semplice
    const re = new RegExp(`${urlRe.source}|${emailRe.source}`, "gi")
    let m: RegExpExecArray | null
    while ((m = re.exec(line))) {
        const match = m[0]
        pushText(line.slice(lastIndex, m.index))
        const isEmail = emailRe.test(match)
        emailRe.lastIndex = 0 // reset
        parts.push(
            <a
                key={`${m.index}-${match}`}
                href={isEmail ? `mailto:${match}` : match}
                target={isEmail ? undefined : "_blank"}
                rel={isEmail ? undefined : "noopener noreferrer"}
                className="underline underline-offset-4"
            >
                {match}
            </a>
        )
        lastIndex = m.index + match.length
    }
    pushText(line.slice(lastIndex))
    return parts
}

export function TextToParagraphs({ text }: { text: string }) {
    const paragraphs = text
        .trim()
        .split(/\n{2,}/) // paragrafi separati da almeno una riga vuota
        .map((block) => block.split("\n")) // linee dentro al paragrafo

    return (
        <div className="prose">
            {paragraphs.map((lines, i) => (
                <p key={i}>
                    {lines.map((ln, j) => (
                        <Fragment key={j}>
                            {linkify(ln)}
                            {j < lines.length - 1 && <br />}
                        </Fragment>
                    ))}
                </p>
            ))}
        </div>
    )
}
