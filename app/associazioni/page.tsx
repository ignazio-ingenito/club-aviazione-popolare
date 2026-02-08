import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { getPage, getChapters } from "@/lib/server"

import Markdown from "react-markdown"
import {
  Users,
  MapPin,
  Plane,
  GraduationCap,
  ClockFading,
  Globe,
  CalendarClock,
} from "lucide-react"
import { PageHero } from "@/components/page/hero"

export default async function index() {
  const { title, description } = await getPage("associazioni")
  const chapters = await getChapters()

  return (
    <>
      <PageHero title={title} description={description} />
      <div className="px-4 sm:px-8">
        <div className="max-w-5xl m-auto py-8 flex flex-col gap-y-8">
          <section className="grid gap-4 grid-cols-[repeat(auto-fit,minmax(415px,1fr))] justify-center">
            {chapters.map(
              ({
                id,
                slug,
                aircrafts,
                highlights,
                description,
                name,
                founded,
                location,
                members,
                president,
                website,
              }) => (
                <Card
                  key={name}
                  className="border-0 shadow-sm dark:border py-6 px-8"
                >
                  <CardHeader className="p-0 m-0">
                    <CardTitle className="text-2xl pb-3 border-b border-accent/20">
                      <div className="flex flex-col sm:flex-row overflow-hidden h-8">
                        <div>{name}</div>
                        {
                          description && (slug || typeof id !== "undefined") && (
                            <a
                              href={`/associazioni/${slug ?? id}`}
                              className="flex-1 flex gap-x-1 justify-start sm:justify-end items-center pt-2 sm:pt-0"
                            >
                              <CalendarClock className="h-4 w-4 text-primary mt-0.5 shrink-0" />
                              <div className="text-sm font-normal text-accent text-nowrap hover:underline">
                                La nostra storia...
                              </div>
                            </a>
                          )}
                      </div>
                    </CardTitle>
                    <CardDescription className="pt-2 flex [&_a]:text-accent [&_a]:pl-3 [&_p]:line-clamp-4 [&_p]:min-h-16">
                      <Markdown>{highlights}</Markdown>
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="grid grid-cols-2 p-0 pt-4 gap-y-4">
                    <div className="flex flex-col">
                      <div className="flex gap-x-3 items-center">
                        <Globe className="h-5 w-5 text-primary mt-0.5 shrink-0" />
                        <h4 className="font-semibold text-sm">Sito web</h4>
                      </div>
                      <a
                        href={`http://${website}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="pl-8 text-primary text-sm overflow-hidden text-ellipsis hover:underline "
                      >
                        {(website || "")
                          .replaceAll(/https?:\/\//g, "")
                          .replace(/\/.*$/, "")}
                      </a>
                    </div>
                    <div className="grid grid-cols-[auto_1fr] gap-x-2 gap-0.5 items-center">
                      <ClockFading className="h-5 w-5 text-primary mt-0.5 shrink-0" />
                      <h4 className="font-semibold text-sm">Fondato</h4>
                      <p></p>
                      <p className="text-sm text-muted-foreground">{founded}</p>
                    </div>
                    <div className="grid grid-cols-[auto_1fr] gap-x-2 gap-y-0.5 items-center">
                      <MapPin className="h-5 w-5 text-primary mt-0.5 shrink-0" />
                      <h4 className="font-semibold text-sm">Sede</h4>
                      <p></p>
                      <p className="text-sm text-muted-foreground">{location}</p>
                    </div>
                    <div className="grid grid-cols-[auto_1fr] gap-x-2 gap-y-0.5 items-center">
                      <GraduationCap className="h-5 w-5 text-primary mt-0.5 shrink-0" />
                      <h4 className="font-semibold text-sm">Presidente</h4>
                      <p></p>
                      <p className="text-sm text-muted-foreground">{president}</p>
                    </div>
                    <div className="grid grid-cols-[auto_1fr] gap-x-2 gap-y-0.5 items-center">
                      <Users className="h-5 w-5 text-primary mt-0.5 shrink-0" />
                      <h4 className="font-semibold text-sm">Soci</h4>
                      <p></p>
                      <p className="text-sm text-muted-foreground">{members}</p>
                    </div>
                    <div className="grid grid-cols-[auto_1fr] gap-x-2 gap-y-0.5 items-center">
                      <Plane className="h-5 w-5 text-primary mt-0.5 shrink-0" />
                      <h4 className="font-semibold text-sm">Flotta</h4>
                      <p></p>
                      <p className="text-sm text-muted-foreground">{aircrafts}</p>
                    </div>
                  </CardContent>
                </Card>
              )
            )}
          </section>
        </div>
      </div>
    </>
  )
}
