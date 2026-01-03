"use client"

import { useEffect, useState } from "react"
import { Flag, Loader2, RefreshCw, Search, Filter } from "lucide-react"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
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
import type { Flag as FlagType, FlagStats, Game } from "@/lib/types"

export default function FlagsPage() {
  const [games, setGames] = useState<Game[]>([])
  const [selectedGameId, setSelectedGameId] = useState<string>("")
  const [flags, setFlags] = useState<FlagType[]>([])
  const [stats, setStats] = useState<FlagStats | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [filterStolen, setFilterStolen] = useState<string>("all")

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

  async function fetchFlags() {
    if (!selectedGameId) return

    try {
      setIsRefreshing(true)
      const [flagsData, statsData] = await Promise.all([
        api.flags.list(selectedGameId, {
          limit: 50,
          is_stolen: filterStolen === "all" ? undefined : filterStolen === "stolen",
        }),
        api.flags.getStats(selectedGameId),
      ])
      setFlags(flagsData.items)
      setStats(statsData)
    } catch (error) {
      console.error("Failed to fetch flags:", error)
    } finally {
      setIsRefreshing(false)
    }
  }

  useEffect(() => {
    fetchGames()
  }, [])

  useEffect(() => {
    if (selectedGameId) {
      fetchFlags()
    }
  }, [selectedGameId, filterStolen])

  function formatDate(dateString: string) {
    return new Date(dateString).toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    })
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
          <h1 className="text-3xl font-bold tracking-tight">Flags</h1>
          <p className="text-muted-foreground">
            Monitor generated flags across games
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
            onClick={fetchFlags}
            disabled={isRefreshing || !selectedGameId}
          >
            <RefreshCw className={`size-4 ${isRefreshing ? "animate-spin" : ""}`} />
          </Button>
        </div>
      </div>

      {selectedGameId && stats && (
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Total Flags</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_flags}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Stolen Flags</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-500">{stats.stolen_flags}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Safe Flags</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-emerald-500">{stats.not_stolen_flags}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Total Steals</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_steals}</div>
            </CardContent>
          </Card>
        </div>
      )}

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Flag History</CardTitle>
              <CardDescription>
                {flags.length} flags shown
              </CardDescription>
            </div>
            <Select value={filterStolen} onValueChange={setFilterStolen}>
              <SelectTrigger className="w-[150px]">
                <Filter className="mr-2 size-4" />
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Flags</SelectItem>
                <SelectItem value="stolen">Stolen</SelectItem>
                <SelectItem value="safe">Safe</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent>
          {!selectedGameId ? (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <Flag className="mb-2 size-8 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">Select a game to view flags</p>
            </div>
          ) : flags.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <Flag className="mb-2 size-8 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">No flags found</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Team</TableHead>
                  <TableHead>Flag</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Stolen Count</TableHead>
                  <TableHead>Created</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {flags.map((flag) => (
                  <TableRow key={flag.id}>
                    <TableCell className="font-medium">{flag.team_id}</TableCell>
                    <TableCell className="font-mono text-xs max-w-[200px] truncate">
                      {flag.flag_value}
                    </TableCell>
                    <TableCell>
                      <Badge variant={flag.flag_type === "root" ? "destructive" : "secondary"}>
                        {flag.flag_type}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={flag.is_stolen ? "destructive" : "outline"}
                        className={
                          flag.is_stolen
                            ? "bg-red-500/10 text-red-500 border-red-500/20"
                            : "bg-emerald-500/10 text-emerald-500 border-emerald-500/20"
                        }
                      >
                        {flag.is_stolen ? "Stolen" : "Safe"}
                      </Badge>
                    </TableCell>
                    <TableCell className="font-mono">{flag.stolen_count}</TableCell>
                    <TableCell className="text-muted-foreground">
                      {formatDate(flag.created_at)}
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
