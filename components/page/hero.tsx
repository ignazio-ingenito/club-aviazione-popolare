import { TextToParagraphs } from "@/components/text-to-paragraphs"

interface PageHeroProps {
    title?: string
    description?: string
}

export const PageHero = async ({ title, description }: PageHeroProps) => (
    <section className="px-8 pt-20 pb-8 bg-linear-to-br from-primary to-primary/80 text-secondary-foreground">
        <div className="max-w-7xl m-auto">
            <h1 className="text-4xl md:text-5xl font-bold pb-6 text-balance">
                {title ?? ""}
            </h1>
            <div className="text-lg leading-relaxed opacity-90">
                <TextToParagraphs text={description ?? ""} />
            </div>
        </div>
    </section>
)