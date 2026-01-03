"use client"

import { useEffect, useState, useRef } from "react"
import { Shield, Upload, Trash2, MoreHorizontal, Loader2, RefreshCw, Edit } from "lucide-react"
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
import type { Vulnbox } from "@/lib/types"

export default function VulnboxesPage() {
  const [vulnboxes, setVulnboxes] = useState<Vulnbox[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isUploading, setIsUploading] = useState(false)
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [deleteId, setDeleteId] = useState<string | null>(null)
  
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [file, setFile] = useState<File | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  async function fetchVulnboxes() {
    try {
      setIsLoading(true)
      const response = await api.vulnboxes.list()
      setVulnboxes(response.items)
    } catch (error) {
      toast.error("Failed to fetch vulnboxes")
      console.error(error)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchVulnboxes()
  }, [])

  async function handleUpload() {
    if (!name.trim() || !file) {
      toast.error("Please provide a name and select a file")
      return
    }

    try {
      setIsUploading(true)
      await api.vulnboxes.create(name, file, description || undefined)
      toast.success("Vulnbox uploaded successfully")
      setIsDialogOpen(false)
      resetForm()
      fetchVulnboxes()
    } catch (error) {
      toast.error("Failed to upload vulnbox")
      console.error(error)
    } finally {
      setIsUploading(false)
    }
  }

  async function handleDelete() {
    if (!deleteId) return

    try {
      await api.vulnboxes.delete(deleteId)
      toast.success("Vulnbox deleted successfully")
      setDeleteId(null)
      fetchVulnboxes()
    } catch (error) {
      toast.error("Failed to delete vulnbox")
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
          <h1 className="text-3xl font-bold tracking-tight">Vulnboxes</h1>
          <p className="text-muted-foreground">
            Manage vulnerable Docker images for CTF challenges
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="icon" onClick={fetchVulnboxes} disabled={isLoading}>
            <RefreshCw className={`size-4 ${isLoading ? "animate-spin" : ""}`} />
          </Button>
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Upload className="mr-2 size-4" />
                Upload Vulnbox
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Upload Vulnbox</DialogTitle>
                <DialogDescription>
                  Upload a .zip file containing your vulnerable Docker image
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Name</Label>
                  <Input
                    id="name"
                    placeholder="my-vulnbox"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="description">Description (optional)</Label>
                  <Textarea
                    id="description"
                    placeholder="A brief description of this vulnbox..."
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="file">Vulnbox File (.zip)</Label>
                  <Input
                    id="file"
                    type="file"
                    accept=".zip"
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
          <CardTitle>All Vulnboxes</CardTitle>
          <CardDescription>
            {vulnboxes.length} vulnbox{vulnboxes.length !== 1 ? "es" : ""} available
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="size-6 animate-spin text-muted-foreground" />
            </div>
          ) : vulnboxes.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Shield className="mb-3 size-12 text-muted-foreground" />
              <h3 className="text-lg font-medium">No vulnboxes yet</h3>
              <p className="text-sm text-muted-foreground">
                Upload your first vulnbox to get started
              </p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead>Docker Image</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className="w-[50px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {vulnboxes.map((vulnbox) => (
                  <TableRow key={vulnbox.id}>
                    <TableCell className="font-medium">{vulnbox.name}</TableCell>
                    <TableCell className="max-w-[200px] truncate text-muted-foreground">
                      {vulnbox.description || "-"}
                    </TableCell>
                    <TableCell>
                      {vulnbox.docker_image ? (
                        <Badge variant="secondary">{vulnbox.docker_image}</Badge>
                      ) : (
                        <Badge variant="outline">Not built</Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {formatDate(vulnbox.created_at)}
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
                            className="text-destructive"
                            onClick={() => setDeleteId(vulnbox.id)}
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
            <AlertDialogTitle>Delete Vulnbox</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this vulnbox? This action cannot be undone.
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
