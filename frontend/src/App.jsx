/* Desenvolvido com auxílio de IA; ver AI_USAGE.md. A sessão e a reconciliação
   vivem no hook, para que os componentes se concentrem na experiência de uso. */
import React from "react";
import usePassport from "./hooks/usePassport.js";
import Brand from "./components/Brand.jsx";
import forumLogo from "./assets/forum-logo.png";
import Landing from "./components/Landing.jsx";
import Dashboard from "./components/Dashboard.jsx";
export default function App() {
  const {
    data,
    loading,
    busy,
    notice,
    setNotice,
    refresh,
    reload,
    success,
    act,
  } = usePassport();
  function authenticated(value) {
    success(value);
    requestAnimationFrame(() => document.getElementById("greeting")?.focus());
  }
  return (
    <>
      <a className="skip-link" href="#main-content">
        Saltar para o conteúdo
      </a>
      <header
        className={`site-header ${data?.user ? "is-authenticated" : "is-public"}`}
      >
        <Brand />
        <div className="header-right">
          {!data?.user && (
            <nav className="public-nav" aria-label="Navegação principal">
              <a href="#experiencia">A experiência</a>
              <a href="#como-funciona">Como funciona</a>
              <a className="header-cta" href="#acesso">
                O meu passaporte <span aria-hidden="true">↗</span>
              </a>
            </nav>
          )}
          {data?.user && (
            <span className="header-label">O TEU ESPAÇO FÓRUM</span>
          )}
          {data?.user && (
            <>
              <span className="user-badge">
                <span aria-hidden="true">
                  {data.user.username.slice(0, 1).toUpperCase()}
                </span>
                <span className="user-name">{data.user.username}</span>
              </span>
              <button
                className="logout"
                disabled={busy}
                onClick={() => act("logout", {})}
              >
                Sair <span aria-hidden="true">↗</span>
              </button>
            </>
          )}
        </div>
      </header>
      {notice && (
        <div
          className={`notice ${notice.error ? "error" : ""}`}
          role={notice.error ? "alert" : "status"}
        >
          <span>{notice.text}</span>
          <button aria-label="Fechar mensagem" onClick={() => setNotice(null)}>
            ×
          </button>
        </div>
      )}
      {loading ? (
        <main className="loading" id="main-content" role="status">
          <span className="loading-mark" aria-hidden="true">
            ✳
          </span>
          A preparar o teu passaporte…
        </main>
      ) : data?.user ? (
        <Dashboard
          key={data.user.username}
          data={data}
          act={act}
          busy={busy}
          refresh={refresh}
        />
      ) : data ? (
        <Landing onSuccess={authenticated} />
      ) : (
        <main className="empty" id="main-content">
          <h1>Vamos tentar novamente?</h1>
          <p>
            Não foi possível contactar o servidor. O teu progresso continua
            guardado.
          </p>
          <button className="primary" onClick={reload}>
            Voltar a ligar
          </button>
        </main>
      )}
      <footer className="site-footer">
        <div className="footer-top">
          <div>
            <span className="footer-wordmark">
              Ideias em <em>movimento.</em> <span aria-hidden="true">↗</span>
            </span>
            <p>Um espaço para a curiosidade e para o que vem a seguir.</p>
          </div>
          <div className="footer-brand">
            <img
              src={forumLogo}
              alt="Logótipo do Fórum Mecânica"
              width="54"
              height="54"
            />
            <span className="footer-edition">
              PASSAPORTE FÓRUM
              <br />
              <strong>2026 / 27</strong>
            </span>
          </div>
        </div>
        <div className="footer-bottom">
          <span>© 2026 Fórum Mecânica · Projeto de recrutamento</span>
          <span>Feito para aprender. Construído com auxílio de IA.</span>
        </div>
      </footer>
    </>
  );
}
