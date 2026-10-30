"""Importador de .dem ou .dem.gz do Counter-Strike 2.

A leitura em si fica em ``edb.demo_stats.analyze`` (demoparser2). Este módulo prepara o upload (descompacta,
confere o tamanho, calcula o SHA-256) e converte a análise no formato da prévia do painel.
Toda importação deve ser revisada pelo administrador antes de gravar.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import gzip
import hashlib
import tempfile

MAX_UNCOMPRESSED = 1024 * 1024 * 1024  # 1 GB

@dataclass
class DemoOutput:
    fingerprint: str
    map_name: str
    rounds_total: int
    players: list[dict]
    warnings: list[str]


def prepare_upload(uploaded):
    """Descompacta em blocos, verifica limite, e devolve (TemporaryDirectory, path, sha256)."""
    folder = tempfile.TemporaryDirectory(prefix='xinxas_')
    is_gz = str(uploaded.name).lower().endswith('.gz')
    if not str(uploaded.name).lower().endswith(('.dem','.dem.gz','.gz')):
        folder.cleanup()
        raise ValueError('Formato não suportado: utilize .dem, .dem.gz ou .gz')
    out = Path(folder.name)/'partida.dem'
    uploaded.seek(0)
    sha = hashlib.sha256(); size=0
    try:
        raw = gzip.GzipFile(fileobj=uploaded, mode='rb') if is_gz else uploaded
        try:
            with open(out,'wb') as dest:
                while True:
                    b=raw.read(1024*1024)
                    if not b: break
                    size+=len(b)
                    if size>MAX_UNCOMPRESSED:
                        raise ValueError('Demo descompactada excede 1 GB')
                    sha.update(b); dest.write(b)
        finally:
            if is_gz: raw.close()   # o upload em si é fechado por quem o recebeu
        if size<1024:
            raise ValueError('Arquivo muito pequeno para conter uma demo válida')
        return folder, str(out), sha.hexdigest()
    except Exception:
        folder.cleanup(); raise


def _validate_combat_stats(players, rounds_total):
    """Recusa um placar impossível em vez de fabricar dez jogadores 0/0/0."""
    if int(rounds_total) < 1:
        raise ValueError('Nenhum round oficial identificado na demo.')
    kills = sum(int(p.get('kills') or 0) for p in players)
    deaths = sum(int(p.get('deaths') or 0) for p in players)
    if kills <= 0 or deaths <= 0:
        raise ValueError(
            'A demo identificou os jogadores/rounds, mas não foi possível extrair '
            'as eliminações e mortes (K/D = 0). O resultado não foi salvo. '
            'A versão ou a numeração dos eventos pode ser incompatível.'
        )


def parse_demo_stats(dem_path: str, fingerprint: str) -> DemoOutput:
    """Lê a demo com o ``demo_stats.analyze`` (o mesmo parser do pipeline de linha de comando).

    Devolve o formato do ``parse_demo``, já com vencedor, rating estimado, KAST, aberturas e trades.
    A partida começa no último ``begin_new_match``, então o round faca fica de fora.
    """
    from edb.demo_stats import COUNT_FIELDS, analyze
    from edb.hltv_stats import rating2

    analysis = analyze(dem_path)
    t_score = int(analysis['score']['team_t_first'])
    ct_score = int(analysis['score']['team_ct_first'])
    winner = 2 if t_score > ct_score else 3 if ct_score > t_score else None
    warns = []
    result = []
    for p in analysis['players']:
        estimate = rating2({f: p.get(f, 0) for f in COUNT_FIELDS})
        result.append({
            'nickname': str(p.get('nick') or '') or 'Steam ' + str(p['steamid'])[-6:],
            'steamid': str(p['steamid']),
            'kills': int(p['kills']), 'deaths': int(p['deaths']), 'assists': int(p['assists']),
            'damage': int(p['damage']), 'rounds': int(p['rounds']), 'headshots': int(p['headshots']),
            'plants': int(p['plants']), 'defuses': int(p['defuses']),
            'rating': round(estimate, 2) if estimate is not None else None,
            'kast': int(p['kast']), 'open_kills': int(p['open_kills']), 'trade_kills': int(p['trade_kills']),
            'won': None if winner is None else int(p['team']) == winner,
        })
    rounds_total = int(analysis['rounds'])
    _validate_combat_stats(result, rounds_total)
    if len(result) != 10:
        warns.append(f'{len(result)} participantes reconhecidos; uma partida 5v5 tem 10. Reveja trocas de jogadores.')
    if winner is None:
        warns.append(f'Placar empatado ({t_score}x{ct_score}); marque o vencedor manualmente.')
    if 'warnings' in analysis:
        warns.extend(str(w) for w in analysis['warnings'])
    elif max(t_score, ct_score) < 13:
        warns.append(f'Ninguém chegou a 13 rounds ({t_score}x{ct_score}); confira se a partida acabou antes.')
    warns.append(f'Placar {t_score}x{ct_score} (time que começou de T x time que começou de CT). '
                 'Revise a data: a demo não a traz.')
    return DemoOutput(fingerprint, str(analysis.get('map') or '').title() or 'Não identificado',
                      rounds_total, result, warns)
