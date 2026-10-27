// A resposta fica local até ser validada; a explicação só é revelada após conclusão.
import React, { useState } from "react";
export default function Challenge({ challenge, onAnswer, busy, index }) {
  const [answer, setAnswer] = useState(null),
    [error, setError] = useState("");
  async function submit(event) {
    event.preventDefault();
    setError("");
    const result = await onAnswer(challenge.id, answer);
    if (!result.ok) setError(result.error);
  }
  return (
    <article
      className={`challenge card ${challenge.completed ? "completed" : ""}`}
      aria-labelledby={`challenge-${challenge.id}`}
    >
      <div className="card-top">
        <span className="tag">{challenge.category}</span>
        <span className="points">+{challenge.points} pts</span>
      </div>
      <span className="challenge-number" aria-hidden="true">
        {String((index ?? 0) + 1).padStart(2, "0")}
      </span>
      <h3 id={`challenge-${challenge.id}`}>{challenge.title}</h3>
      {challenge.completed ? (
        <>
          <p className="done">✓ Desafio concluído</p>
          <p className="lesson">{challenge.explanation}</p>
          <span className="earned-label">
            {challenge.points} pontos conquistados
          </span>
        </>
      ) : (
        <form onSubmit={submit}>
          <fieldset disabled={busy}>
            <legend>{challenge.question}</legend>
            {challenge.options.map((option, i) => (
              <label
                className={`answer ${answer === i ? "selected" : ""}`}
                key={option}
              >
                <input
                  type="radio"
                  name={challenge.id}
                  value={i}
                  checked={answer === i}
                  onChange={() => {
                    setAnswer(i);
                    setError("");
                  }}
                  required
                />
                {option}
              </label>
            ))}
          </fieldset>
          {error && (
            <p className="error" role="alert">
              {error}
            </p>
          )}
          <button className="secondary full" disabled={answer === null || busy}>
            Validar resposta <span aria-hidden="true">↗</span>
          </button>
        </form>
      )}
    </article>
  );
}
