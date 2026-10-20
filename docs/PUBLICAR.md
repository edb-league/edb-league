# Publicação do XINXAS LEAGUE (Streamlit + Supabase)

Estado em 17/10/2026: repositório e banco criados, migração aplicada, deploy do site ainda pendente.

## Serviços
- Código: https://github.com/matheusbsc6/xinxas-league
- Supabase: https://supabase.com/dashboard/project/cgopqcbgxpzurejtjmbu
- Project URL (pública, **não é uma senha**): https://cgopqcbgxpzurejtjmbu.supabase.co
- Região do banco: São Paulo
- Tabelas: public.players, public.matches, public.player_stats
- RLS ativado; sem políticas para anon/authenticated de propósito.

## Publicar no Streamlit Community Cloud

1. Acesse https://share.streamlit.io e faça login com o **mesmo GitHub**.
2. Selecione **Create app** → **Deploy a public app from GitHub**.
3. Repository: `matheusbsc6/xinxas-league`
4. Branch: `main`
5. Main file path: `app.py`
6. Abra **Advanced settings → Secrets**, e configure **lá**, nunca no GitHub nem nesta conversa:

```toml
XINXAS_ADMIN_PASSWORD = "SUA_SENHA_FORTE_EXCLUSIVA"
SUPABASE_URL = "https://cgopqcbgxpzurejtjmbu.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = "COLE_AQUI_O_SEGREDO_PRIVADO_DO_SUPABASE"
```

7. A chave **service_role** (ou equivalente de privilégios elevados aceita pelo PostgREST) pode ser consultada no projeto Supabase em **Project Settings → API Keys**. Use o valor somente no campo privado **Secrets** do Streamlit. Não a coloque no repositório, em prints ou em mensagens.
8. Clique em **Deploy**, aguarde a instalação e abra o endereço `.streamlit.app` exibido pela hospedagem.
9. Visite **Administração**, entre com a senha e cadastre os jogadores com 1–5 estrelas.
10. Importe uma partida, **revise** a prévia, a data e os vencedores antes de confirmar. O parser de demos ainda necessita validação com arquivo real.

## Verificação

- Os rankings públicos devem mostrar uma tela vazia antes do primeiro registro, sem erro.
- A área Administração deve solicitar senha.
- Ao salvar um jogador, ele deve permanecer cadastrado após recarregar a página.
- No menu lateral deve constar **Banco persistente: Supabase**. Se aparecer **Dados locais (SQLite)**, o deploy NÃO está conectado ao banco e não deve ser usado como produção.
- Confira o GitHub Actions no repositório para os testes unitários (isso não equivale a validar a importação da demo real).

## Segurança e custo

- O projeto Supabase foi criado após confirmação de custo de **US$ 0 por mês** no plano gratuito. Limites de uso e termos podem mudar: confira os planos antes de alterar recursos.
- O Streamlit Community Cloud deve ser utilizado em seu plano gratuito, sujeito às cotas da plataforma. Não aceite upgrades pagos sem avaliar.
- O site é público para leitura por quem recebe o link. Apenas a aba Administração exige senha.
- O banco bloqueia chamadas anônimas diretas pelo RLS sem políticas. O servidor Streamlit utiliza credencial privilegiada; proteja a senha do administrador.
- Não envie replays com dados privados nem tokens para o GitHub.
