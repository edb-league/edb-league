import { PrivacySettings } from "@/components/players/PrivacySettings";
import { Card } from "@/components/ui/Card";
import { PageHeader } from "@/components/ui/PageHeader";
import { getMe } from "@/lib/me";

export const metadata = {
  title: "Privacidade",
  description: "Quais dados a EDB LEAGUE guarda, o que aparece para os outros e como escolher o que mostrar.",
};

const H2 = "text-3xl md:text-4xl";

export default async function PrivacyPage() {
  const me = await getMe();
  return (
    <>
      <PageHeader title="Privacidade" subtitle="O que o site guarda sobre você, o que os outros veem e como mudar isso." art="home" />

      <Card aria-labelledby="escolhas">
        <h2 id="escolhas" className={H2}>
          Suas escolhas
        </h2>
        <p className="mt-1 mb-4 max-w-prose text-base text-muted">
          A foto, o nome na Steam e as horas de CS vêm do seu perfil público da Steam. Por padrão aparecem no seu perfil da liga; você pode esconder cada um.
        </p>
        <PrivacySettings me={me} />
      </Card>

      <Card aria-labelledby="dados">
        <h2 id="dados" className={H2}>
          O que o site guarda
        </h2>
        <ul className="mt-3 flex max-w-prose list-disc flex-col gap-2 pl-6 text-base">
          <li>
            <b>Cadastro na liga:</b> apelido, nome (se o administrador informou), nível e estrelas. Aparecem nos rankings e nas partidas.
          </li>
          <li>
            <b>Estatísticas das partidas:</b> kills, mortes, dano e o que a demo mostra, por jogador e mapa. Fazem parte do histórico da liga.
          </li>
          <li>
            <b>SteamID:</b> usado só para entrar com a Steam e buscar sua foto. Nunca é mostrado a ninguém, nem a quem tem conta.
          </li>
          <li>
            <b>Votos de MVP:</b> guardados para contar o resultado. Ninguém vê quem votou em quem, e o resultado só sai quando a votação fecha.
          </li>
          <li>
            <b>Sessão:</b> ao entrar com a Steam, um cookie de sessão (protegido, só do site) guarda que você entrou por 14 dias. O tema claro ou escuro fica no
            próprio navegador.
          </li>
        </ul>
      </Card>

      <Card aria-labelledby="nao">
        <h2 id="nao" className={H2}>
          O que o site não faz
        </h2>
        <ul className="mt-3 flex max-w-prose list-disc flex-col gap-2 pl-6 text-base">
          <li>Não pede e-mail, senha da Steam nem dados de pagamento. O login é feito na página da própria Steam.</li>
          <li>Não usa cookies de publicidade nem rastreadores de terceiros.</li>
          <li>Não vende nem repassa dados. O administrador pode ligar avisos no Discord com placar e apelidos, que já são públicos no site.</li>
        </ul>
        <p className="mt-4 max-w-prose text-base text-muted">
          Quer corrigir ou tirar seu cadastro da liga? Fale com o administrador. O histórico de partidas já disputadas pode ser preservado para manter os rankings
          corretos.
        </p>
      </Card>
    </>
  );
}
