'use client'

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { ColumnDef, flexRender, getCoreRowModel, getFilteredRowModel, getSortedRowModel, SortingState, useReactTable } from "@tanstack/react-table"

import { Meeting } from "@/lib/types"
import { ArrowDown, ArrowUp, ArrowUpDown, MessageCircleWarning, SearchIcon, X } from "lucide-react"
import { useState } from "react"
import { Button } from "@/components/ui/button"
import { InputGroup, InputGroupInput, InputGroupAddon } from "@/components/ui/input-group"


function SortIcon({ sorted }: { sorted: "asc" | "desc" | false }) {
    if (sorted === "asc") return <ArrowUp className="size-4!" />
    if (sorted === "desc") return <ArrowDown className="size-4!" />
    return <ArrowUpDown className="size-4!" />
}

const columns: ColumnDef<Meeting>[] = [
    {
        accessorKey: "year",
        header: ({ column }) =>
            <Button className="w-full flex justify-start" variant="ghost" onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}>
                <SortIcon sorted={column.getIsSorted()} />
                Anno
            </Button>
    },
    {
        accessorKey: "place",
        header: ({ column }) =>
            <Button className="w-full flex justify-start" variant="ghost" onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}>
                <SortIcon sorted={column.getIsSorted()} />
                Luogo
            </Button>
    },
    {
        accessorKey: "date",
        header: ({ column }) =>
            <Button className="w-full flex justify-start" variant="ghost" onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}>
                <SortIcon sorted={column.getIsSorted()} />
                Data
            </Button>
    },
]

type MeetingTableProps = {
    meetings: Meeting[]
}

export default function MeetingTable({ meetings: data }: MeetingTableProps) {
    const [sorting, setSorting] = useState<SortingState>([])
    const [globalFilter, setGlobalFilter] = useState("")
    const table = useReactTable({
        data,
        columns,
        getCoreRowModel: getCoreRowModel(),
        onSortingChange: setSorting,
        getSortedRowModel: getSortedRowModel(),
        onGlobalFilterChange: setGlobalFilter,
        getFilteredRowModel: getFilteredRowModel(),
        state: { sorting, globalFilter }
    })

    return (
        <div className="flex flex-col gap-y-1">
            <div className="flex justify-end">
                <InputGroup className="max-w-xs">
                    <InputGroupInput placeholder="Cerca..."
                        value={table.getState().globalFilter ?? ""}
                        onChange={(e) => table.setGlobalFilter(e.target.value)}
                    />
                    <InputGroupAddon>
                        <SearchIcon />
                    </InputGroupAddon>
                    <InputGroupAddon align="inline-end" className="transition-all">
                        {table.getState().globalFilter &&
                            <X
                                onClick={e => table.setGlobalFilter("")}
                                className="rounded-full cursor-pointer size-6 p-1 hover:text-accent-foreground hover:bg-accent" />
                        }
                    </InputGroupAddon>
                </InputGroup>
            </div>
            <Table className="border rounded-md overflow-hidden">
                <TableHeader>
                    {table.getHeaderGroups().map((headerGroup) => (
                        <TableRow key={headerGroup.id}>
                            {
                                headerGroup.headers.map((header) =>
                                    <TableHead key={header.id}>
                                        {
                                            header.isPlaceholder
                                                ? <></>
                                                : flexRender(
                                                    header.column.columnDef.header,
                                                    header.getContext()
                                                )
                                        }
                                    </TableHead>
                                )
                            }
                        </TableRow>
                    ))}
                </TableHeader>
                <TableBody>
                    {
                        table.getRowModel().rows?.length
                            ? (table.getRowModel().rows.map(row => (
                                <TableRow key={row.id}
                                    data-state={row.getIsSelected() && "selected"}>
                                    {
                                        row.getVisibleCells().map(cell => (
                                            <TableCell key={cell.id} className="pl-7!">
                                                {flexRender(cell.column.columnDef.cell, cell.getContext())}
                                            </TableCell>
                                        ))
                                    }
                                </TableRow>
                            )))
                            : (
                                <TableRow>
                                    <TableCell colSpan={columns.length} className="h-24 text-center">
                                        <div className="flex items-center justify-center gap-2 text-muted-foreground">
                                            <MessageCircleWarning className="size-5 text-muted-foreground" />
                                            <span>Ops, non ci sono dati...</span>
                                        </div>
                                    </TableCell>
                                </TableRow>)
                    }
                </TableBody>
            </Table >
        </div >
    )

}