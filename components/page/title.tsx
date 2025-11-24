import { LucideIcon } from "../lucide-icon"


interface PageTitleProps {
    title?: string
    description?: string
    icon?: string
}

export const PageTitle = ({ title, icon }: PageTitleProps) => (
    <div className="flex items-center gap-x-4 my-2">
        <LucideIcon name={icon || "plane"} className="h-12 w-12" />
        <h2 className="text-3xl font-bold">{title}</h2>
    </div>
)
