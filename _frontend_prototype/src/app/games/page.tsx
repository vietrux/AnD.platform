"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { Gamepad2, Plus, MoreHorizontal, Trash2, Play, Pause, Square, Loader2, RefreshCw } from "lucide-react"
import { toast } from "sonner"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
  DialogClose,
} from "@/components/ui/dialog"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { Badge } from "@/components/ui/badge"
import { api } from "@/lib/api/client"
import type { Game, GameStatus } from "@/lib/types"

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

export default function GamesPage() {
  const [games, setGames] = useState<Game[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isCreating, setIsCreating] = useState(false)
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [deleteId, setDeleteId] = useState<string | null>(null)
  const [actionLoading, setActionLoading] = useState<string | null>(null)
  
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [tickDuration, setTickDuration] = useState(60)

  async function fetchGames() {
    try {
      setIsLoading(true)
      const response = await api.games.list()
      setGames(response.games)
    } catch (error) {
      toast.error("Failed to fetch games")
      console.error(error)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchGames()
  }, [])

  async function handleCreate() {
    if (!name.trim()) {
      toast.error("Please provide a game name")
      return
    }

    try {
      setIsCreating(true)
      await api.games.create({
        name,
        description: description || undefined,
        tick_duration_seconds: tickDuration,
      })
      toast.success("Game created successfully")
      setIsDialogOpen(false)
      resetForm()
      fetchGames()
    } catch (error) {
      toast.error("Failed to create game")
      console.error(error)
    } finally {
      setIsCreating(false)
    }
  }

  async function handleStart(gameId: string) {
    try {
      setActionLoading(gameId)
      await api.games.start(gameId)
      toast.success("Game started")
      fetchGames()
    } catch (error) {
      toast.error("Failed to start game")
      console.error(error)
    } finally {
      setActionLoading(null)
    }
  }

  async function handlePause(gameId: string) {
    try {
      setActionLoading(gameId)
      await api.games.pause(gameId)
      toast.success("Game paused")
      fetchGames()
    } catch (error) {
      toast.error("Failed to pause game")
      console.error(error)
    } finally {
      setActionLoading(null)
    }
  }

  async function handleStop(gameId: string) {
    try {
      setActionLoading(gameId)
      await api.games.stop(gameId)
      toast.success("Game stopped")
      fetchGames()
    } catch (error) {
      toast.error("Failed to stop game")
      console.error(error)
    } finally {
      setActionLoading(null)
    }
  }

  async function handleDelete() {
    if (!deleteId) return

    try {
      await api.games.delete(deleteId)
      toast.success("Game deleted successfully")
      setDeleteId(null)
      fetchGames()
    } catch (error) {
      toast.error("Failed to delete game")
      console.error(error)
    }
  }

  function resetForm() {
    setName("")
    setDescription("")
    setTickDuration(60)
  }

  function formatDate(dateString: string) {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    })
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Games</h1>
          <p className="text-muted-foreground">
            Manage CTF Attack-Defense competitions
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="icon" onClick={fetchGames} disabled={isLoading}>
            <RefreshCw className={`size-4 ${isLoading ? "animate-spin" : ""}`} />
          </Button>
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-2 size-4" />
                New Game
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create New Game</DialogTitle>
                <DialogDescription>
                  Set up a new Attack-Defense CTF competition
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Game Name</Label>
                  <Input
                    id="name"
                    placeholder="CTF 2026"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="description">Description (optional)</Label>
                  <Textarea
                    id="description"
                    placeholder="A brief description of this game..."
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="tick">Tick Duration (seconds)</Label>
                  <Input
                    id="tick"
                    type="number"
                    min={10}
                    max={600}
                    value={tickDuration}
                    onChange={(e) => setTickDuration(parseInt(e.target.value) || 60)}
                  />
                  <p className="text-xs text-muted-foreground">
                    Time between flag generation cycles (10-600 seconds)
                  </p>
                </div>
              </div>
              <DialogFooter>
                <DialogClose asChild>
                  <Button variant="outline">Cancel</Button>
                </DialogClose>
                <Button onClick={handleCreate} disabled={isCreating}>
                  {isCreating && <Loader2 className="mr-2 size-4 animate-spin" />}
                  Create Game
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>All Games</CardTitle>
          <CardDescription>
            {games.length} game{games.length !== 1 ? "s" : ""} total
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="size-6 animate-spin text-muted-foreground" />
            </div>
          ) : games.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Gamepad2 className="mb-3 size-12 text-muted-foreground" />
              <h3 className="text-lg font-medium">No games yet</h3>
              <p className="text-sm text-muted-foreground">
                Create your first game to get started
              </p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Current Tick</TableHead>
                  <TableHead>Tick Duration</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className="w-[50px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {games.map((game) => (
                  <TableRow key={game.id}>
                    <TableCell>
                      <Link 
                        href={`/games/${game.id}`}
                        className="font-medium hover:underline"
                      >
                        {game.name}
                      </Link>
                      {game.description && (
                        <p className="text-xs text-muted-foreground truncate max-w-[200px]">
                          {game.description}
                        </p>
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge className={getStatusColor(game.status)}>
                        {game.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="font-mono">
                      {game.current_tick}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {game.tick_duration_seconds}s
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {formatDate(game.created_at)}
                    </TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon" disabled={actionLoading === game.id}>
                            {actionLoading === game.id ? (
                              <Loader2 className="size-4 animate-spin" />
                            ) : (
                              <MoreHorizontal className="size-4" />
                            )}
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem asChild>
                            <Link href={`/games/${game.id}`}>
                              View Details
                            </Link>
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          {game.status === "draft" && (
                            <DropdownMenuItem onClick={() => handleStart(game.id)}>
                              <Play className="mr-2 size-4" />
                              Start Game
                            </DropdownMenuItem>
                          )}
                          {game.status === "running" && (
                            <DropdownMenuItem onClick={() => handlePause(game.id)}>
                              <Pause className="mr-2 size-4" />
                              Pause Game
                            </DropdownMenuItem>
                          )}
                          {game.status === "paused" && (
                            <DropdownMenuItem onClick={() => handleStart(game.id)}>
                              <Play className="mr-2 size-4" />
                              Resume Game
                            </DropdownMenuItem>
                          )}
                          {(game.status === "running" || game.status === "paused") && (
                            <DropdownMenuItem onClick={() => handleStop(game.id)}>
                              <Square className="mr-2 size-4" />
                              Stop Game
                            </DropdownMenuItem>
                          )}
                          <DropdownMenuSeparator />
                          <DropdownMenuItem
                            className="text-destructive"
                            onClick={() => setDeleteId(game.id)}
                          >
                            <Trash2 className="mr-2 size-4" />
                            Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <AlertDialog open={!!deleteId} onOpenChange={(open) => !open && setDeleteId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Game</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this game? This will also delete all associated teams, flags, and submissions. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
