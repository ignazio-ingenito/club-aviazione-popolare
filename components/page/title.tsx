import { LucideIcon } from "../lucide-icon"


interface PageTitleProps {
    title?: string
    description?: string
    icon?: string
}

export const PageTitle = ({ title, icon }: PageTitleProps) => (
    <div className="flex items-center gap-x-4 mt-8">
        <LucideIcon className="size-12" name={icon || "plane"} />
        <h3 className="p-0 m-0">{title}</h3>
    </div>
)
