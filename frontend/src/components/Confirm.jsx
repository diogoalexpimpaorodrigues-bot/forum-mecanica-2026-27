// O dialog mantém foco e mensagens dentro da confirmação, mesmo se a rede falhar.
// Desenvolvido com auxílio de IA; ver AI_USAGE.md.
import React, { useLayoutEffect, useRef, useState } from "react";
export default function Confirm({ reward, balance, onClose, onConfirm, busy }) {
  const dialog = useRef(null),
    [error, setError] = useState("");
  useLayoutEffect(() => {
    const element = dialog.current,
      opener = document.activeElement;
    element.showModal();
    return () => {
      element.close();
      if (opener?.isConnected && !opener.disabled) opener.focus();
    };
  }, []);
  async function confirm() {
    setError("");
    const result = await onConfirm();
    if (!result?.ok)
      setError(result?.error || "Não foi possível concluir o resgate.");
  }
  return (
    <dialog
      ref={dialog}
      className="modal"
      aria-labelledby="resgate-title"
      aria-describedby="resgate-description"
      onCancel={(event) => {
        event.preventDefault();
        if (!busy) onClose();
      }}
    >
      <p className="eyebrow">A TUA PRÓXIMA CONQUISTA</p>
      <h2 id="resgate-title">Confirmar resgate?</h2>
      <p id="resgate-description">
        Vais trocar <strong>{reward.cost} pontos</strong> por{" "}
        <strong>{reward.title}</strong>.
      </p>
      <dl className="redemption-summary">
        <div>
          <dt>Saldo atual</dt>
          <dd>{balance} pts</dd>
        </div>
        <div>
          <dt>Custo do brinde</dt>
          <dd>−{reward.cost} pts</dd>
        </div>
        <div>
          <dt>Saldo após resgate</dt>
          <dd>{Math.max(0, balance - reward.cost)} pts</dd>
        </div>
      </dl>
      <p className="muted">
        A troca é definitiva nesta demonstração. O código fica no histórico; o
        brinde é ilustrativo e não tem entrega física.
      </p>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      <div className="modal-actions">
        <button className="secondary" onClick={onClose} disabled={busy}>
          Cancelar
        </button>
        <button
          className="primary"
          onClick={confirm}
          disabled={busy || balance < reward.cost}
        >
          {busy ? "A confirmar…" : "Confirmar resgate"}
        </button>
      </div>
    </dialog>
  );
}
