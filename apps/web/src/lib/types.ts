/**
 * Contrato JSON entre a API (FastAPI, pasta api/) e o frontend (Next.js, pasta web/).
 * Todos os campos usam snake_case, como no Python. Datas são strings ISO (YYYY-MM-DD).
 * Valores ausentes viram null, nunca NaN. Erros: HTTP 4xx/5xx com corpo { detail: string }.
 */

export type PlayerRef = { id: string; name: string };

export type SeasonStatus =
  | "upcoming"
  | "active"
  | "closed_pending"
  | "homologated"
  | "unknown";

export type SeasonInfo = {
  number: number;
  label: string;
  starts_on: string | null;
  ends_on: string | null;
  status: SeasonStatus;
  homologated: boolean;
  /** Presente apenas quando status === "active". */
  progress: { day: number; total_days: number; remaining: number } | null;
  /** BO1/BO3 completos na temporada. */
  completed_series: number;
};

export type Meta = {
  /** true quando o servidor roda com dados sintéticos (EDB_DEMO=1). */
  demo: boolean;
  /** true quando usa Supabase; false = SQLite local. */
  cloud: boolean;
  generated_at: string;
  today: string;
  current_season: number;
  seasons: SeasonInfo[];
  counts: { players: number; matches: number; maps: number; kills: number };
};

/* ---------- Visão geral ---------- */

export type DrawPlayer = { id: string; name: string; level: number };

export type Highlight = {
  title: "MVP" | "Revelação" | "Xinxa";
  ranking: "elite" | "superacao" | "xp";
  player: PlayerRef | null;
  /** Ex.: "Índice 74,2 • 8 partidas" ou "Exige pelo menos 6 mapas". */
  detail: string;
};

export type Home = {
  season: SeasonInfo;
  counts: { players: number; matches: number; kills: number; xp_distributed: number };
  highlights: Highlight[];
  top_elite: { player_id: string; name: string; elite: number }[];
  /** Jogadores ativos, para o sorteador. */
  roster: DrawPlayer[];
};

/** Arquivo de temporadas: uma entrada por temporada iniciada, da mais nova para a mais antiga. */
export type SeasonArchiveItem = {
  season: SeasonInfo;
  counts: { players: number; matches: number; kills: number; xp_distributed: number };
  /** Títulos da temporada; só são oficiais quando season.homologated é true. */
  highlights: Highlight[];
};

export type SeasonArchive = { seasons: SeasonArchiveItem[] };

/** Votação de MVP de um mapa. Depende de quem está logado; nunca expõe quem votou em quem. */
export type MatchMvp = {
  /** "unavailable": banco offline ou recurso ainda não ativado. */
  status: "open" | "closed" | "unavailable";
  closes_on: string;
  /** Jogadores do mapa (quem pode votar). */
  electorate: number;
  votes_cast: number;
  /** Quem a pessoa logada pode escolher (sem ela mesma). */
  candidates: PlayerRef[];
  viewer: {
    logged_in: boolean;
    player_id: string | null;
    can_vote: boolean;
    my_vote: string | null;
    /** Motivo de não poder votar, para mostrar na tela. */
    reason: string | null;
  };
  /** Só depois que a votação fecha; os empatados em primeiro têm mvp true. */
  results: { player: PlayerRef; votes: number; mvp: boolean }[] | null;
};

/* ---------- Rankings ---------- */

export type RankingType = "elite" | "superacao" | "xp" | "bagres";

export type RankingRow = {
  rank: number;
  player_id: string;
  name: string;
  /** 0 no ranking bagres (usa level). */
  stars: number;
  level: number | null;
  matches: number;
  maps_played: number | null;
  kills: number;
  kd: number | null;
  kpr: number | null;
  adr: number | null;
  wins: number;
  elite: number | null;
  superacao: number | null;
  xp: number | null;
  eligible: boolean;
  /** true quando eligible é false (texto "Provisório"). */
  provisional: boolean;
  /** Valor do ranking em foco (elite | superacao | xp | adr). */
  focus: number | null;
};

