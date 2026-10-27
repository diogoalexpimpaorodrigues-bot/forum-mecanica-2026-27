// Coordena pedidos e sincroniza separadores sem guardar dados privados no browser.
// Desenvolvido com auxílio de IA; ver AI_USAGE.md.
import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api.js";

export default function usePassport() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState(null);
  const active = useRef(false),
    generation = useRef(0),
    channel = useRef(null),
    mounted = useRef(true);
  const current = useRef(null);
  const queuedRefresh = useRef(false);

  const accept = useCallback((value) => {
    const previous = current.current;
    // Uma resposta antiga nunca faz o saldo andar para trás na mesma conta.
    if (
      previous?.user?.username === value.user?.username &&
      (previous?.revision ?? -1) > (value.revision ?? -1)
    )
      return;
    current.current = value;
    if (mounted.current) setData(value);
  }, []);

  const refresh = useCallback(
    async ({ initial = false, signal, announce = false } = {}) => {
      if (active.current) {
        queuedRefresh.current = true;
        return;
      }
      const ticket = ++generation.current;

      try {
        const value = await api("session", undefined, { signal });
        if (!mounted.current || ticket !== generation.current) return;
        const previous = current.current;
        accept(value);
        if (previous?.user && previous.user.username !== value.user?.username)
          setNotice({
            error: true,
            text: "A sessão mudou noutro separador. Confirma a conta antes de continuar.",
          });
        else if (announce)
          setNotice({ text: "Os teus dados estão atualizados." });
        else if (initial) setNotice(null);
        if (value.user && location.pathname !== "/dashboard")
          window.history.replaceState({}, "", "/dashboard");
        if (!value.user && location.pathname === "/dashboard")
          window.history.replaceState({}, "", "/");
      } catch (error) {
        if (
          mounted.current &&
          ticket === generation.current &&
          error.code !== "aborted"
        )
          setNotice({
            error: true,
            text: "Não foi possível atualizar os dados. Verifica a ligação e volta a tentar.",
          });
      } finally {
        if (mounted.current && ticket === generation.current) setLoading(false);
      }
    },
    [accept],
  );

  const invalidate = useCallback(() => {
    generation.current += 1;
  }, []);

  useEffect(() => {
    mounted.current = true;
    const controller = new AbortController();
    // A microtarefa deixa o cleanup do StrictMode cancelar uma montagem descartada.
    queueMicrotask(() => {
      if (!controller.signal.aborted)
        refresh({ initial: true, signal: controller.signal });
    });
    const focus = () => {
      if (document.visibilityState !== "hidden") refresh();
    };
    window.addEventListener("focus", focus);
    window.addEventListener("online", focus);
    window.addEventListener("pageshow", focus);
    document.addEventListener("visibilitychange", focus);
    if (typeof BroadcastChannel !== "undefined") {
      channel.current = new BroadcastChannel("forum-session");
      channel.current.onmessage = () => refresh();
    }
    return () => {
      mounted.current = false;
      controller.abort();
      invalidate();
      window.removeEventListener("focus", focus);
      window.removeEventListener("online", focus);
      window.removeEventListener("pageshow", focus);
      document.removeEventListener("visibilitychange", focus);
      channel.current?.close();
    };
  }, [refresh, invalidate]);

  function success(value) {
    generation.current++;
    accept(value);
    setNotice(null);
    window.history.replaceState({}, "", value.user ? "/dashboard" : "/");
    channel.current?.postMessage("changed");
  }

  async function act(path, payload) {
    if (active.current)
      return { ok: false, error: "Já está uma operação em curso." };
    active.current = true;
    generation.current++;
    setBusy(true);
    setNotice(null);
    const username = current.current?.user?.username;
    try {
      const value = await api(path, {
        ...payload,
        ...(path === "logout" ? {} : { expected_user: username }),
      });
      accept(value);
      if (value.message) setNotice({ text: value.message });
      if (!value.user) window.history.replaceState({}, "", "/");
      channel.current?.postMessage("changed");
      return { ok: true, data: value };
    } catch (error) {
      if (error.code === "unauthenticated" || error.status === 401) {
        accept({ user: null });
        window.history.replaceState({}, "", "/");
      }
      // Após uma resposta perdida ou um conflito, lemos o estado real. Não enviamos
      // uma segunda operação: a primeira pode já ter sido confirmada no servidor.
      if (
        [
          "network_error",
          "timeout",
          "invalid_response",
          "already_completed",
          "already_redeemed",
          "insufficient_balance",
          "account_changed",
          "service_busy",
        ].includes(error.code)
      ) {
        try {
          const latest = await api("session");
          accept(latest);
          const sameUser = latest.user?.username === username;
          const confirmed =
            (path === "logout" && !latest.user) ||
            (sameUser &&
              (path === "claim"
                ? latest.challenges?.some(
                    (c) => c.id === payload.id && c.completed,
                  )
                : path === "redeem"
                  ? latest.rewards?.some(
                      (r) => r.id === payload.id && r.redeemed,
                    )
                  : false));
          if (confirmed) {
            setNotice({
              text: "O estado foi confirmado no servidor. A operação ficou registada uma única vez.",
            });
            channel.current?.postMessage("changed");
            return { ok: true, data: latest };
          }
        } catch {
          /* Mantemos a última fotografia e deixamos claro que não foi atualizada. */
        }
      }
      const text =
        error.message || "Não foi possível concluir. Tenta novamente.";
      if (
        path === "logout" ||
        error.status === 401 ||
        error.code === "account_changed"
      )
        setNotice({ error: true, text });
      return { ok: false, error: text };
    } finally {
      active.current = false;
      if (mounted.current) {
        setBusy(false);
        if (queuedRefresh.current) {
          queuedRefresh.current = false;
          refresh();
        }
      }
    }
  }
  function reload() {
    setLoading(true);
    return refresh({ initial: true });
  }
  return {
    data,
    loading,
    busy,
    notice,
    setNotice,
    refresh,
    reload,
    success,
    act,
  };
}
