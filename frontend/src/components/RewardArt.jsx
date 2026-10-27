// Brindes ilustrativos, com o logótipo fornecido aplicado sem alterar a imagem.
// Os desenhos dos objetos foram criados com auxílio de IA; ver AI_USAGE.md.
import React from "react";
import forumLogo from "../assets/forum-logo.png";
export default function RewardArt({ id }) {
  return (
    <svg
      className="reward-illustration"
      viewBox="0 0 280 180"
      aria-hidden="true"
      focusable="false"
    >
      <ellipse cx="140" cy="155" rx="68" ry="9" fill="#d4dfe6" />
      {id === "autocolantes" ? (
        <g transform="rotate(-8 140 90)">
          <rect
            x="78"
            y="20"
            width="124"
            height="135"
            rx="10"
            fill="#fffdf5"
            stroke="#c4d2dc"
          />
          <rect
            x="90"
            y="35"
            width="50"
            height="50"
            rx="7"
            fill="#fff"
            stroke="#c4d2dc"
          />
          <image href={forumLogo} x="94" y="39" width="42" height="42" />
          <rect x="145" y="42" width="39" height="43" rx="8" fill="#25475f" />
          <path
            d="m156 64 7 7 12-19"
            stroke="#83dcfa"
            strokeWidth="3"
            fill="none"
          />
          <rect x="93" y="96" width="91" height="36" rx="18" fill="#e5ecf1" />
          <text
            x="138"
            y="119"
            textAnchor="middle"
            fill="#25475f"
            fontSize="14"
            fontWeight="700"
          >
            IDEIAS ↗
          </text>
        </g>
      ) : id === "caderno" ? (
        <g transform="rotate(10 140 90)">
          <rect x="88" y="23" width="112" height="135" rx="8" fill="#ced7de" />
          <rect x="82" y="17" width="112" height="135" rx="8" fill="#38566c" />
          <path d="M98 17v135" stroke="#2a465a" strokeWidth="3" />
          <path d="M175 17v135" stroke="#b8d7ee" strokeWidth="6" />
          <path d="M120 54h33m-33 8h24" stroke="#b8d7ee" strokeWidth="2" />
          <rect x="116" y="85" width="38" height="38" rx="6" fill="#fff" />
          <image href={forumLogo} x="119" y="88" width="32" height="32" />
          <path d="m151 152 0 15 6-5 6 5V152" fill="#a7cae3" />
        </g>
      ) : (
        <g>
          <rect x="119" y="16" width="42" height="21" rx="6" fill="#243a4a" />
          <path
            d="M117 37h46v12c0 9 14 13 14 29v60c0 11-8 17-17 17h-40c-9 0-17-6-17-17V78c0-16 14-20 14-29Z"
            fill="#a5c7df"
          />
          <path
            d="M117 68v64c0 6 2 9 6 10"
            stroke="#d7e8f4"
            strokeWidth="6"
            strokeLinecap="round"
            fill="none"
          />
          <path d="M126 23h28" stroke="#6b8598" strokeWidth="2" />
          <rect x="121" y="85" width="38" height="38" rx="6" fill="#fff" />
          <image href={forumLogo} x="124" y="88" width="32" height="32" />
        </g>
      )}
    </svg>
  );
}