export type Ranking = {
  season: SeasonInfo;
  type: RankingType;
  title: string;
  focus_label: string;
  focus_unit: "" | "%";
  rows: RankingRow[];
  /** Somente superacao: últimas 2 partidas vs 2 anteriores. */
  progress: { name: string; change_pct: number; games: number }[] | null;
  /** Textos de metodologia, na ordem de exibição. */
  notes: string[];
};

export type MissionWeek = {
  number: number;
  total: number;
  starts_on: string;
  ends_on: string;
  days_left: number;
  /** true quando a temporada já acabou (mostra a última semana). */
  closed: boolean;
};

export type MissionPlayer = {
  player: PlayerRef;
  level: number | null;
  stars: number;
  /** KPR da meta, pelo nível de estrelas. */
  target: number;
  /** done: cumprida e conta no XP; unselected: bateu a meta, mas o mapa ficou fora dos 6 do XP; open: jogou e não bateu; none: sem partidas na semana. */
  status: "done" | "unselected" | "open" | "none";
  maps_in_week: number;
  /** Melhor KPR da semana em mapas de 8 rounds ou mais. */
  best_kpr: number | null;
};

export type Missions = {
  targets: { stars: number; kpr: number }[];
  xp: Ranking;
  week: MissionWeek | null;
  players: MissionPlayer[];
};

/* ---------- Jogadores ---------- */

export type PlayerListItem = {
  id: string;
  nickname: string;
  real_name: string | null;
  /** "Nome real (nick)" ou o nick. */
  name: string;
  stars: number;
  level: number;
  is_active: boolean;
};

export type SteamView = {
  state: "linked" | "unlinked" | "invalid" | "no_key" | "error" | "notfound";
  avatar: string;
  persona: string;
  hours: number | null;
  note: string;
};

export type PlayerSummary = {
  games: number;
  wins: number;
  win_rate: number | null;
  kills: number;
  deaths: number;
  assists: number;
  kd: number | null;
  kpr: number | null;
  adr: number | null;
  best: { kills: number; map: string; date: string; match_id: string } | null;
};

export type PlayerMatchRow = {
  match_id: string;
  date: string;
  map: string;
  played_nick: string;
  result: "win" | "loss" | "unknown";
  kills: number;
  deaths: number;
  assists: number;
  rounds: number;
  kd: number | null;
  kpr: number | null;
  adr: number | null;
  rating: number | null;
};

export type Medal = {
  id: string;
  name: string;
  tier: "bronze" | "silver" | "gold";
  description: string;
  metric: string;
  target: number;
  current: number | null;
  earned: boolean;
  /** 0-100, null quando a métrica não está disponível. */
  progress: number | null;
};

export type StatUnit = "n" | "pct" | "s";

/** Métrica de uma seção do perfil. `t` e `ct` só existem quando a demo permite separar por lado. */
export type AdvMetric = {
  key: string;
  /** Nome da HLTV, em inglês. */
  label: string;
  /** Significado em português, mostrado em letra menor ao lado do nome. */
  meaning: string;
  value: number | null;
  t: number | null;
  ct: number | null;
  unit: StatUnit;
  decimals: number;
  hint: string;
  /** Definição própria da liga, não idêntica à da HLTV. */
  adapted: boolean;
};

export type AdvCard = { key: string; label: string; meaning: string; value: number | null; unit: StatUnit; decimals: number };

export type AdvScore = { key: string; label: string; meaning: string; value: number | null };

export type AdvSections = {
  firepower: AdvMetric[];
  entrying: AdvMetric[];
  trading: AdvMetric[];
  opening: AdvMetric[];
  closing: AdvMetric[];
  sniping: AdvMetric[];
  utility: AdvMetric[];
};

export type AdvRating = {
  rating1: number | null;
  rating1_t: number | null;
  rating1_ct: number | null;
  rating2: number | null;
  rating2_t: number | null;
  rating2_ct: number | null;
};

export type AdvMultikill = { kills: number; rounds: number; t: number; ct: number; pct: number | null };
export type AdvClutch = { label: string; tries: number; won: number };
export type AdvWeaponClass = { label: string; kills: number; pct: number | null };
export type AdvWeapon = { weapon: string; kills: number; pct: number | null };
export type AdvSpecialKill = { label: string; kills: number };

