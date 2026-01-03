"use client"

import { useEffect, useState } from "react"
import { Send, Loader2, RefreshCw, CheckCircle, XCircle, AlertCircle, Clock } from "lucide-react"
import { toast } from "sonner"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
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
import { api } from "@/lib/api/client"
import type { SubmissionDetail, Game, SubmissionStatus } from "@/lib/types"

function getStatusIcon(status: SubmissionStatus) {
  switch (status) {
    case "accepted":
      return <CheckCircle className="size-4 text-emerald-500" />
    case "rejected":
    case "invalid":
      return <XCircle className="size-4 text-red-500" />
    case "duplicate":
    case "own_flag":
      return <AlertCircle className="size-4 text-amber-500" />
    case "expired":
      return <Clock className="size-4 text-slate-500" />
    default:
      return null
  }
}

function getStatusColor(status: SubmissionStatus): string {
  switch (status) {
    case "accepted":
      return "bg-emerald-500/10 text-emerald-500 border-emerald-500/20"
    case "rejected":
    case "invalid":
      return "bg-red-500/10 text-red-500 border-red-500/20"
    case "duplicate":
    case "own_flag":
      return "bg-amber-500/10 text-amber-500 border-amber-500/20"
    case "expired":
      return "bg-slate-500/10 text-slate-400 border-slate-500/20"
    default:
      return ""
  }
}

export default function SubmissionsPage() {
  const [games, setGames] = useState<Game[]>([])
  const [selectedGameId, setSelectedGameId] = useState<string>("")
  const [submissions, setSubmissions] = useState<SubmissionDetail[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [filterStatus, setFilterStatus] = useState<string>("all")
  
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [submitGameId, setSubmitGameId] = useState("")
  const [submitTeamId, setSubmitTeamId] = useState("")
  const [submitFlag, setSubmitFlag] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)

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

  async function fetchSubmissions() {
    try {
      setIsRefreshing(true)
      const response = await api.submissions.list({
        game_id: selectedGameId || undefined,
        status: filterStatus === "all" ? undefined : (filterStatus as SubmissionStatus),
        limit: 50,
      })
      setSubmissions(response.items)
    } catch (error) {
      console.error("Failed to fetch submissions:", error)
    } finally {
      setIsRefreshing(false)
    }
  }

  useEffect(() => {
    fetchGames()
  }, [])

  useEffect(() => {
    fetchSubmissions()
  }, [selectedGameId, filterStatus])

  async function handleSubmitFlag() {
    if (!submitGameId || !submitTeamId.trim() || !submitFlag.trim()) {
      toast.error("Please fill in all fields")
      return
    }

    try {
      setIsSubmitting(true)
      const result = await api.submissions.submit({
        game_id: submitGameId,
        team_id: submitTeamId,
        flag: submitFlag,
      })
      
      if (result.status === "accepted") {
        toast.success(`Flag accepted! +${result.points} points`, {
          description: result.message,
        })
      } else {
        toast.error(`Flag ${result.status}`, {
          description: result.message,
        })
      }
      
      setIsDialogOpen(false)
      setSubmitFlag("")
      fetchSubmissions()
    } catch (error) {
      toast.error("Failed to submit flag")
      console.error(error)
    } finally {
      setIsSubmitting(false)
    }
  }

  function formatDate(dateString: string) {
    return new Date(dateString).toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
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
          <h1 className="text-3xl font-bold tracking-tight">Submissions</h1>
          <p className="text-muted-foreground">
            Flag submission history and testing
          </p>
        </div>
        <div className="flex items-center gap-4">
          <Select value={selectedGameId} onValueChange={setSelectedGameId}>
            <SelectTrigger className="w-[200px]">
              <SelectValue placeholder="All games" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">All games</SelectItem>
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
            onClick={fetchSubmissions}
            disabled={isRefreshing}
          >
            <RefreshCw className={`size-4 ${isRefreshing ? "animate-spin" : ""}`} />
          </Button>
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Send className="mr-2 size-4" />
                Submit Flag
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Submit Flag</DialogTitle>
                <DialogDescription>
                  Test flag submission for a team
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label>Game</Label>
                  <Select value={submitGameId} onValueChange={setSubmitGameId}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select a game" />
                    </SelectTrigger>
                    <SelectContent>
                      {games.filter((g) => g.status === "running").map((game) => (
                        <SelectItem key={game.id} value={game.id}>
                          {game.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="teamId">Team ID</Label>
                  <Input
                    id="teamId"
                    placeholder="attacker-team-id"
                    value={submitTeamId}
                    onChange={(e) => setSubmitTeamId(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="flag">Flag</Label>
                  <Input
                    id="flag"
                    placeholder="FLAG{...}"
                    value={submitFlag}
                    onChange={(e) => setSubmitFlag(e.target.value)}
                  />
                </div>
              </div>
              <DialogFooter>
                <DialogClose asChild>
                  <Button variant="outline">Cancel</Button>
                </DialogClose>
                <Button onClick={handleSubmitFlag} disabled={isSubmitting}>
                  {isSubmitting && <Loader2 className="mr-2 size-4 animate-spin" />}
                  Submit
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Submission History</CardTitle>
              <CardDescription>
                {submissions.length} submissions shown
              </CardDescription>
            </div>
            <Select value={filterStatus} onValueChange={setFilterStatus}>
              <SelectTrigger className="w-[150px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="accepted">Accepted</SelectItem>
                <SelectItem value="rejected">Rejected</SelectItem>
                <SelectItem value="duplicate">Duplicate</SelectItem>
                <SelectItem value="expired">Expired</SelectItem>
                <SelectItem value="own_flag">Own Flag</SelectItem>
                <SelectItem value="invalid">Invalid</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent>
          {submissions.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <Send className="mb-2 size-8 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">No submissions yet</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Team</TableHead>
                  <TableHead>Flag</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Points</TableHead>
                  <TableHead>Submitted</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {submissions.map((submission) => (
                  <TableRow key={submission.id}>
                    <TableCell className="font-medium">{submission.attacker_team_id}</TableCell>
                    <TableCell className="font-mono text-xs max-w-[200px] truncate">
                      {submission.submitted_flag}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {getStatusIcon(submission.status)}
                        <Badge className={getStatusColor(submission.status)}>
                          {submission.status.replace("_", " ")}
                        </Badge>
                      </div>
                    </TableCell>
                    <TableCell>
                      <span className={submission.points > 0 ? "text-emerald-500 font-medium" : "text-muted-foreground"}>
                        {submission.points > 0 ? `+${submission.points}` : submission.points}
                      </span>
                    </TableCell>
                    <TableCell className="text-muted-foreground text-sm">
                      {formatDate(submission.submitted_at)}
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
