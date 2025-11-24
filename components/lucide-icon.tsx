import { BookText, Calendar1, Coins, Drill, FileText, GraduationCap, HardHat, LibraryBig, MapPinHouse, Megaphone, MessagesSquare, Network, Newspaper, NotebookText, Plane, PlaneTakeoff, Rss, Share2, ShieldUser, Speech, Target, TrafficCone, TriangleAlert, Trophy, Users, Wrench } from "lucide-react"
import { SVGProps } from "react"
import { Engine } from "./svg/Engine"

export interface DynamicLucideIconProps
    extends Omit<SVGProps<SVGSVGElement>, "ref"> {
    name: string
    className?: string
}

const iconMap: Record<string, React.FC<any>> = {
    "book-text": BookText,
    "calendar-1": Calendar1,
    "coins": Coins,
    "drill": Drill,
    "engine": Engine,
    "file-text": FileText,
    "graduation-cap": GraduationCap,
    "hard-hat": HardHat,
    "library-big": LibraryBig,
    "map-pin-house": MapPinHouse,
    "megaphone": Megaphone,
    "messages-square": MessagesSquare,
    "newspaper": Newspaper,
    "network": Network,
    "notebook-text": NotebookText,
    "plane-takeoff": PlaneTakeoff,
    "plane": Plane,
    "rss": Rss,
    "share-2": Share2,
    "shield-user": ShieldUser,
    "speech": Speech,
    "target": Target,
    "traffic-cone": TrafficCone,
    "trophy": Trophy,
    "triangle-alert": TriangleAlert,
    "users": Users,
    "wrench": Wrench,
}

export function LucideIcon({ name, ...props }: DynamicLucideIconProps) {
    const Icon = iconMap[name]

    return Icon
        ? <Icon {...props} />
        : <TriangleAlert className="bg-red-500" />
}
