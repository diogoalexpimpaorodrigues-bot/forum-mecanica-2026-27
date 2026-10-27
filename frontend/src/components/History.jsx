// O histórico é pessoal e vem do servidor; os filtros só alteram a apresentação.
import React, { useState } from "react";
export default function History({ movements, onExplore }) {
  const [filter, setFilter] = useState("all"),
    [message, setMessage] = useState("");
  const visible = movements.filter(
    (m) => filter === "all" || m.kind === filter,
  );
  async function copy(code) {
    try {
      await navigator.clipboard.writeText(code);
      setMessage("Código copiado.");
    } catch {
      setMessage(
        "Não foi possível copiar automaticamente. Seleciona o código e copia-o manualmente.",
      );
    }
  }
  function download() {
    const quote = (value) => {
      const text = String(value);
      // O CSV não deve transformar uma descrição numa fórmula de uma folha de cálculo.
      const safe =
        typeof value === "string" && /^[=+@\-\t\r]/.test(text.trimStart())
          ? "'" + text
          : text;
      return `"${safe.replaceAll('"', '""')}"`;
    };
    const lines = [
      ["Data", "Movimento", "Pontos", "Código de resgate"],
      ...movements.map((m) => [m.date, m.title, m.amount, m.code || ""]),
    ];
    const blob = new Blob(
      ["\ufeff" + lines.map((row) => row.map(quote).join(";")).join("\r\n")],
      { type: "text/csv;charset=utf-8" },
    );
    const url = URL.createObjectURL(blob),
      link = document.createElement("a");
    link.href = url;
    link.download = "passaporte-forum-historico.csv";
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  return (
    <>
      <div className="section-heading">
        <div>
          <p className="eyebrow">CADA PASSO CONTA</p>
          <h2 id="panel-title" tabIndex={-1}>
            O teu percurso, em movimentos.
          </h2>
        </div>
        {movements.length > 0 && (
          <button className="text-button" onClick={download}>
            Descarregar histórico <span aria-hidden="true">↓</span>
          </button>
        )}
      </div>
      {movements.length === 0 ? (
        <div className="empty compact">
          <span aria-hidden="true">↗</span>
          <h3>A primeira conquista está à tua espera.</h3>
          <p>Conclui um desafio para veres aqui o teu progresso.</p>
          <button className="primary" onClick={onExplore}>
            Ver desafios
          </button>
        </div>
      ) : (
        <>
          <div className="filter-row" aria-label="Filtrar movimentos">
            {[
              ["all", "Todos"],
              ["credit", "Pontos ganhos"],
              ["redeem", "Resgates"],
            ].map(([value, label]) => (
              <button
                key={value}
                aria-pressed={filter === value}
                onClick={() => setFilter(value)}
              >
                {label}
              </button>
            ))}
          </div>
          {message && (
            <p className="inline-status" role="status">
              {message}
            </p>
          )}
          {visible.length === 0 ? (
            <p className="empty-filter" role="status">
              Ainda não existem movimentos deste tipo.
            </p>
          ) : (
            <div className="history">
              {visible.map((m) => (
                <article className="movement" key={m.id}>
                  <span
                    className={`movement-icon ${m.kind}`}
                    aria-hidden="true"
                  >
                    {m.amount > 0 ? "↗" : "↙"}
                  </span>
                  <div className="movement-details">
                    <h3>{m.title}</h3>
                    <time dateTime={m.date}>
                      {new Intl.DateTimeFormat("pt-PT", {
                        dateStyle: "medium",
                        timeStyle: "short",
                        timeZone: "Europe/Lisbon",
                      }).format(new Date(m.date))}
                    </time>
                    {m.code && (
                      <div className="redemption-code">
                        <span>Código de resgate</span>
                        <code>{m.code}</code>
                        <button
                          className="text-button"
                          onClick={() => copy(m.code)}
                          aria-label={`Copiar código de ${m.title}`}
                        >
                          Copiar código
                        </button>
                      </div>
                    )}
                  </div>
                  <strong className={m.amount > 0 ? "positive" : ""}>
                    <span className="sr-only">
                      {m.amount > 0 ? "Crédito:" : "Débito:"}
                    </span>
                    {m.amount > 0 ? "+" : ""}
                    {m.amount}
                    <small> pts</small>
                  </strong>
                </article>
              ))}
            </div>
          )}
        </>
      )}
    </>
  );
}
