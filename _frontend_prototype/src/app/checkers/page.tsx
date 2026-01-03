"use client"

import { useEffect, useState, useRef } from "react"
import { Bug, Upload, Trash2, MoreHorizontal, Loader2, RefreshCw, CheckCircle, XCircle } from "lucide-react"
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
import type { Checker } from "@/lib/types"

export default function CheckersPage() {
  const [checkers, setCheckers] = useState<Checker[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isUploading, setIsUploading] = useState(false)
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [deleteId, setDeleteId] = useState<string | null>(null)
  const [validatingId, setValidatingId] = useState<string | null>(null)
  
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [file, setFile] = useState<File | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  async function fetchCheckers() {
    try {
      setIsLoading(true)
      const response = await api.checkers.list()
      setCheckers(response.items)
    } catch (error) {
      toast.error("Failed to fetch checkers")
      console.error(error)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchCheckers()
  }, [])

  async function handleUpload() {
    if (!name.trim() || !file) {
      toast.error("Please provide a name and select a file")
      return
    }

    try {
      setIsUploading(true)
      await api.checkers.create(name, file, description || undefined)
      toast.success("Checker uploaded successfully")
      setIsDialogOpen(false)
      resetForm()
      fetchCheckers()
    } catch (error) {
      toast.error("Failed to upload checker")
      console.error(error)
    } finally {
      setIsUploading(false)
    }
  }

  async function handleValidate(checkerId: string) {
    try {
      setValidatingId(checkerId)
      const result = await api.checkers.validate(checkerId)
      if (result.valid) {
        toast.success("Checker is valid", { description: result.message })
      } else {
        toast.error("Checker validation failed", { description: result.message })
      }
    } catch (error) {
      toast.error("Failed to validate checker")
      console.error(error)
    } finally {
      setValidatingId(null)
    }
  }

  async function handleDelete() {
    if (!deleteId) return

    try {
      await api.checkers.delete(deleteId)
      toast.success("Checker deleted successfully")
      setDeleteId(null)
      fetchCheckers()
    } catch (error) {
      toast.error("Failed to delete checker")
      console.error(error)
    }
  }

  function resetForm() {
    setName("")
    setDescription("")
    setFile(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ""
    }
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
          <h1 className="text-3xl font-bold tracking-tight">Checkers</h1>
          <p className="text-muted-foreground">
            Manage SLA checker scripts for CTF services
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="icon" onClick={fetchCheckers} disabled={isLoading}>
            <RefreshCw className={`size-4 ${isLoading ? "animate-spin" : ""}`} />
          </Button>
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Upload className="mr-2 size-4" />
                Upload Checker
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Upload Checker</DialogTitle>
                <DialogDescription>
                  Upload a Python checker script for SLA checks
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Name</Label>
                  <Input
                    id="name"
                    placeholder="my-checker"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="description">Description (optional)</Label>
                  <Textarea
                    id="description"
                    placeholder="A brief description of this checker..."
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="file">Checker File (.py)</Label>
                  <Input
                    id="file"
                    type="file"
                    accept=".py"
                    ref={fileInputRef}
                    onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                  />
                </div>
              </div>
              <DialogFooter>
                <DialogClose asChild>
                  <Button variant="outline">Cancel</Button>
                </DialogClose>
                <Button onClick={handleUpload} disabled={isUploading}>
                  {isUploading && <Loader2 className="mr-2 size-4 animate-spin" />}
                  Upload
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>All Checkers</CardTitle>
          <CardDescription>
            {checkers.length} checker{checkers.length !== 1 ? "s" : ""} available
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="size-6 animate-spin text-muted-foreground" />
            </div>
          ) : checkers.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Bug className="mb-3 size-12 text-muted-foreground" />
              <h3 className="text-lg font-medium">No checkers yet</h3>
              <p className="text-sm text-muted-foreground">
                Upload your first checker script to get started
              </p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead>Module</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className="w-[50px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {checkers.map((checker) => (
                  <TableRow key={checker.id}>
                    <TableCell className="font-medium">{checker.name}</TableCell>
                    <TableCell className="max-w-[200px] truncate text-muted-foreground">
                      {checker.description || "-"}
                    </TableCell>
                    <TableCell>
                      <Badge variant="secondary" className="font-mono text-xs">
                        {checker.module_name}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {formatDate(checker.created_at)}
                    </TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreHorizontal className="size-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem
                            onClick={() => handleValidate(checker.id)}
                            disabled={validatingId === checker.id}
                          >
                            {validatingId === checker.id ? (
                              <Loader2 className="mr-2 size-4 animate-spin" />
                            ) : (
                              <CheckCircle className="mr-2 size-4" />
                            )}
                            Validate
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem
                            className="text-destructive"
                            onClick={() => setDeleteId(checker.id)}
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
            <AlertDialogTitle>Delete Checker</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this checker? This action cannot be undone.
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
