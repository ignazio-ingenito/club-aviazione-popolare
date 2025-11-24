
import { getPage, getMeetings } from "@/lib/server"

import { PageHero } from "@/components/page/hero"
import { PageTitle } from "@/components/page/title"

import MeetingTable from "./table"

export default async function index() {
  const { content_title, description } = await getPage("albo-storico")
  const meetings = await getMeetings()

  return (
    <>
      <PageHero title={content_title} description={description} />

      <div className="p-8 flex flex-col gap-y-8 max-w-7xl m-auto">
        <PageTitle title={content_title} description={description} icon="notebook-text" />
        <MeetingTable meetings={meetings} />
      </div>
    </>
  )
}
