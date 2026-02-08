
import { getPage, getMeetings } from "@/lib/server"

import { PageHero } from "@/components/page/hero"
import { PageTitle } from "@/components/page/title"

import MeetingTable from "./table"
import { Cover } from "@/components/page/cover"

export default async function index() {
  const res = await getPage("albo-storico")
  console.log(res)
  const { title, description, cover } = res
  const meetings = await getMeetings()

  return (
    <>
      <PageHero title={title} description={description} />

      <div className="px-4 sm:px-8">
        <div className="max-w-5xl m-auto flex flex-col gap-y-8 py-8">
          <div className="w-full flex justify-center">
            <Cover cover={cover} className="h-auto w-auto max-h-120 object-contain" />
          </div>

          <MeetingTable meetings={meetings} />
        </div>
      </div>
    </>
  )
}
