"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { 
  Gamepad2, 
  Shield, 
  Bug, 
  Trophy, 
  Plus,
  PlayCircle,
  Upload,
  Activity,
} from "lucide-react"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { api } from "@/lib/api/client"
import type { Game, Vulnbox, Checker, GameStatus } from "@/lib/types"

interface DashboardStats {
  totalGames: number
  runningGames: number
  totalVulnboxes: number
  totalCheckers: number
  games: Game[]
}

function getStatusVariant(status: GameStatus): "default" | "secondary" | "destructive" | "outline" {
  switch (status) {
    case "running":
      return "default"
    case "paused":
      return "secondary"
    case "finished":
      return "outline"
    case "deploying":
      return "secondary"
    default:
      return "outline"
  }
}

function getStatusColor(status: GameStatus): string {
  switch (status) {
    case "running":
      return "bg-emerald-500/10 text-emerald-500 border-emerald-500/20"
    case "paused":
      return "bg-amber-500/10 text-amber-500 border-amber-500/20"
    case "finished":
      return "bg-slate-500/10 text-slate-400 border-slate-500/20"
    case "deploying":
      return "bg-blue-500/10 text-blue-500 border-blue-500/20"
    default:
      return "bg-slate-500/10 text-slate-400 border-slate-500/20"
  }
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    async function fetchStats() {
      try {
        const [gamesResponse, vulnboxesResponse, checkersResponse] = await Promise.all([
          api.games.list(),
          api.vulnboxes.list(),
          api.checkers.list(),
        ])

        setStats({
          totalGames: gamesResponse.total,
          runningGames: gamesResponse.games.filter((g) => g.status === "running").length,
          totalVulnboxes: vulnboxesResponse.total,
          totalCheckers: checkersResponse.total,
          games: gamesResponse.games.slice(0, 5),
        })
      } catch (error) {
        console.error("Failed to fetch stats:", error)
      } finally {
        setIsLoading(false)
      }
    }

    fetchStats()
  }, [])

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            Welcome to the Attack-Defense CTF Platform
          </p>
        </div>
        <div className="flex gap-2">
          <Button asChild>
            <Link href="/games">
              <Plus className="mr-2 size-4" />
              New Game
            </Link>
          </Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Games</CardTitle>
            <Gamepad2 className="size-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {isLoading ? "-" : stats?.totalGames ?? 0}
            </div>
            <p className="text-xs text-muted-foreground">
              {stats?.runningGames ?? 0} currently running
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Vulnboxes</CardTitle>
            <Shield className="size-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {isLoading ? "-" : stats?.totalVulnboxes ?? 0}
            </div>
            <p className="text-xs text-muted-foreground">
              Docker images available
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Checkers</CardTitle>
            <Bug className="size-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {isLoading ? "-" : stats?.totalCheckers ?? 0}
            </div>
            <p className="text-xs text-muted-foreground">
              SLA check scripts
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Games</CardTitle>
            <Activity className="size-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {isLoading ? "-" : stats?.runningGames ?? 0}
            </div>
            <p className="text-xs text-muted-foreground">
              Games in progress
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Recent Games</CardTitle>
            <CardDescription>Latest games in the system</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-2">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-12 animate-pulse rounded bg-muted" />
                ))}
              </div>
            ) : stats?.games.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-8 text-center">
                <Gamepad2 className="mb-2 size-8 text-muted-foreground" />
                <p className="text-sm text-muted-foreground">No games yet</p>
                <Button asChild variant="link" size="sm">
                  <Link href="/games">Create your first game</Link>
                </Button>
              </div>
            ) : (
              <div className="space-y-3">
                {stats?.games.map((game) => (
                  <Link
                    key={game.id}
                    href={`/games/${game.id}`}
                    className="flex items-center justify-between rounded-lg border p-3 transition-colors hover:bg-muted/50"
                  >
                    <div>
                      <p className="font-medium">{game.name}</p>
                      <p className="text-xs text-muted-foreground">
                        Tick {game.current_tick} • {game.tick_duration_seconds}s intervals
                      </p>
                    </div>
                    <Badge className={getStatusColor(game.status)}>
                      {game.status}
                    </Badge>
                  </Link>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>Common operations</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3">
            <Button variant="outline" className="justify-start" asChild>
              <Link href="/games">
                <PlayCircle className="mr-2 size-4" />
                Create New Game
              </Link>
            </Button>
            <Button variant="outline" className="justify-start" asChild>
              <Link href="/vulnboxes">
                <Upload className="mr-2 size-4" />
                Upload Vulnbox
              </Link>
            </Button>
            <Button variant="outline" className="justify-start" asChild>
              <Link href="/checkers">
                <Bug className="mr-2 size-4" />
                Upload Checker
              </Link>
            </Button>
            <Button variant="outline" className="justify-start" asChild>
              <Link href="/scoreboard">
                <Trophy className="mr-2 size-4" />
                View Scoreboard
              </Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
