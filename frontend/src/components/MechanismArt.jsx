// Uma vista explodida, desenhada em SVG, liga a identidade à engenharia mecânica.
// A geometria é original e decorativa; não representa uma peça para fabrico.
// Desenvolvido com auxílio de IA; ver AI_USAGE.md.
import React, { useId } from "react";

function ring(outer, inner) {
  return `M ${outer} 0 a ${outer} ${outer} 0 1 0 ${-2 * outer} 0 a ${outer} ${outer} 0 1 0 ${2 * outer} 0 M ${inner} 0 a ${inner} ${inner} 0 1 0 ${-2 * inner} 0 a ${inner} ${inner} 0 1 0 ${2 * inner} 0`;
}
export default function MechanismArt() {
  // Cada instância recebe os seus gradientes, mesmo quando coexistem na página.
  const id = useId().replaceAll(":", "");
  const holes = Array.from({ length: 12 }, (_, i) => {
    const angle = (i * Math.PI) / 6;
    return [Math.cos(angle) * 156, Math.sin(angle) * 156];
  });
  const teeth = Array.from({ length: 96 }, (_, i) => {
    const angle = (i * Math.PI * 2) / 96;
    const radius = i % 4 === 0 || i % 4 === 3 ? 207 : 222;
    return `${Math.cos(angle) * radius},${Math.sin(angle) * radius}`;
  }).join(" ");
  return (
    <svg
      className="mechanism-art"
      viewBox="0 0 620 580"
      aria-hidden="true"
      focusable="false"
    >
      <defs>
        <linearGradient id={`${id}-metal`} x1="0" y1="0" x2="1" y2="1">
          <stop stopColor="#e1f4fc" />
          <stop offset=".28" stopColor="#a0c9e0" />
          <stop offset=".65" stopColor="#4d88ad" />
          <stop offset="1" stopColor="#b6d9ec" />
        </linearGradient>
        <linearGradient id={`${id}-accent`} x1="0" y1="0" x2="1" y2="1">
          <stop stopColor="#c3f0ff" />
          <stop offset=".45" stopColor="#6ad6f9" />
          <stop offset="1" stopColor="#378fc0" />
        </linearGradient>
        <linearGradient id={`${id}-edge`} x1="0" y1="0" x2="0" y2="1">
          <stop stopColor="#698497" />
          <stop offset="1" stopColor="#213d52" />
        </linearGradient>
        <radialGradient id={`${id}-glow`}>
          <stop stopColor="#a5c2d7" stopOpacity=".17" />
          <stop offset="1" stopColor="#a5c2d7" stopOpacity="0" />
        </radialGradient>
      </defs>
      <circle cx="310" cy="296" r="280" fill={`url(#${id}-glow)`} />
      <g fill="none" stroke="#758d9f" strokeWidth=".7" opacity=".35">
        <circle cx="310" cy="290" r="248" />
        <circle cx="310" cy="290" r="222" strokeDasharray="2 9" />
        <path d="M310 15v550M32 290h556M114 94l392 392M114 486 506 94" />
        <path d="M40 50h24m-12-12v24M556 516h24m-12-12v24" />
      </g>
      <ellipse
        cx="325"
        cy="458"
        rx="186"
        ry="37"
        fill="#091b28"
        opacity=".45"
      />
      <g transform="translate(314 397) rotate(-24) scale(1 .52)">
        <path
          d={ring(205, 101)}
          transform="translate(0 16)"
          fill="#254358"
          fillRule="evenodd"
        />
        <path
          d={ring(205, 101)}
          fill={`url(#${id}-edge)`}
          stroke="#7991a2"
          fillRule="evenodd"
        />
        <circle r="190" fill="none" stroke="#899ead" strokeWidth="1" />
        <circle r="114" fill="none" stroke="#899ead" strokeWidth="1" />
      </g>
      <g stroke="#a3c1d6" strokeWidth="1" opacity=".45" strokeDasharray="4 6">
        <path d="M166 244v140M454 114v139M228 269v108M398 190v179" />
      </g>
      <g transform="translate(310 297) rotate(-24) scale(1 .62)">
        <polygon points={teeth} transform="translate(0 17)" fill="#5e94ba" />
        <polygon
          points={teeth}
          fill={`url(#${id}-accent)`}
          stroke="#ddedf9"
          strokeWidth="1"
        />
        <circle r="91" fill="#1b394f" />
        <circle r="99" fill="none" stroke="#a8cfeb" strokeWidth="8" />
        <circle r="182" fill="none" stroke="#93bedc" strokeWidth="1" />
        <circle r="145" fill="none" stroke="#e0effa" strokeWidth="1" />
        {holes
          .filter((_, i) => i % 2 === 0)
          .map(([x, y], i) => (
            <g key={i}>
              <circle cx={x} cy={y} r="12" fill="#679abe" />
              <circle cx={x} cy={y - 2} r="9" fill="#1a374c" />
            </g>
          ))}
      </g>
      <g transform="translate(310 183) rotate(-24) scale(1 .62)">
        <path
          d={ring(197, 105)}
          transform="translate(0 18)"
          fill="#617a8b"
          fillRule="evenodd"
        />
        <path
          d={ring(197, 105)}
          fill={`url(#${id}-metal)`}
          stroke="#e0edf7"
          fillRule="evenodd"
        />
        <circle r="184" fill="none" stroke="#e4f0f8" strokeWidth="1" />
        <circle r="118" fill="none" stroke="#70899c" strokeWidth="1" />
        {holes.map(([x, y], i) => (
          <g key={i}>
            <circle cx={x} cy={y} r="10" fill="#556b7a" />
            <circle cx={x} cy={y - 2} r="7" fill="#1a364b" />
            <path
              d={`M${x - 3} ${y - 2}h6`}
              stroke="#9eb5c5"
              strokeWidth="1.5"
            />
          </g>
        ))}
      </g>
      <g fill="none" stroke="#acc4d6" strokeWidth="1">
        <path d="m416 106 61-50h67M127 332l-57 38H25M428 396l57 51h81" />
        <circle cx="416" cy="106" r="3" fill="#83dcfa" />
        <circle cx="127" cy="332" r="3" fill="#83dcfa" />
        <circle cx="428" cy="396" r="3" fill="#83dcfa" />
      </g>
      <g fill="#bdcdd8" fontFamily="monospace" fontSize="9" letterSpacing="1.5">
        <text x="481" y="44">
          01 / EXPLORAR
        </text>
        <text x="25" y="389">
          02 / APRENDER
        </text>
        <text x="483" y="466">
          03 / AVANÇAR
        </text>
        <text x="40" y="546">
          FM — VISTA EXPLODIDA
        </text>
        <text x="508" y="546">
          26 / 27
        </text>
      </g>
    </svg>
  );
}
