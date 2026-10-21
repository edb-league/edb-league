/** Marcador de valor ausente: o traço é visual, o leitor de tela lê "sem dados". */
export function NoData() {
  return (
    <>
      <span aria-hidden="true">–</span>
      <span className="sr-only">sem dados</span>
    </>
  );
}
