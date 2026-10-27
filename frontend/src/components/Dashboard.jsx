// O saldo vem sempre do servidor; a seleção de secções fica no URL para sobreviver ao refresh.
// Desenvolvido com auxílio de IA; ver AI_USAGE.md.
import React, { useEffect, useState } from "react";
import Challenge from "./Challenge.jsx";
import Confirm from "./Confirm.jsx";
import History from "./History.jsx";
import RewardArt from "./RewardArt.jsx";
const sections = [
  ["challenges", "Desafios"],
  ["rewards", "Loja de brindes"],
  ["history", "Histórico"],
];
const currentSection = () =>
  sections.some(
    ([key]) => key === new URLSearchParams(location.search).get("view"),
  )
    ? new URLSearchParams(location.search).get("view")
    : "challenges";
export default function Dashboard({ data, act, busy, refresh }) {
  const [section, setSection] = useState(currentSection),
    [reward, setReward] = useState(null);
  useEffect(() => {
    const change = () => setSection(currentSection());
    window.addEventListener("popstate", change);
    return () => window.removeEventListener("popstate", change);
  }, []);
  function navigate(next, focus = false) {
    setSection(next);
    window.history.pushState({}, "", `/dashboard?view=${next}`);
    if (focus)
      requestAnimationFrame(() =>
        document.getElementById("panel-title")?.focus(),
      );
  }
  const completed = data.challenges.filter((c) => c.completed).length;
  const remaining = data.challenges
    .filter((c) => !c.completed)
    .reduce((sum, c) => sum + c.points, 0);
  const available = data.rewards.filter(
    (r) => !r.redeemed && r.cost <= data.balance,
  ).length;
  return (
    <main className="dashboard" id="main-content" tabIndex={-1}>
      <div className="dashboard-breadcrumb">
        <span>PASSAPORTE / ÁREA PESSOAL</span>
        <span>
          <span className="status-dot" /> SESSÃO INICIADA
        </span>
      </div>
      <div className="dashboard-heading">
        <div>
          <p className="eyebrow">O TEU PASSAPORTE FÓRUM</p>
          <h1 id="greeting" tabIndex={-1}>
            Olá, <span>{data.user.username}</span>
            <span className="wave" aria-hidden="true">
              ↗
            </span>
          </h1>
          <p className="muted">
            {completed === data.challenges.length
              ? "Completaste todos os desafios. Leva contigo o que aprendeste."
              : "Há sempre mais uma ideia para pôr em movimento."}
          </p>
        </div>
        <div className="dashboard-tools">
          <span className="edition">
            EDIÇÃO <strong>2026/27</strong>
          </span>
          <button
            className="text-button"
            disabled={busy}
            onClick={() => refresh({ announce: true })}
          >
            Atualizar dados ↻
          </button>
        </div>
      </div>
      <section className="stats" aria-label="O teu progresso">
        <div className="balance">
          <div>
            <p>PONTOS DISPONÍVEIS</p>
            <strong>
              {data.balance}
              <small> pts</small>
            </strong>
            <span>
              {available
                ? `${available} ${available === 1 ? "brinde disponível" : "brindes disponíveis"} para resgatar`
                : "A tua curiosidade tem valor."}
            </span>
          </div>
          <span className="balance-art" aria-hidden="true">
            <span />
            <span />
            <span />
          </span>
        </div>
        <div className="stat">
          <span className="stat-icon" aria-hidden="true">
            ↗
          </span>
          <strong>{data.earned}</strong>
          <p>Pontos conquistados</p>
          <span className="stat-detail">
            {data.spent ?? 0} pontos utilizados
          </span>
        </div>
        <div className="stat">
          <span className="stat-icon" aria-hidden="true">
            ✓
          </span>
          <strong>
            {completed}
            <small> / {data.challenges.length}</small>
          </strong>
          <p>Desafios concluídos</p>
          <progress
            aria-label="Desafios concluídos"
            value={completed}
            max={data.challenges.length}
          />
        </div>
      </section>
      <nav className="section-tabs" aria-label="Secções do passaporte">
        {sections.map(([key, label], index) => (
          <button
            key={key}
            aria-current={section === key ? "page" : undefined}
            onClick={() => navigate(key)}
          >
            <span className="nav-index" aria-hidden="true">
              0{index + 1}
            </span>
            {label}
            {key === "history" && (
              <span aria-hidden="true">{data.movements.length}</span>
            )}
          </button>
        ))}
      </nav>
      {section === "challenges" && (
        <>
          <div className="section-heading">
            <div>
              <p className="eyebrow">APRENDE. PARTICIPA. AVANÇA.</p>
              <h2 id="panel-title" tabIndex={-1}>
                Pequenos desafios, novas descobertas.
              </h2>
            </div>
            <span className="section-meta">
              {remaining
                ? `${remaining} pontos por descobrir`
                : "Percurso concluído ✓"}
            </span>
          </div>
          <div className="cards">
            {data.challenges.map((c, i) => (
              <Challenge
                key={c.id}
                index={i}
                challenge={c}
                busy={busy}
                onAnswer={(id, answer) => act("claim", { id, answer })}
              />
            ))}
          </div>
          <aside className="note">
            <span aria-hidden="true">✦</span>
            <div>
              <strong>
                {completed === data.challenges.length
                  ? "Uma volta completa. Novas ideias na bagagem."
                  : "O conhecimento é só o começo."}
              </strong>
              <p>
                Cada desafio dá pontos uma vez. Na loja, escolhes como os queres
                utilizar.
              </p>
            </div>
            <button onClick={() => navigate("rewards", true)}>
              Explorar brindes →
            </button>
          </aside>
        </>
      )}
      {section === "rewards" && (
        <>
          <div className="section-heading">
            <div>
              <p className="eyebrow">CONQUISTAS QUE LEVAS CONTIGO</p>
              <h2 id="panel-title" tabIndex={-1}>
                Escolhe a tua próxima recompensa.
              </h2>
            </div>
            <span className="section-meta">
              Um exemplar de cada brinde por conta
            </span>
          </div>
          <div className="cards">
            {data.rewards.map((r) => (
              <article
                className={`card reward ${r.redeemed ? "redeemed" : ""}`}
                key={r.id}
              >
                <div className="reward-art">
                  <RewardArt id={r.id} />
                  {r.redeemed && (
                    <span className="reward-badge">Resgatado ✓</span>
                  )}
                </div>
                <span className="points">{r.cost} pts</span>
                <h3>{r.title}</h3>
                <p className="muted">{r.description}</p>
                <button
                  className="secondary full"
                  disabled={busy || r.redeemed || data.balance < r.cost}
                  onClick={() => setReward(r)}
                >
                  {r.redeemed
                    ? "✓ Já resgatado"
                    : data.balance < r.cost
                      ? `Faltam ${r.cost - data.balance} pontos`
                      : "Resgatar brinde ↗"}
                </button>
                {r.redeemed && (
                  <button
                    className="text-button view-code"
                    onClick={() => navigate("history", true)}
                  >
                    Ver código no histórico
                  </button>
                )}
              </article>
            ))}
          </div>
          <p className="muted disclaimer">
            Catálogo de demonstração. Os brindes são ilustrativos e não têm
            entrega física.
          </p>
        </>
      )}
      {section === "history" && (
        <History
          movements={data.movements}
          onExplore={() => navigate("challenges", true)}
        />
      )}
      {reward && (
        <Confirm
          reward={reward}
          balance={data.balance}
          busy={busy}
          onClose={() => setReward(null)}
          onConfirm={async () => {
            const result = await act("redeem", { id: reward.id });
            if (result.ok) {
              setReward(null);
              navigate("history", true);
            }
            return result;
          }}
        />
      )}
    </main>
  );
}
