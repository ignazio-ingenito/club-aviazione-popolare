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
import { PageTitle } from "@/components/page/title"

export default async function index() {
  const { content_title, description } = await getPage("associazioni")
  const chapters = await getChapters()

  return (
    <>
      <PageHero title={content_title} description={description} />

      <div className="py-8 flex flex-col gap-y-8 max-w-5xl m-auto">
        <PageTitle
          title={content_title}
          description={description}
          icon="map-pin-house"
        />

        <section className="grid gap-4 grid-cols-[repeat(auto-fit,minmax(360px,470px))] justify-center">
          {chapters.map(
            ({
              aircrafts,
              description,
              link,
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
                    <div className="flex flex-col sm:flex-row">
                      <div>{name}</div>
                      <a
                        href={link}
                        className="flex-1 flex gap-x-1 justify-start sm:justify-end items-center pt-2 sm:pt-0"
                      >
                        <CalendarClock className="h-4 w-4 text-primary mt-0.5 shrink-0" />
                        <div className="text-sm font-normal text-accent text-nowrap hover:underline">
                          La nostra storia...
                        </div>
                      </a>
                    </div>
                  </CardTitle>
                  <CardDescription className="flex [&_a]:text-accent [&_a]:pl-3">
                    <Markdown>{description}</Markdown>
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
    </>
  )
}