export type AdvTotals = {
  kills: number;
  deaths: number;
  assists: number;
  rounds_with_kill: number;
  plants: number;
  defuses: number;
  kills_t: number;
  kills_ct: number;
};

export type AdvMap = {
  map: string;
  games: number;
  wins: number;
  win_rate: number | null;
  kpr: number | null;
  adr: number | null;
  rating: number | null;
};

export type AdvCompany = { player: PlayerRef; games: number; rating: number | null; win_rate: number | null };
export type AdvSimilar = { player: PlayerRef; similarity: number };

/** Estatísticas calculadas a partir das demos. `null` quando nenhuma partida do jogador tem demo. */
export type AdvSide = "all" | "t" | "ct";

export type AdvFilters = {
  /** Filtros aplicados, já normalizados pela API. */
  applied: { side: "t" | "ct" | null; map: string | null; format: "bo1" | "bo3" | null; season: number | null };
  /** Valores que existem nas partidas com demo deste jogador. */
  options: { maps: string[]; formats: ("bo1" | "bo3")[]; seasons: number[] };
};

export type AdvancedStats = {
  rounds: number;
  side: AdvSide;
  filters: AdvFilters;
  rating: AdvRating;
  cards: AdvCard[];
  sections: AdvSections;
  multikills: AdvMultikill[];
  clutches: AdvClutch[];
  weapon_classes: AdvWeaponClass[];
  weapons: AdvWeapon[];
  special_kills: AdvSpecialKill[];
  totals: AdvTotals;
  scores: AdvScore[];
  similar: AdvSimilar[];
  coverage: { maps_with_demo: number; maps_total: number };
  maps: AdvMap[];
  teammates: AdvCompany[];
  opponents: AdvCompany[];
};

/** Ratings da demo sem filtro, para o cabeçalho. `null` quando nenhuma partida do jogador tem demo. */
export type AdvHeadline = {
  rating1: number | null;
  rating1_t: number | null;
  rating1_ct: number | null;
  rating2: number | null;
  rating2_t: number | null;
  rating2_ct: number | null;
  maps_with_demo: number;
};

export type PlayerDetail = {
  player: PlayerListItem;
  steam: SteamView;
  summary: PlayerSummary;
  /** Mais recente primeiro. */
  matches: PlayerMatchRow[];
  medals: Medal[];
  headline: AdvHeadline | null;
  advanced: AdvancedStats | null;
};

/* ---------- Comparar ---------- */

export type CompareMetric = {
  key: string;
  label: string;
  first: number | null;
  second: number | null;
  decimals: number;
  suffix: string;
  better: "first" | "second" | "tie" | null;
};

export type Compare = {
  first: PlayerListItem;
  second: PlayerListItem;
  metrics: CompareMetric[];
  shared_count: number;
  opponent_games: number;
  teammate_games: number;
  head_to_head: { first: number; second: number };
  shared: {
    match_id: string;
    date: string;
    map: string;
    relation: "Mesmo time" | "Adversários" | "Lados não confirmados";
    first: { kills: number; adr: number | null };
    second: { kills: number; adr: number | null };
  }[];
};

/* ---------- Hall da Fama e medalhas ---------- */

export type RecordCard = {
  title: string;
  value: string;
  holders: PlayerRef[];
  detail: string;
};

export type Hall = {
  match_count: number;
  henio: {
    adr: number;
    holders: { id: string; name: string; maps: number }[];
    min_maps: number;
  } | null;
  /** Todos os recordes, na ordem de hall_of_fame(). */
  records: RecordCard[];
  top_kills: { player: PlayerRef; kills: number }[];
  titles: {
    season_number: number;
    title: "MVP" | "Revelação" | "Xinxa";
    ranking: "elite" | "superacao" | "xp";
    player: PlayerRef | null;
    score: number;
  }[];
};

export type MedalCatalogue = {
  summary: {
    available: number;
    honored_players: number;
    tiers: number;
    earned_total: number;
  };
  medals: (Omit<Medal, "current" | "earned" | "progress"> & {
    holders: PlayerRef[];
  })[];
};

