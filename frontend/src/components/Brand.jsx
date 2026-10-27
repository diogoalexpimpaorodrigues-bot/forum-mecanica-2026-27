// O símbolo é o ficheiro fornecido pelo utilizador, mantido sem alterações.
// O texto ao lado é composição da interface. Auxílio de IA: ver AI_USAGE.md.
import React from "react";
import forumLogo from "../assets/forum-logo.png";
export default function Brand() {
  return (
    <a className="brand" href="/" aria-label="Fórum Mecânica, início">
      <img
        className="brand-icon"
        src={forumLogo}
        alt="Logótipo do Fórum Mecânica"
        width="56"
        height="56"
      />
      <span>
        Fórum <span className="brand-second">Mecânica</span>
      </span>
    </a>
  );
}
