// Apresentamos o percurso antes de pedir dados. As âncoras apontam para secções
// reais da página e continuam úteis para quem navega apenas com o teclado.
// Desenvolvido com auxílio de IA; ver AI_USAGE.md.
import React from "react";
import Auth from "./Auth.jsx";
import forumLogo from "../assets/forum-logo.png";
import MechanismArt from "./MechanismArt.jsx";
const steps = [
  [
    "01",
    "Segue a curiosidade.",
    "Explora desafios de engenharia, sustentabilidade e tecnologia. Há sempre uma nova perspetiva para descobrir.",
    "EXPLORAR",
  ],
  [
    "02",
    "Dá valor ao que aprendes.",
    "Responde, descobre a explicação e ganha pontos por cada desafio concluído. O teu progresso fica guardado.",
    "CONQUISTAR",
  ],
  [
    "03",
    "Leva as ideias contigo.",
    "Troca os teus pontos por brindes do catálogo de demonstração e consulta cada conquista no teu histórico.",
    "RESGATAR",
  ],
];
export default function Landing({ onSuccess }) {
  return (
    <main className="landing" id="main-content" tabIndex={-1}>
      <section className="hero" aria-labelledby="hero-title">
        <div className="hero-content">
          <div className="pill">
            <span className="live-dot" /> PASSAPORTE FÓRUM · 2026/27
          </div>
          <h1 id="hero-title">
            A curiosidade
            <br />
            põe tudo em
            <br />
            <em>movimento.</em>
          </h1>
          <p className="hero-copy">
            Novas ideias. Pequenas descobertas. O teu espaço para explorar a
            engenharia e dar o próximo passo.
          </p>
          <div className="hero-actions">
            <a className="primary" href="#acesso">
              Começar o meu percurso <span aria-hidden="true">↗</span>
            </a>
            <a className="hero-link" href="#como-funciona">
              Como funciona <span aria-hidden="true">↓</span>
            </a>
          </div>
          <div className="hero-caption">
            <span aria-hidden="true">✳</span> ENGENHARIA. PESSOAS. FUTURO.
          </div>
        </div>
        <div className="hero-visual">
          <MechanismArt />
        </div>
        <div className="hero-rail">
          <span>FEITO DE CURIOSIDADE</span>
          <span>
            DESENHADO PARA DESCOBRIR <span aria-hidden="true">↗</span>
          </span>
          <span>Fórum Mecânica / 26—27</span>
        </div>
      </section>
      <section
        className="experience"
        id="experiencia"
        aria-labelledby="experience-title"
      >
        <div className="experience-heading">
          <div>
            <p className="eyebrow">A EXPERIÊNCIA PASSAPORTE</p>
            <h2 id="experience-title">
              Um pequeno passo.
              <br />
              <em>Novas perspetivas.</em>
            </h2>
          </div>
          <p>
            Aprender também é participar. Transforma a tua curiosidade num
            percurso de desafios, pontos e conquistas — ao teu ritmo.
          </p>
        </div>
        <div className="journey" id="como-funciona">
          {steps.map(([number, title, copy, label]) => (
            <article className="journey-step" key={number}>
              <div className="journey-top">
                <span>{number}</span>
                <span aria-hidden="true">↗</span>
              </div>
              <h3>{title}</h3>
              <p>{copy}</p>
              <span className="journey-label">{label}</span>
            </article>
          ))}
        </div>
      </section>
      <section
        className="access-section"
        id="acesso"
        aria-label="O teu passaporte e acesso à conta"
      >
        <div className="access-story">
          <p className="eyebrow">O PRÓXIMO PASSO É TEU</p>
          <h2>
            Há muito
            <br />
            por <em>descobrir.</em>
          </h2>
          <p>
            Cria o teu passaporte, guarda as tuas conquistas e regressa quando
            quiseres. Só precisas de um nome de utilizador e de uma
            palavra-passe.
          </p>
          <div className="passport-object" aria-hidden="true">
            <div className="passport-top">
              <span>Fórum Mecânica</span>
              <span>26/27 ↗</span>
            </div>
            <div className="passport-middle">
              <span>
                O teu
                <br />
                <em>passaporte.</em>
              </span>
              <span className="passport-mark">
                <img src={forumLogo} alt="" width="72" height="72" />
              </span>
            </div>
            <div className="passport-bottom">
              <span>EXPLORA · APRENDE · AVANÇA</span>
              <span className="barcode" />
            </div>
          </div>
          <div className="access-detail">
            <span aria-hidden="true">◈</span>
            <span>O teu ritmo. O teu percurso. As tuas conquistas.</span>
          </div>
        </div>
        <Auth onSuccess={onSuccess} />
      </section>
    </main>
  );
}
