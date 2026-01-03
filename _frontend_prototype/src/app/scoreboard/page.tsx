"use client"

import { useEffect, useState } from "react"
import { Trophy, RefreshCw, Loader2, ArrowUp, ArrowDown, Minus, Swords, Shield, Clock } from "lucide-react"

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
import type { ScoreboardResponse, Game } from "@/lib/types"

export default function ScoreboardPage() {
  const [games, setGames] = useState<Game[]>([])
  const [selectedGameId, setSelectedGameId] = useState<string>("")
  const [scoreboard, setScoreboard] = useState<ScoreboardResponse | null>(null)
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

  async function fetchScoreboard() {
    if (!selectedGameId) return

    try {
      setIsRefreshing(true)
      const data = await api.scoreboard.get(selectedGameId)
      setScoreboard(data)
    } catch (error) {
      console.error("Failed to fetch scoreboard:", error)
    } finally {
      setIsRefreshing(false)
    }
  }

  useEffect(() => {
    fetchGames()
  }, [])

  useEffect(() => {
    if (selectedGameId) {
      fetchScoreboard()
    }
  }, [selectedGameId])

  useEffect(() => {
    if (!selectedGameId) return
    const interval = setInterval(fetchScoreboard, 10000)
    return () => clearInterval(interval)
  }, [selectedGameId])

  function getRankChange(rank: number) {
    return null
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
          <h1 className="text-3xl font-bold tracking-tight">Scoreboard</h1>
          <p className="text-muted-foreground">
            Live rankings and team scores
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
            onClick={fetchScoreboard}
            disabled={isRefreshing || !selectedGameId}
          >
            <RefreshCw className={`size-4 ${isRefreshing ? "animate-spin" : ""}`} />
          </Button>
        </div>
      </div>

      {!selectedGameId ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Trophy className="mb-3 size-12 text-muted-foreground" />
            <h3 className="text-lg font-medium">Select a Game</h3>
            <p className="text-sm text-muted-foreground">
              Choose a game to view its scoreboard
            </p>
          </CardContent>
        </Card>
      ) : scoreboard ? (
        <>
          <div className="grid gap-4 md:grid-cols-3">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Game</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-xl font-bold">{scoreboard.game_name}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Current Tick</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2">
                  <Clock className="size-4 text-muted-foreground" />
                  <span className="text-xl font-bold">{scoreboard.current_tick}</span>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Last Updated</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-sm text-muted-foreground">
                  {scoreboard.last_updated
                    ? new Date(scoreboard.last_updated).toLocaleString()
                    : "Never"}
                </div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Rankings</CardTitle>
              <CardDescription>
                {scoreboard.entries.length} team{scoreboard.entries.length !== 1 ? "s" : ""} competing
              </CardDescription>
            </CardHeader>
            <CardContent>
              {scoreboard.entries.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-8 text-center">
                  <Trophy className="mb-2 size-8 text-muted-foreground" />
                  <p className="text-sm text-muted-foreground">No scores yet</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-[60px]">Rank</TableHead>
                      <TableHead>Team</TableHead>
                      <TableHead className="text-right">
                        <span className="flex items-center justify-end gap-1">
                          <Swords className="size-4" />
                          Attack
                        </span>
                      </TableHead>
                      <TableHead className="text-right">
                        <span className="flex items-center justify-end gap-1">
                          <Shield className="size-4" />
                          Defense
                        </span>
                      </TableHead>
                      <TableHead className="text-right">SLA</TableHead>
                      <TableHead className="text-right">Total</TableHead>
                      <TableHead className="text-right">Flags</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {scoreboard.entries.map((entry) => (
                      <TableRow key={entry.team_id}>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <Badge
                              variant={entry.rank === 1 ? "default" : "secondary"}
                              className={
                                entry.rank === 1
                                  ? "bg-amber-500/10 text-amber-500 border-amber-500/20"
                                  : entry.rank === 2
                                  ? "bg-slate-400/10 text-slate-400 border-slate-400/20"
                                  : entry.rank === 3
                                  ? "bg-orange-500/10 text-orange-500 border-orange-500/20"
                                  : ""
                              }
                            >
                              #{entry.rank}
                            </Badge>
                          </div>
                        </TableCell>
                        <TableCell className="font-medium">{entry.team_id}</TableCell>
                        <TableCell className="text-right font-mono text-emerald-500">
                          +{entry.attack_points}
                        </TableCell>
                        <TableCell className="text-right font-mono text-red-500">
                          -{entry.defense_points}
                        </TableCell>
                        <TableCell className="text-right font-mono">
                          {entry.sla_points}
                        </TableCell>
                        <TableCell className="text-right font-bold">
                          {entry.total_points}
                        </TableCell>
                        <TableCell className="text-right text-muted-foreground">
                          <span className="text-emerald-500">↑{entry.flags_captured}</span>
                          {" / "}
                          <span className="text-red-500">↓{entry.flags_lost}</span>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </>
      ) : (
        <Card>
          <CardContent className="flex items-center justify-center py-12">
            <Loader2 className="size-6 animate-spin text-muted-foreground" />
          </CardContent>
        </Card>
      )}
    </div>
  )
}
