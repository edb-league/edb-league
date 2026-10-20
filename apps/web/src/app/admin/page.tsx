import { AdminApp } from "@/components/admin/AdminApp";
import { PageHeader } from "@/components/ui/PageHeader";

export const metadata = {
  title: "Administração",
  robots: { index: false, follow: false },
};

export default function AdminPage() {
  return (
    <>
      <PageHeader
        title="Administração"
        subtitle="Cadastre jogadores, importe partidas, registre confrontos e homologue temporadas."
        art="trophy"
      />
      <div className="mt-6">
        <AdminApp />
      </div>
    </>
  );
}
