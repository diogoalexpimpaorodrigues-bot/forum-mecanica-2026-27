import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, expect, it, vi } from "vitest";
import usePassport from "./usePassport.js";
import { api } from "../api.js";
vi.mock("../api.js", () => ({ api: vi.fn() }));
const state = {
  user: { username: "ana" },
  revision: 0,
  balance: 0,
  earned: 0,
  spent: 0,
  challenges: [{ id: "energia", completed: false }],
  rewards: [{ id: "pack", redeemed: false }],
  movements: [],
};
beforeEach(() => {
  vi.resetAllMocks();
});
it("reconcilia um crédito cuja resposta se perdeu sem o repetir", async () => {
  api
    .mockResolvedValueOnce(state)
    .mockRejectedValueOnce(
      Object.assign(new Error("rede"), { code: "network_error" }),
    )
    .mockResolvedValueOnce({
      ...state,
      revision: 1,
      balance: 80,
      challenges: [{ id: "energia", completed: true }],
    });
  const { result } = renderHook(() => usePassport());
  await waitFor(() => expect(result.current.loading).toBe(false));
  let response;
  await act(async () => {
    response = await result.current.act("claim", { id: "energia", answer: 1 });
  });
  expect(response.ok).toBe(true);
  expect(result.current.data.balance).toBe(80);
  expect(api.mock.calls.filter((c) => c[0] === "claim")).toHaveLength(1);
});
it("não aceita uma fotografia com revisão mais antiga", async () => {
  api
    .mockResolvedValueOnce({ ...state, revision: 2, balance: 100 })
    .mockResolvedValueOnce({ ...state, revision: 1, balance: 80 });
  const { result } = renderHook(() => usePassport());
  await waitFor(() => expect(result.current.loading).toBe(false));
  await act(() => result.current.refresh());
  expect(result.current.data.balance).toBe(100);
});
it("bloqueia dois pedidos iniciados no mesmo instante", async () => {
  let complete;
  api.mockResolvedValueOnce(state).mockImplementationOnce(
    () =>
      new Promise((resolve) => {
        complete = resolve;
      }),
  );
  const { result } = renderHook(() => usePassport());
  await waitFor(() => expect(result.current.loading).toBe(false));
  let first, second;
  act(() => {
    first = result.current.act("claim", { id: "energia", answer: 1 });
    second = result.current.act("claim", { id: "energia", answer: 1 });
  });
  expect(await second).toMatchObject({ ok: false });
  await act(async () => {
    complete({ ...state, revision: 1 });
    await first;
  });
  expect(api.mock.calls.filter((c) => c[0] === "claim")).toHaveLength(1);
});
it("limpa os dados quando a sessão expira durante uma operação", async () => {
  api.mockResolvedValueOnce(state).mockRejectedValueOnce(
    Object.assign(new Error("Sessão terminada"), {
      status: 401,
      code: "unauthenticated",
    }),
  );
  const { result } = renderHook(() => usePassport());
  await waitFor(() => expect(result.current.loading).toBe(false));
  await act(() => result.current.act("claim", { id: "energia", answer: 1 }));
  expect(result.current.data.user).toBeNull();
});
it("não declara sucesso quando a reconciliação falha", async () => {
  api
    .mockResolvedValueOnce(state)
    .mockRejectedValueOnce(
      Object.assign(new Error("Sem ligação"), { code: "network_error" }),
    )
    .mockRejectedValueOnce(new Error("offline"));
  const { result } = renderHook(() => usePassport());
  await waitFor(() => expect(result.current.loading).toBe(false));
  let response;
  await act(async () => {
    response = await result.current.act("redeem", { id: "pack" });
  });
  expect(response).toMatchObject({ ok: false, error: "Sem ligação" });
  expect(result.current.data.balance).toBe(0);
});

it("ignora uma leitura anterior que chega depois de um crédito", async () => {
  let oldResponse;
  api
    .mockResolvedValueOnce(state)
    .mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          oldResponse = resolve;
        }),
    )
    .mockResolvedValueOnce({
      ...state,
      balance: 80,
      revision: 1,
      challenges: [{ id: "energia", completed: true }],
    });
  const { result } = renderHook(() => usePassport());
  await waitFor(() => expect(result.current.loading).toBe(false));
  let reading;
  act(() => {
    reading = result.current.refresh();
  });
  await act(() => result.current.act("claim", { id: "energia", answer: 1 }));
  await act(async () => {
    oldResponse(state);
    await reading;
  });
  expect(result.current.data.balance).toBe(80);
});
it("atualiza a identificação quando outra conta aparece num refresh", async () => {
  api
    .mockResolvedValueOnce(state)
    .mockResolvedValueOnce({ ...state, user: { username: "beatriz" } });
  const { result } = renderHook(() => usePassport());
  await waitFor(() => expect(result.current.loading).toBe(false));
  await act(() => result.current.refresh());
  expect(result.current.data.user.username).toBe("beatriz");
  expect(result.current.notice.text).toContain("noutro separador");
});
