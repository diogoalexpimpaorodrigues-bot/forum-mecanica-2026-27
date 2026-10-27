// A validação imediata ajuda a corrigir os campos; a decisão final é sempre do Django.
// Desenvolvido com auxílio de IA; ver AI_USAGE.md.
import React, { useRef, useState } from "react";
import { api } from "../api.js";

export default function Auth({ onSuccess }) {
  const [register, setRegister] = useState(false),
    [busy, setBusy] = useState(false);
  const [error, setError] = useState(""),
    [fields, setFields] = useState({}),
    [visible, setVisible] = useState(false);
  const form = useRef(null),
    lock = useRef(false);
  function changeMode(next) {
    setRegister(next);
    setError("");
    setFields({});
    setVisible(false);
  }
  function showErrors(message, errors = {}) {
    setError(message);
    setFields(errors);
    // Esperamos pela atualização dos atributos aria-invalid antes de devolver o foco.
    requestAnimationFrame(() =>
      form.current?.querySelector('[aria-invalid="true"]')?.focus(),
    );
  }
  async function submit(event) {
    event.preventDefault();
    if (lock.current) return;
    const data = Object.fromEntries(new FormData(event.currentTarget));
    const errors = {};
    if (!data.username.trim().normalize("NFKC"))
      errors.username = ["Indica o teu nome de utilizador."];
    else if (register && data.username.trim().normalize("NFKC").length < 3)
      errors.username = ["Usa pelo menos 3 caracteres."];
    if (!data.password.trim()) errors.password = ["Indica a palavra-passe."];
    else if (register && data.password.length < 10)
      errors.password = ["Usa pelo menos 10 caracteres."];
    if (register && data.confirmation !== data.password)
      errors.confirmation = ["As palavras-passe não coincidem."];
    if (Object.keys(errors).length) {
      showErrors("Revê os campos assinalados.", errors);
      return;
    }
    lock.current = true;
    setBusy(true);
    setError("");
    setFields({});
    try {
      onSuccess(await api(register ? "register" : "login", data));
    } catch (e) {
      if (["network_error", "timeout", "invalid_response"].includes(e.code)) {
        try {
          const session = await api("session");
          if (
            session.user?.username === data.username.trim().normalize("NFKC")
          ) {
            onSuccess(session);
            return;
          }
        } catch {
          /* O erro original continua a ser o mais útil. */
        }
      }
      showErrors(e.message, e.fields);
    } finally {
      lock.current = false;
      setBusy(false);
    }
  }
  const errorFor = (name) =>
    fields[name]?.length ? (
      <p className="field-error" id={`${name}-error`}>
        {fields[name].join(" ")}
      </p>
    ) : null;
  return (
    <section className="auth-card" aria-labelledby="auth-title">
      <div className="tabs" aria-label="Acesso à conta">
        <button
          aria-pressed={!register}
          disabled={busy}
          onClick={() => changeMode(false)}
        >
          Entrar
        </button>
        <button
          aria-pressed={register}
          disabled={busy}
          onClick={() => changeMode(true)}
        >
          Criar conta
        </button>
      </div>
      <p className="eyebrow">O TEU PONTO DE PARTIDA</p>
      <h2 id="auth-title" tabIndex={-1}>
        {register ? "Faz parte do movimento." : "Bom ter-te por cá."}
      </h2>
      <p className="muted">
        {register
          ? "Um nome, uma palavra-passe e muitas ideias pela frente."
          : "Entra para continuar o teu percurso."}
      </p>
      <form
        ref={form}
        onSubmit={submit}
        key={String(register)}
        noValidate
        aria-busy={busy}
      >
        <label htmlFor="username">Nome de utilizador</label>
        <input
          id="username"
          name="username"
          autoComplete="username"
          autoCapitalize="none"
          spellCheck="false"
          required
          minLength={register ? 3 : 1}
          maxLength={30}
          placeholder="O teu nome no Fórum"
          readOnly={busy}
          aria-invalid={!!fields.username}
          aria-describedby={
            fields.username
              ? "username-error"
              : register
                ? "username-help"
                : undefined
          }
        />
        {errorFor("username")}
        {register && (
          <small id="username-help">
            3 a 30 caracteres. As maiúsculas e minúsculas são diferentes.
          </small>
        )}
        <label htmlFor="password">Palavra-passe</label>
        <div className="password-field">
          <input
            id="password"
            name="password"
            type={visible ? "text" : "password"}
            autoComplete={register ? "new-password" : "current-password"}
            required
            maxLength={128}
            readOnly={busy}
            aria-invalid={!!fields.password}
            aria-describedby={
              [
                register ? "password-help" : "",
                fields.password ? "password-error" : "",
              ]
                .filter(Boolean)
                .join(" ") || undefined
            }
          />
          <button
            type="button"
            className="password-toggle"
            onClick={() => setVisible(!visible)}
            aria-label={
              visible ? "Ocultar palavra-passe" : "Mostrar palavra-passe"
            }
            aria-pressed={visible}
          >
            {visible ? "Ocultar" : "Mostrar"}
          </button>
        </div>
        {errorFor("password")}
        {register && (
          <>
            <small id="password-help">
              Pelo menos 10 caracteres. Evita palavras-passe comuns ou apenas
              números.
            </small>
            <label htmlFor="confirmation">Confirmar palavra-passe</label>
            <input
              id="confirmation"
              name="confirmation"
              type={visible ? "text" : "password"}
              autoComplete="new-password"
              required
              maxLength={128}
              readOnly={busy}
              aria-invalid={!!fields.confirmation}
              aria-describedby={
                fields.confirmation ? "confirmation-error" : undefined
              }
            />
            {errorFor("confirmation")}
          </>
        )}
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
        <button className="primary full" disabled={busy}>
          {busy
            ? "A processar…"
            : register
              ? "Criar conta e começar →"
              : "Entrar no meu passaporte →"}
        </button>
      </form>
      <div className="privacy">
        <span aria-hidden="true">◈</span>
        <span>Sem email. O teu progresso fica guardado na tua conta.</span>
      </div>
    </section>
  );
}
