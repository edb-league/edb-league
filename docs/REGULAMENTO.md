# Regulamento oficial da EDB LEAGUE — v1.0

**Vigencia:** a partir da Temporada 1 (19/10/2026). A Temporada 0, encerrada em 18/10/2026, e experimental; seus resultados, estatisticas e excecoes permanecem preservados.

## Calendario
- Temporadas consecutivas de **14 dias corridos**, segunda a domingo, no fuso America/Sao_Paulo.
- T1: 19/10/2026 a 01/11/2026; T2: 02/11 a 15/11; seguintes em intervalos sucessivos de 14 dias.
- Nao ha quantidade maxima de BO3 por temporada.
- A BO3 pertence a temporada da data/hora de inicio do primeiro mapa, mesmo se finalizar apos a meia-noite do ultimo dia.
- Cada BO3 envolve duas equipes de cinco jogadores. A vitoria da serie e obtida em 2x0 ou 2x1, mantendo a equipe da serie. Substituicoes excepcionais exigem registro.
- O sistema preserva os mapas historicos da T0, incluindo resultado 3x0 e mudancas de escalação.

## Rankings e elegibilidade
- Sao contabilizados os **seis melhores mapas por jogador e por ranking**, sem limite para mapas adicionais registrados.
- Um jogador precisa de **seis mapas validos disputados** durante a temporada para concorrer aos titulos.
- Elite seleciona os seis maiores indices individuais de Elite, e entao calcula o indice sobre KPR e ADR agregados nesses mapas.
- Superacao seleciona os seis maiores indices individuais proporcionais as estrelas, e entao calcula a media ponderada pelos rounds sobre os mapas selecionados.
- Cada ranking pode escolher um conjunto diferente de seis mapas.
- Formula Elite: 100 x (0,60 x KPR/0,75 + 0,40 x ADR/75). Sem dano informado, utiliza 100 x KPR/0,75.
- Formula Superacao: 100 x (KPR / meta_das_estrelas - 1).
- Metas KPR: 1 estrela 0,42; 2 estrelas 0,57; 3 estrelas 0,72; 4 estrelas 0,87; 5 estrelas 1,02.
- O limite pode ser revisto **somente para temporadas futuras**.

## XP
- Seis mapas selecionados por pontuacao de participacao/vitoria: 40 XP por mapa + 20 XP por vitoria.
- Nos empates de pontuacao de mapa, os realizados primeiro sao priorizados.
- As missoes concedem 100 XP por semana da temporada, no maximo duas por temporada; contam apenas os seis mapas selecionados para XP.
- A missao exige KPR pelo menos igual a meta das estrelas, em mapa com no minimo oito rounds.
- O terceiro mapa de uma BO3 que termine apos o encerramento continua pertencendo a segunda semana da temporada iniciada, sem gerar bonus de terceira semana.

## Estrelas e historico
- O nivel de 1 a 5 estrelas e congelado para cada jogador durante a temporada.
- Mudancas de estrelas feitas durante o ciclo produzem efeito apenas no proximo.
- Todos os mapas continuam nas estatisticas de carreira, ainda que nao pontuem no ranking competitivo.

## Titulos e desempates
- Apenas tres titulos competitivos oficiais por temporada: **MVP** (Elite), **Revelacao** (Superacao) e **Xinxa** (XP).
- Uma pessoa pode conquistar varios titulos.
- Elite: desempate por KPR e depois ADR.
- Superacao: desempate por KPR e depois ADR.
- XP: desempate por vitorias nos mapas selecionados e depois Indice Elite.
- As comparacoes usam valores sem arredondamento intermediario; empate absoluto requer homologacao administrativa.
- Titulos homologados aparecem no Hall da Fama e no perfil do jogador.

## Encerramento e homologacao
- A temporada se encerra automaticamente ao fim do ultimo domingo. Novas BO3 iniciadas depois do fim pertencem ao proximo periodo.
- Resultados disputados durante o periodo podem ser lancados posteriormente, ate a homologacao.
- Apos conferir as BO3 e os registros, o administrador homologa as tres classificacoes e os tres titulos. O sistema salva snapshots dos rankings homologados.
- Nao alterar rankings homologados em correcoes posteriores sem revisao administrativa expressa.
- Temporada 0 permanece encerrada e nao recebe os novos criterios retroativamente.

**Aplicacao tecnica:** season_rankings.py, season_system.py, app.py e tabelas/funcoes de temporada no Supabase.