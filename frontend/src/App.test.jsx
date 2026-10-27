// Testamos a interação visível, sem acoplar os testes à organização interna dos componentes.
import React from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import App from "./App.jsx";
import { api } from "./api.js";
vi.mock("./api.js", () => ({ api: vi.fn() }));
const state = {
  user: { username: "ana" },
  balance: 0,
  earned: 0,
  challenges: [
    {
      id: "energia",
      title: "Energia",
      category: "Engenharia",
      question: "Fonte renovável?",
      options: ["Carvão", "Vento"],
      points: 80,
      completed: false,
    },
  ],
  rewards: [
    {
      id: "pack",
      title: "Pack",
      description: "Autocolantes",
      icon: "✳",
      cost: 80,
      redeemed: false,
    },
  ],
  movements: [],
};
beforeEach(() => {
  vi.resetAllMocks();
  window.history.replaceState({}, "", "/");
});
describe("Passaporte", () => {
  it("apresenta o formulário inicial sem pedir email", async () => {
    api.mockResolvedValue({ user: null });
    render(<App />);
    expect(await screen.findByLabelText("Nome de utilizador")).toBeVisible();
    expect(screen.queryByLabelText(/email/i)).not.toBeInTheDocument();
  });
  it("regista e identifica a conta autenticada", async () => {
    const u = userEvent.setup();
    api.mockResolvedValueOnce({ user: null }).mockResolvedValueOnce(state);
    render(<App />);
    await u.click(await screen.findByRole("button", { name: "Criar conta" }));
    await u.type(screen.getByLabelText("Nome de utilizador"), "ana");
    await u.type(screen.getByLabelText("Palavra-passe"), "Segura!123456");
    await u.type(
      screen.getByLabelText("Confirmar palavra-passe"),
      "Segura!123456",
    );
    await u.click(
      screen.getByRole("button", { name: /Criar conta e começar/ }),
    );
    expect(await screen.findByText("Olá,")).toBeVisible();
    expect(api).toHaveBeenLastCalledWith("register", {
      username: "ana",
      password: "Segura!123456",
      confirmation: "Segura!123456",
    });
    expect(window.location.pathname).toBe("/dashboard");
  });
  it("mostra erros de login", async () => {
    const u = userEvent.setup();
    api
      .mockResolvedValueOnce({ user: null })
      .mockRejectedValueOnce(new Error("Credenciais incorretas"));
    render(<App />);
    await u.type(await screen.findByLabelText("Nome de utilizador"), "ana");
    await u.type(screen.getByLabelText("Palavra-passe"), "errada");
    await u.click(screen.getByRole("button", { name: /Entrar no meu/ }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Credenciais incorretas",
    );
  });
  it("exige escolher uma resposta antes de validar", async () => {
    api.mockResolvedValue(state);
    const u = userEvent.setup();
    render(<App />);
    const button = await screen.findByRole("button", {
      name: /Validar resposta/,
    });
    expect(button).toBeDisabled();
    await u.click(screen.getByLabelText("Vento"));
    await u.click(button);
    await waitFor(() =>
      expect(api).toHaveBeenLastCalledWith("claim", {
        id: "energia",
        answer: 1,
        expected_user: "ana",
      }),
    );
  });
  it("mostra o histórico vazio e permite voltar aos desafios", async () => {
    api.mockResolvedValue(state);
    const u = userEvent.setup();
    render(<App />);
    await u.click(await screen.findByRole("button", { name: /Histórico/ }));
    expect(
      screen.getByText("A primeira conquista está à tua espera."),
    ).toBeVisible();
    await u.click(screen.getByRole("button", { name: "Ver desafios" }));
    expect(screen.getByText("Fonte renovável?")).toBeVisible();
  });
  it("termina a sessão e regressa à entrada", async () => {
    api.mockResolvedValueOnce(state).mockResolvedValueOnce({ user: null });
    const u = userEvent.setup();
    render(<App />);
    await u.click(await screen.findByRole("button", { name: /Sair/ }));
    expect(await screen.findByLabelText("Nome de utilizador")).toBeVisible();
    expect(api).toHaveBeenLastCalledWith("logout", {});
  });
  it("permite recuperar de uma falha de ligação", async () => {
    api
      .mockRejectedValueOnce(new Error("offline"))
      .mockResolvedValueOnce({ user: null });
    const u = userEvent.setup();
    render(<App />);
    await u.click(
      await screen.findByRole("button", { name: "Voltar a ligar" }),
    );
    expect(await screen.findByLabelText("Nome de utilizador")).toBeVisible();
  });
});
