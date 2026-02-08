import { TextToParagraphs } from "@/components/text-to-paragraphs"

interface PageHeroProps {
  title?: string
  description?: string
}

export const PageHero = async ({ title, description }: PageHeroProps) => (
  <section className="p-8 max-sm:px-4 bg-linear-to-br from-primary to-primary/80 text-secondary-foreground">
    <div className="max-w-5xl m-auto">
      <h2 className="font-bold text-balance">{title ?? ""}</h2>
      <div className="text-base leading-relaxed opacity-90">
        <TextToParagraphs text={description ?? ""} />
      </div>
    </div>
  </section>
)
