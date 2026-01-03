import type {
  Game,
  GameCreate,
  GameUpdate,
  GameListResponse,
  GameTeam,
  GameTeamAdd,
  Vulnbox,
  VulnboxUpdate,
  VulnboxListResponse,
  Checker,
  CheckerUpdate,
  CheckerListResponse,
  ValidateResponse,
  Tick,
  TickListResponse,
  Flag,
  FlagListResponse,
  FlagStats,
  FlagSubmit,
  SubmissionResponse,
  SubmissionDetail,
  SubmissionListResponse,
  ScoreboardResponse,
  ScoreboardEntry,
  ServiceStatus,
  ServiceStatusListResponse,
  DeleteResponse,
  PaginationParams,
  SubmissionStatus,
} from "@/lib/types"

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

async function fetchApi<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    ...options,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown error" }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  return response.json()
}

async function fetchFormData<T>(
  endpoint: string,
  formData: FormData
): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    method: "POST",
    body: formData,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown error" }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  return response.json()
}

export const api = {
  games: {
    list: (params?: PaginationParams) =>
      fetchApi<GameListResponse>(`/games?skip=${params?.skip ?? 0}&limit=${params?.limit ?? 100}`),
    
    get: (gameId: string) =>
      fetchApi<Game>(`/games/${gameId}`),
    
    create: (data: GameCreate) =>
      fetchApi<Game>("/games", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    
    update: (gameId: string, data: GameUpdate) =>
      fetchApi<Game>(`/games/${gameId}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
    
    delete: (gameId: string) =>
      fetchApi<DeleteResponse>(`/games/${gameId}`, { method: "DELETE" }),
    
    start: (gameId: string) =>
      fetchApi<void>(`/games/${gameId}/start`, { method: "POST" }),
    
    pause: (gameId: string) =>
      fetchApi<void>(`/games/${gameId}/pause`, { method: "POST" }),
    
    stop: (gameId: string) =>
      fetchApi<void>(`/games/${gameId}/stop`, { method: "POST" }),
    
    assignVulnbox: (gameId: string, vulnboxId: string) =>
      fetchApi<Game>(`/games/${gameId}/assign-vulnbox?vulnbox_id=${vulnboxId}`, { method: "POST" }),
    
    assignChecker: (gameId: string, checkerId: string) =>
      fetchApi<Game>(`/games/${gameId}/assign-checker?checker_id=${checkerId}`, { method: "POST" }),
    
    teams: {
      list: (gameId: string) =>
        fetchApi<GameTeam[]>(`/games/${gameId}/teams`),
      
      get: (gameId: string, teamId: string) =>
        fetchApi<GameTeam>(`/games/${gameId}/teams/${teamId}`),
      
      add: (gameId: string, data: GameTeamAdd) =>
        fetchApi<GameTeam>(`/games/${gameId}/teams`, {
          method: "POST",
          body: JSON.stringify(data),
        }),
      
      remove: (gameId: string, teamId: string) =>
        fetchApi<DeleteResponse>(`/games/${gameId}/teams/${teamId}`, { method: "DELETE" }),
    },
  },

  vulnboxes: {
    list: (params?: PaginationParams) =>
      fetchApi<VulnboxListResponse>(`/vulnboxes?skip=${params?.skip ?? 0}&limit=${params?.limit ?? 50}`),
    
    get: (vulnboxId: string) =>
      fetchApi<Vulnbox>(`/vulnboxes/${vulnboxId}`),
    
    create: (name: string, file: File, description?: string) => {
      const formData = new FormData()
      formData.append("file", file)
      const url = `/vulnboxes?name=${encodeURIComponent(name)}${description ? `&description=${encodeURIComponent(description)}` : ""}`
      return fetchFormData<Vulnbox>(url, formData)
    },
    
    update: (vulnboxId: string, data: VulnboxUpdate) =>
      fetchApi<Vulnbox>(`/vulnboxes/${vulnboxId}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
    
    delete: (vulnboxId: string) =>
      fetchApi<DeleteResponse>(`/vulnboxes/${vulnboxId}`, { method: "DELETE" }),
  },

  checkers: {
    list: (params?: PaginationParams) =>
      fetchApi<CheckerListResponse>(`/checkers?skip=${params?.skip ?? 0}&limit=${params?.limit ?? 50}`),
    
    get: (checkerId: string) =>
      fetchApi<Checker>(`/checkers/${checkerId}`),
    
    create: (name: string, file: File, description?: string) => {
      const formData = new FormData()
      formData.append("file", file)
      const url = `/checkers?name=${encodeURIComponent(name)}${description ? `&description=${encodeURIComponent(description)}` : ""}`
      return fetchFormData<Checker>(url, formData)
    },
    
    update: (checkerId: string, data: CheckerUpdate) =>
      fetchApi<Checker>(`/checkers/${checkerId}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
    
    delete: (checkerId: string) =>
      fetchApi<DeleteResponse>(`/checkers/${checkerId}`, { method: "DELETE" }),
    
    validate: (checkerId: string) =>
      fetchApi<ValidateResponse>(`/checkers/${checkerId}/validate`, { method: "POST" }),
  },

  ticks: {
    list: (gameId: string, params?: PaginationParams & { status?: string }) =>
      fetchApi<TickListResponse>(
        `/ticks?game_id=${gameId}&skip=${params?.skip ?? 0}&limit=${params?.limit ?? 50}${params?.status ? `&status=${params.status}` : ""}`
      ),
    
    get: (tickId: string) =>
      fetchApi<Tick>(`/ticks/${tickId}`),
    
    getCurrent: (gameId: string) =>
      fetchApi<Tick | null>(`/ticks/current?game_id=${gameId}`),
    
    getLatest: (gameId: string) =>
      fetchApi<Tick | null>(`/ticks/latest?game_id=${gameId}`),
    
    getByNumber: (gameId: string, tickNumber: number) =>
      fetchApi<Tick>(`/ticks/number/${tickNumber}?game_id=${gameId}`),
  },

  flags: {
    list: (gameId: string, params?: PaginationParams & { team_id?: string; tick_id?: string; is_stolen?: boolean }) =>
      fetchApi<FlagListResponse>(
        `/flags?game_id=${gameId}&skip=${params?.skip ?? 0}&limit=${params?.limit ?? 50}${params?.team_id ? `&team_id=${params.team_id}` : ""}${params?.tick_id ? `&tick_id=${params.tick_id}` : ""}${params?.is_stolen !== undefined ? `&is_stolen=${params.is_stolen}` : ""}`
      ),
    
    get: (flagId: string) =>
      fetchApi<Flag>(`/flags/${flagId}`),
    
    getByValue: (flagValue: string) =>
      fetchApi<Flag>(`/flags/by-value/${encodeURIComponent(flagValue)}`),
    
    getStats: (gameId: string, teamId?: string) =>
      fetchApi<FlagStats>(`/flags/stats?game_id=${gameId}${teamId ? `&team_id=${teamId}` : ""}`),
    
    getByTick: (tickId: string, params?: PaginationParams) =>
      fetchApi<FlagListResponse>(`/flags/tick/${tickId}?skip=${params?.skip ?? 0}&limit=${params?.limit ?? 50}`),
    
    getTeamTickFlags: (gameId: string, teamId: string, tickId: string) =>
      fetchApi<Flag[]>(`/flags/team/${teamId}/tick/${tickId}?game_id=${gameId}`),
  },

  submissions: {
    list: (params?: PaginationParams & { game_id?: string; team_id?: string; status?: SubmissionStatus }) =>
      fetchApi<SubmissionListResponse>(
        `/submissions?skip=${params?.skip ?? 0}&limit=${params?.limit ?? 50}${params?.game_id ? `&game_id=${params.game_id}` : ""}${params?.team_id ? `&team_id=${params.team_id}` : ""}${params?.status ? `&status=${params.status}` : ""}`
      ),
    
    get: (submissionId: string) =>
      fetchApi<SubmissionDetail>(`/submissions/${submissionId}`),
    
    submit: (data: FlagSubmit) =>
      fetchApi<SubmissionResponse>("/submissions", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    
    delete: (submissionId: string) =>
      fetchApi<DeleteResponse>(`/submissions/${submissionId}`, { method: "DELETE" }),
  },

  scoreboard: {
    list: (params?: PaginationParams) =>
      fetchApi<ScoreboardResponse[]>(`/scoreboard?skip=${params?.skip ?? 0}&limit=${params?.limit ?? 50}`),
    
    get: (gameId: string) =>
      fetchApi<ScoreboardResponse>(`/scoreboard/${gameId}`),
    
    getTeamScore: (gameId: string, teamId: string) =>
      fetchApi<ScoreboardEntry>(`/scoreboard/${gameId}/team/${teamId}`),
  },

  checkerStatus: {
    list: (params?: PaginationParams & { game_id?: string; team_id?: string; tick_id?: string }) =>
      fetchApi<ServiceStatusListResponse>(
        `/checker/statuses?skip=${params?.skip ?? 0}&limit=${params?.limit ?? 50}${params?.game_id ? `&game_id=${params.game_id}` : ""}${params?.team_id ? `&team_id=${params.team_id}` : ""}${params?.tick_id ? `&tick_id=${params.tick_id}` : ""}`
      ),
    
    get: (statusId: string) =>
      fetchApi<ServiceStatus>(`/checker/statuses/${statusId}`),
    
    delete: (statusId: string) =>
      fetchApi<DeleteResponse>(`/checker/statuses/${statusId}`, { method: "DELETE" }),
  },

  health: {
    check: () => fetchApi<Record<string, unknown>>("/health"),
  },
}
