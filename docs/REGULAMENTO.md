# Regulamento oficial da EDB LEAGUE — v1.0

**Vigencia:** a partir da Temporada 1 (15/10/2026, dia da primeira partida da liga). A Temporada 0, encerrada em 18/10/2026, e experimental; seus resultados, estatisticas e excecoes permanecem preservados.

## Calendario
- Temporadas mensais consecutivas, do dia 19 ao dia 18 do mes seguinte, no fuso America/Sao_Paulo.
- A **Temporada 1** e a excecao: comeca em 15/10/2026 (primeira partida) e termina em 18/11/2026. T2: 19/11 a 18/12; as seguintes seguem o mesmo padrao.
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
- Seis mapas selecionados para render o maximo de XP: 40 XP por mapa + 20 XP por vitoria + 100 XP por semana coberta por uma missao cumprida em um dos seis mapas. Como a missao vale mais que a vitoria, um mapa de missao pode entrar no lugar de uma vitoria comum.
- Cada semana so precisa de um mapa de missao; nos empates de XP vencem as combinacoes com mais vitorias e, depois, com os mapas realizados primeiro.
- As missoes concedem 100 XP por semana da temporada (blocos de 7 dias contados a partir do primeiro dia da temporada), sem limite de missoes alem da quantidade de semanas; contam apenas os seis mapas selecionados para XP.
- A missao exige KPR pelo menos igual a meta das estrelas, em mapa com no minimo oito rounds.
- O ultimo mapa de uma BO3 que termine apos o encerramento continua na temporada em que a serie comecou, e conta na ultima semana dela, sem gerar bonus de semana extra.
- Uma vitoria vale 40 + 20 = 60 XP; uma derrota, 40 XP.

**Exemplos** (3 estrelas, meta de 0,72 KPR; mapas de 20 rounds, entao 15 kills cumprem a missao):
- *Seis mapas, uma missao:* 4 vitorias, 2 derrotas e uma missao na semana 2 = 6 x 40 + 4 x 20 + 100 = **420 XP**.
- *A missao vale mais que a vitoria:* sete mapas, seis vitorias sem missao e uma derrota com 20 kills na semana 2. So com vitorias seriam 6 x 60 = 360 XP; o site tira uma vitoria e inclui a derrota da missao: 5 x 60 + 40 + 100 = **440 XP**.
- *Duas missoes na mesma semana:* contam 100 XP uma unica vez; a outra vaga vai para a melhor vitoria comum: 6 x 60 + 100 = **460 XP**.

## Estatisticas do perfil
- As notas de 0 a 100 do perfil comparam o jogador com os demais e exigem **no minimo 100 rounds** com demo (cerca de 4 a 5 mapas) tanto para receber nota quanto para entrar na comparacao. Em perfis filtrados por lado, o minimo e de 50 rounds do lado. Antes disso, o perfil mostra "—".
- O ADR por mapa e sempre ponderado: dano total dividido pelos rounds totais, a mesma conta do KPR e dos rankings (nao a media dos ADRs de cada partida).
- Ao gravar uma partida avulsa, e obrigatorio informar quem venceu. Partida sem vencedor definido nao entra no XP nem na taxa de vitoria.

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
- A temporada se encerra automaticamente no dia 18 do mes seguinte (ou em 18/11 na Temporada 1). Novas BO3 iniciadas depois do fim pertencem ao proximo periodo.
- Resultados disputados durante o periodo podem ser lancados posteriormente, ate a homologacao.
- Apos conferir as BO3 e os registros, o administrador homologa as tres classificacoes e os tres titulos. O sistema salva snapshots dos rankings homologados.
- Nao alterar rankings homologados em correcoes posteriores sem revisao administrativa expressa.
- Temporada 0 permanece encerrada e nao recebe os novos criterios retroativamente.

**Aplicacao tecnica:** season_rankings.py, season_system.py, a API e tabelas/funcoes de temporada no Supabase.