/* ---------- Partidas ---------- */

export type MapCard = {
  id: string;
  /** Nome do mapa em maiúsculas, como em fixture_overview(). */
  map: string;
  date_label: string;
  date: string | null;
  left: string;
  right: string;
  score_left: number | null;
  score_right: number | null;
  verified: boolean;
  winner: "left" | "right" | null;
};

export type SeriesCard = {
  id: string;
  format: "bo1" | "bo3";
  date_label: string;
  status: "FINALIZADA" | "EM ANDAMENTO" | "AGUARDANDO REGISTRO";
  complete: boolean;
  /** PT sempre à esquerda e PL à direita quando identificados. */
  left: string;
  right: string;
  score_left: number | null;
  score_right: number | null;
  winner: "left" | "right" | null;
  summary: string;
  maps: MapCard[];
};

export type MatchesList = {
  season: SeasonInfo;
  bo1: SeriesCard[];
  bo3: SeriesCard[];
  /** Mapas antigos ainda não agrupados em BO1/BO3. */
  legacy: MapCard[];
};

export type ScoreRow = {
  player: string;
  k: number;
  a: number;
  d: number;
  kd: number | null;
  adr: number | null;
};

export type TeamTable = {
  name: string;
  outcome: "win" | "loss" | "unknown";
  players: number;
  kills: number;
  rows: ScoreRow[];
};

export type RoundReason = "eliminacao" | "bomba" | "desarme" | "tempo";

/** Um round do mapa, do ponto de vista dos times da esquerda (PT) e da direita (PL) do cartão da partida. */
export type RoundEntry = {
  round: number;
  winner: "left" | "right";
  /** Lado que o time vencedor jogava. */
  side: "t" | "ct";
  /** Null quando a demo não permite saber (por exemplo, CT venceu sem bomba e o jogo não informou o motivo). */
  reason: RoundReason | null;
  planted: boolean;
  /** Placar acumulado depois do round. */
  score_left: number;
  score_right: number;
};

export type RoundTimeline = { rounds: RoundEntry[] };

export type MatchDetail = {
  match: MapCard;
  season: number | null;
  series_id: string | null;
  series_format: "bo1" | "bo3" | null;
  /** Rounds do mapa; null quando a partida não veio de uma demo analisada (ou o recurso ainda não foi ativado). */
  timeline: RoundTimeline | null;
  teams: TeamTable[];
  general: {
    player: string;
    kills: number;
    deaths: number;
    assists: number;
    damage: number | null;
    rounds: number;
    won: boolean | null;
    rating: number | null;
    kast: number | null;
    open_kills: number | null;
    trade_kills: number | null;
    adr_reported: number | null;
    adr_difference: number | null;
  }[];
  aim: {
    player: string;
    time_to_kill_seconds: number | null;
    damage_time_seconds: number | null;
    aim_accuracy_pct: number | null;
    rifle_hs_pct: number | null;
    pistol_hs_pct: number | null;
    first_bullet_accuracy_pct: number | null;
  }[];
  utility: {
    player: string;
    flash_assists: number | null;
    impactful_flash_assists: number | null;
    enemies_flashed: number | null;
    total_flash_duration_seconds: number | null;
    grenade_damage: number | null;
    smokes_used: number | null;
    enemies_damaged_fire: number | null;
    enemies_damaged_he: number | null;
  }[];
  coverage: { players: number; kills: number; aim: number; grenades: number };
  source: string;
  rounds_total: number | null;
  notes: string | null;
};

/* ---------- Sorteador ---------- */

export type DrawResult = {
  team_a: DrawPlayer[];
  team_b: DrawPlayer[];
  total_a: number;
  total_b: number;
  gap: number;
  /** Texto pronto para copiar no grupo. */
  message: string;
};

/* ---------- Administração ---------- */

export type AdminSession = {
  authenticated: boolean;
  configured: boolean;
  /** true quando o login do administrador pela Steam está ligado no servidor. */
  steam: boolean;
  /** true quando a entrada por senha está ativa. */
  password: boolean;
};

