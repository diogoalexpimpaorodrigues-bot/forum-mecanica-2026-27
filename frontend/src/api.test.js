import { afterEach, expect, it, vi } from "vitest";
import { api } from "./api.js";
afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
  document.cookie = "csrftoken=; Max-Age=0";
});
it("envia o token CSRF e inclui cookies no POST", async () => {
  document.cookie = "csrftoken=seguro";
  const fetch = vi
    .fn()
    .mockResolvedValue({ ok: true, json: async () => ({ user: null }) });
  vi.stubGlobal("fetch", fetch);
  await api("logout", {});
  expect(fetch).toHaveBeenCalledWith(
    "/api/logout/",
    expect.objectContaining({
      method: "POST",
      credentials: "same-origin",
      body: "{}",
      headers: expect.objectContaining({ "X-CSRFToken": "seguro" }),
    }),
  );
});
it("consulta a sessão sem corpo de pedido", async () => {
  const fetch = vi
    .fn()
    .mockResolvedValue({ ok: true, json: async () => ({ user: null }) });
  vi.stubGlobal("fetch", fetch);
  await api("session");
  expect(fetch.mock.calls[0][1].method).toBe("GET");
  expect(fetch.mock.calls[0][1].body).toBeUndefined();
});
it("preserva o estado HTTP para reconhecer uma sessão expirada", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => ({ error: "Sessão expirada" }),
    }),
  );
  await expect(api("claim", {})).rejects.toMatchObject({
    status: 401,
    message: "Sessão expirada",
  });
});
it("apresenta uma mensagem útil quando recebe HTML em vez de JSON", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: false,
      status: 403,
      json: async () => {
        throw new Error("HTML");
      },
    }),
  );
  await expect(api("claim", {})).rejects.toThrow("Atualiza a página");
});

it("renova o CSRF uma única vez após uma rejeição explícita", async () => {
  const fetch = vi
    .fn()
    .mockResolvedValueOnce({
      ok: false,
      status: 403,
      json: async () => ({ error: "CSRF", code: "csrf_failed" }),
    })
    .mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ user: null }),
    })
    .mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ user: null }),
    });
  vi.stubGlobal("fetch", fetch);
  await api("logout", {});
  expect(fetch.mock.calls.map((call) => call[0])).toEqual([
    "/api/logout/",
    "/api/session/",
    "/api/logout/",
  ]);
});
it("não repete automaticamente uma operação após falha de rede", async () => {
  const fetch = vi.fn().mockRejectedValue(new TypeError("offline"));
  vi.stubGlobal("fetch", fetch);
  await expect(api("redeem", { id: "pack" })).rejects.toMatchObject({
    code: "network_error",
  });
  expect(fetch).toHaveBeenCalledTimes(1);
});
it("mantém os erros associados aos campos", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: false,
      status: 400,
      json: async () => ({
        error: "Revê os campos",
        code: "validation_failed",
        fields: { username: ["Já existe."] },
      }),
    }),
  );
  await expect(api("register", {})).rejects.toMatchObject({
    fields: { username: ["Já existe."] },
  });
});
it("aborta pedidos que excedem o tempo limite", async () => {
  vi.useFakeTimers();
  vi.stubGlobal(
    "fetch",
    vi.fn(
      (url, options) =>
        new Promise((resolve, reject) =>
          options.signal.addEventListener("abort", () =>
            reject(new DOMException("Aborted", "AbortError")),
          ),
        ),
    ),
  );
  const promise = expect(
    api("session", undefined, { timeout: 100 }),
  ).rejects.toMatchObject({ code: "timeout" });
  await vi.advanceTimersByTimeAsync(101);
  await promise;
  vi.useRealTimers();
});
it("distingue cancelamento externo de uma falha de ligação", async () => {
  const controller = new AbortController();
  vi.stubGlobal(
    "fetch",
    vi.fn(
      (url, options) =>
        new Promise((resolve, reject) =>
          options.signal.addEventListener("abort", () =>
            reject(new DOMException("Aborted", "AbortError")),
          ),
        ),
    ),
  );
  const promise = expect(
    api("session", undefined, { signal: controller.signal }),
  ).rejects.toMatchObject({ code: "aborted" });
  controller.abort();
  await promise;
});
it("rejeita respostas JSON sem um objeto", async () => {
  vi.stubGlobal(
    "fetch",
    vi
      .fn()
      .mockResolvedValue({ ok: true, status: 200, json: async () => null }),
  );
  await expect(api("session")).rejects.toMatchObject({
    code: "invalid_response",
  });
});

it("rejeita uma resposta de conta estruturalmente inválida", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        user: { username: "ana" },
        balance: -1,
        challenges: [],
        rewards: [],
        movements: [],
      }),
    }),
  );
  await expect(api("session")).rejects.toMatchObject({
    code: "invalid_response",
  });
});
it("não transforma um erro 403 genérico numa repetição de débito", async () => {
  const fetch = vi.fn().mockResolvedValue({
    ok: false,
    status: 403,
    json: async () => ({ error: "Sem acesso", code: "forbidden" }),
  });
  vi.stubGlobal("fetch", fetch);
  await expect(api("redeem", { id: "pack" })).rejects.toMatchObject({
    code: "forbidden",
  });
  expect(fetch).toHaveBeenCalledTimes(1);
});
