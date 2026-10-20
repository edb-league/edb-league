import { redirect } from "next/navigation";
import { parseSeason, seasonQuery } from "@/lib/format";

export default async function RankingsIndex({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const season = parseSeason((await searchParams).temporada);
  redirect(`/rankings/elite${seasonQuery(season)}`);
}