/** Quem está logado (resposta de /api/me). O SteamID nunca é devolvido. */
export type Me = {
  login_enabled: boolean;
  authenticated: boolean;
  is_admin: boolean;
  player: PlayerListItem | null;
  /** Foto da Steam, quando a chave da Steam está configurada. */
  avatar: string | null;
};

export type AdminPlayer = PlayerListItem & { steamid: string | null };

export type AdminOverview = {
  cloud: boolean;
  players: AdminPlayer[];
  /** Temporadas encerradas ainda sem homologação. */
  pending_seasons: SeasonInfo[];
  /** Temporadas abertas (n >= 1, sem homologação) para registrar confrontos. */
  open_seasons: SeasonInfo[];
};

export type ImportPlayer = {
  nickname: string;
  steamid: string;
  kills: number;
  deaths: number;
  assists: number;
  damage: number | null;
  rounds: number;
  headshots: number;
  plants: number;
  defuses: number;
  rating: number | null;
  kast: number | null;
  open_kills: number | null;
  trade_kills: number | null;
  /** Vitória detectada na leitura (opcional). */
  won?: boolean | null;
};

export type ImportPreview = {
  fingerprint: string;
  map: string;
  rounds_total: number;
  source: string;
  warnings: string[];
  players: ImportPlayer[];
  /** true se o ID da partida já existe no banco. */
  duplicate: boolean;
  /** true se a demo tem 0 kills e 0 mortes (leitura inválida). */
  invalid_stats: boolean;
  /** Data tirada do nome do arquivo (md1_mapa_dd_mm), ou null se o nome fora do padrão não a traz. */
  played_at: string | null;
};

export type ImportCommit = {
  fingerprint: string;
  source: string;
  played_at: string;
  map_name: string;
  rounds_total: number;
  note: string;
  players: ImportPlayer[];
  /** Nicknames do time vencedor; vazio = não informado. */
  winners: string[];
};

export type SeriesPlayer = {
  steamid: string;
  nick: string;
  /** A = primeiro time (PT por padrão), B = segundo. */
  team: "A" | "B";
  player_id: string | null;
  player: string | null;
  kills: number;
  deaths: number;
  assists: number;
  adr: number;
  kast: number;
  headshots: number;
  rating: number | null;
};

export type SeriesMap = {
  file: string;
  map: string;
  order: number;
  rounds: number;
  score_a: number;
  score_b: number;
  warnings: string[];
  players: SeriesPlayer[];
};

export type SeriesPending = {
  steamid: string;
  nick: string;
  suggestion: { id: string; nickname: string } | null;
};

export type SeriesItem = {
  key: string;
  label: string;
  format: "bo1" | "bo3";
  played_on: string;
  season: number | null;
  basis: string;
  problems: string[];
  notes: string[];
  changes: string[];
  maps: SeriesMap[];
  unresolved: SeriesPending[];
  can_commit: boolean;
  /** Devolvido sem alteração na gravação. */
  payload: string;
};

export type SeriesPreview = {
  team_a: string;
  team_b: string;
  notes: string[];
  series: SeriesItem[];
  players: { id: string; nickname: string; has_steamid: boolean }[];
};

export type SeriesChoice = {
  kind: "link" | "alias" | "new";
  player_id?: string;
  nickname?: string;
};

export type SeriesCommitResult = {
  ok: boolean;
  match_ids: string[];
  label: string;
  parser_version: number;
};

export type ConfrontCandidates = {
  season: SeasonInfo;
  maps: {
    id: string;
    played_at: string;
    map_name: string;
    label: string;
    rounds_total: number | null;
    team_a_score: number | null;
    team_b_score: number | null;
    /** IDs dos jogadores com estatística neste mapa. */
    player_ids: string[];
  }[];
  players: PlayerRef[];
};

export type ConfrontRequest = {
  season: number;
  format: "bo1" | "bo3";
  match_ids: string[];
  team_a_ids: string[];
  scores: Record<string, [number, number]>;
  team_a_name: string;
  team_b_name: string;
};
