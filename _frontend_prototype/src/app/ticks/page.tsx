"use client"

import { useEffect, useState } from "react"
import { Clock, Loader2, RefreshCw, CheckCircle, XCircle, PlayCircle, MinusCircle } from "lucide-react"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { api } from "@/lib/api/client"
import type { Tick, Game, TickStatus } from "@/lib/types"

function getStatusIcon(status: TickStatus) {
  switch (status) {
    case "completed":
      return <CheckCircle className="size-4 text-emerald-500" />
    case "active":
      return <PlayCircle className="size-4 text-blue-500" />
    case "pending":
      return <MinusCircle className="size-4 text-amber-500" />
    case "error":
      return <XCircle className="size-4 text-red-500" />
    default:
      return <MinusCircle className="size-4 text-muted-foreground" />
  }
}

function getStatusColor(status: TickStatus): string {
  switch (status) {
    case "completed":
      return "bg-emerald-500/10 text-emerald-500 border-emerald-500/20"
    case "active":
      return "bg-blue-500/10 text-blue-500 border-blue-500/20"
    case "pending":
      return "bg-amber-500/10 text-amber-500 border-amber-500/20"
    case "error":
      return "bg-red-500/10 text-red-500 border-red-500/20"
    default:
      return ""
  }
}

export default function TicksPage() {
  const [games, setGames] = useState<Game[]>([])
  const [selectedGameId, setSelectedGameId] = useState<string>("")
  const [ticks, setTicks] = useState<Tick[]>([])
  const [currentTick, setCurrentTick] = useState<Tick | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)

  async function fetchGames() {
    try {
      const response = await api.games.list()
      setGames(response.games)
      if (response.games.length > 0 && !selectedGameId) {
        const runningGame = response.games.find((g) => g.status === "running")
        setSelectedGameId(runningGame?.id ?? response.games[0].id)
      }
    } catch (error) {
      console.error("Failed to fetch games:", error)
    } finally {
      setIsLoading(false)
    }
  }

  async function fetchTicks() {
    if (!selectedGameId) return

    try {
      setIsRefreshing(true)
      const [ticksData, currentData] = await Promise.all([
        api.ticks.list(selectedGameId, { limit: 50 }),
        api.ticks.getCurrent(selectedGameId),
      ])
      setTicks(ticksData.items)
      setCurrentTick(currentData)
    } catch (error) {
      console.error("Failed to fetch ticks:", error)
    } finally {
      setIsRefreshing(false)
    }
  }

  useEffect(() => {
    fetchGames()
  }, [])

  useEffect(() => {
    if (selectedGameId) {
      fetchTicks()
    }
  }, [selectedGameId])

  useEffect(() => {
    if (!selectedGameId) return
    const interval = setInterval(fetchTicks, 5000)
    return () => clearInterval(interval)
  }, [selectedGameId])

  function formatDate(dateString: string | null) {
    if (!dateString) return "-"
    return new Date(dateString).toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    })
  }

  function calculateDuration(start: string | null, end: string | null): string {
    if (!start) return "-"
    const startTime = new Date(start).getTime()
    const endTime = end ? new Date(end).getTime() : Date.now()
    const durationMs = endTime - startTime
    return `${(durationMs / 1000).toFixed(1)}s`
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="size-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Ticks</h1>
          <p className="text-muted-foreground">
            Monitor game tick progression
          </p>
        </div>
        <div className="flex items-center gap-4">
          <Select value={selectedGameId} onValueChange={setSelectedGameId}>
            <SelectTrigger className="w-[200px]">
              <SelectValue placeholder="Select a game" />
            </SelectTrigger>
            <SelectContent>
              {games.map((game) => (
                <SelectItem key={game.id} value={game.id}>
                  {game.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button
            variant="outline"
            size="icon"
            onClick={fetchTicks}
            disabled={isRefreshing || !selectedGameId}
          >
            <RefreshCw className={`size-4 ${isRefreshing ? "animate-spin" : ""}`} />
          </Button>
        </div>
      </div>

      {currentTick && (
        <Card className="border-blue-500/50 bg-blue-500/5">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-blue-500">
              <PlayCircle className="size-5" />
              Current Tick
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-4">
              <div>
                <p className="text-sm text-muted-foreground">Tick Number</p>
                <p className="text-2xl font-bold">{currentTick.tick_number}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Status</p>
                <Badge className={getStatusColor(currentTick.status)}>
                  {currentTick.status}
                </Badge>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Flags Placed</p>
                <p className="text-xl font-mono">{currentTick.flags_placed}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Started At</p>
                <p className="text-sm">{formatDate(currentTick.started_at)}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Tick History</CardTitle>
          <CardDescription>
            {ticks.length} ticks recorded
          </CardDescription>
        </CardHeader>
        <CardContent>
          {!selectedGameId ? (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <Clock className="mb-2 size-8 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">Select a game to view ticks</p>
            </div>
          ) : ticks.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <Clock className="mb-2 size-8 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">No ticks yet</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[80px]">Tick #</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Flags Placed</TableHead>
                  <TableHead>Started</TableHead>
                  <TableHead>Completed</TableHead>
                  <TableHead>Duration</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {ticks.map((tick) => (
                  <TableRow key={tick.id}>
                    <TableCell className="font-mono font-bold">{tick.tick_number}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {getStatusIcon(tick.status)}
                        <Badge className={getStatusColor(tick.status)}>
                          {tick.status}
                        </Badge>
                      </div>
                    </TableCell>
                    <TableCell className="font-mono">{tick.flags_placed}</TableCell>
                    <TableCell className="text-muted-foreground text-sm">
                      {formatDate(tick.started_at)}
                    </TableCell>
                    <TableCell className="text-muted-foreground text-sm">
                      {formatDate(tick.completed_at)}
                    </TableCell>
                    <TableCell className="font-mono text-muted-foreground">
                      {calculateDuration(tick.started_at, tick.completed_at)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
