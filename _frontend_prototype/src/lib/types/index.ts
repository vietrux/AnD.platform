export type GameStatus = "draft" | "deploying" | "running" | "paused" | "finished"
export type TickStatus = "pending" | "active" | "completed" | "error"
export type SubmissionStatus = "accepted" | "rejected" | "duplicate" | "expired" | "own_flag" | "invalid"
export type CheckStatus = "up" | "down" | "error"
export type FlagType = "user" | "root"

export interface Game {
  id: string
  name: string
  description: string | null
  vulnbox_path: string | null
  checker_module: string | null
  status: GameStatus
  tick_duration_seconds: number
  current_tick: number
  start_time: string | null
  created_at: string
}

export interface GameCreate {
  name: string
  description?: string | null
  tick_duration_seconds?: number
}

export interface GameUpdate {
  name?: string | null
  description?: string | null
  tick_duration_seconds?: number | null
}

export interface GameListResponse {
  games: Game[]
  total: number
}

export interface GameTeam {
  id: string
  game_id: string
  team_id: string
  container_name: string | null
  container_ip: string | null
  ssh_username: string | null
  ssh_password: string | null
  ssh_port: number | null
  is_active: boolean
  created_at: string
}

export interface GameTeamAdd {
  team_id: string
}

export interface Vulnbox {
  id: string
  name: string
  description: string | null
  path: string
  docker_image: string | null
  created_at: string
}

export interface VulnboxUpdate {
  name?: string | null
  description?: string | null
}

export interface VulnboxListResponse {
  items: Vulnbox[]
  total: number
  skip: number
  limit: number
  has_more: boolean
}

export interface Checker {
  id: string
  name: string
  description: string | null
  file_path: string
  module_name: string
  created_at: string
}

export interface CheckerUpdate {
  name?: string | null
  description?: string | null
}

export interface CheckerListResponse {
  items: Checker[]
  total: number
  skip: number
  limit: number
  has_more: boolean
}

export interface ValidateResponse {
  valid: boolean
  message: string
}

export interface Tick {
  id: string
  game_id: string
  tick_number: number
  status: TickStatus
  flags_placed: number
  started_at: string | null
  completed_at: string | null
  created_at: string
}

export interface TickListResponse {
  items: Tick[]
  total: number
  skip: number
  limit: number
  has_more: boolean
}

export interface Flag {
  id: string
  game_id: string
  team_id: string
  tick_id: string
  flag_value: string
  flag_type: FlagType
  is_stolen: boolean
  stolen_count: number
  expires_at: string | null
  created_at: string
}

export interface FlagListResponse {
  items: Flag[]
  total: number
  skip: number
  limit: number
  has_more: boolean
}

export interface FlagStats {
  total_flags: number
  stolen_flags: number
  not_stolen_flags: number
  total_steals: number
}

export interface FlagSubmit {
  game_id: string
  team_id: string
  flag: string
}

export interface SubmissionResponse {
  status: SubmissionStatus
  points: number
  message: string
}

export interface SubmissionDetail {
  id: string
  game_id: string
  attacker_team_id: string
  flag_id: string | null
  submitted_flag: string
  status: SubmissionStatus
  points: number
  submitted_at: string
}

export interface SubmissionListResponse {
  items: SubmissionDetail[]
  total: number
  skip: number
  limit: number
  has_more: boolean
}

export interface ScoreboardEntry {
  team_id: string
  attack_points: number
  defense_points: number
  sla_points: number
  total_points: number
  rank: number
  flags_captured: number
  flags_lost: number
}

export interface ScoreboardResponse {
  game_id: string
  game_name: string
  current_tick: number
  entries: ScoreboardEntry[]
  last_updated: string | null
}

export interface ServiceStatus {
  id: string
  game_id: string
  team_id: string
  tick_id: string
  status: CheckStatus
  sla_percentage: number
  error_message: string | null
  check_duration_ms: number | null
  checked_at: string
}

export interface ServiceStatusListResponse {
  items: ServiceStatus[]
  total: number
  skip: number
  limit: number
  has_more: boolean
}

export interface DeleteResponse {
  deleted_id: string
  message: string
}

export interface PaginationParams {
  skip?: number
  limit?: number
}
