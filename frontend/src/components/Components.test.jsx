import React from "react";
import { beforeEach, expect, it, vi } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Auth from "./Auth.jsx";
import Confirm from "./Confirm.jsx";
import History from "./History.jsx";
import Challenge from "./Challenge.jsx";
import { api } from "../api.js";
vi.mock("../api.js", () => ({ api: vi.fn() }));
beforeEach(() => {
  vi.resetAllMocks();
  HTMLDialogElement.prototype.showModal = function () {
    this.setAttribute("open", "");
  };
  HTMLDialogElement.prototype.close = function () {
    this.removeAttribute("open");
  };
});
it("associa erros de validação ao campo e devolve-lhe o foco", async () => {
  const u = userEvent.setup();
  render(<Auth onSuccess={vi.fn()} />);
  await u.click(
    screen.getByRole("button", { name: "Criar conta", exact: true }),
  );
  await u.click(screen.getByRole("button", { name: /Criar conta e começar/ }));
  expect(screen.getByLabelText("Nome de utilizador")).toHaveAttribute(
    "aria-invalid",
    "true",
  );
  await waitFor(() =>
    expect(screen.getByLabelText("Nome de utilizador")).toHaveFocus(),
  );
  expect(api).not.toHaveBeenCalled();
});
it("deteta a confirmação diferente antes de enviar credenciais", async () => {
  const u = userEvent.setup();
  render(<Auth onSuccess={vi.fn()} />);
  await u.click(
    screen.getByRole("button", { name: "Criar conta", exact: true }),
  );
  await u.type(screen.getByLabelText("Nome de utilizador"), "nova");
  await u.type(
    screen.getByLabelText("Palavra-passe", { exact: true }),
    "Segura!12345",
  );
  await u.type(screen.getByLabelText("Confirmar palavra-passe"), "diferente");
  await u.click(screen.getByRole("button", { name: /Criar conta e começar/ }));
  expect(screen.getByText("As palavras-passe não coincidem.")).toBeVisible();
  expect(api).not.toHaveBeenCalled();
});
it("permite mostrar a palavra-passe sem perder o valor", async () => {
  const u = userEvent.setup();
  render(<Auth onSuccess={vi.fn()} />);
  const input = screen.getByLabelText("Palavra-passe", { exact: true });
  await u.type(input, "Texto!12345");
  await u.click(screen.getByRole("button", { name: "Mostrar palavra-passe" }));
  expect(input).toHaveAttribute("type", "text");
  expect(input).toHaveValue("Texto!12345");
  await u.click(screen.getByRole("button", { name: "Ocultar palavra-passe" }));
  expect(input).toHaveAttribute("type", "password");
});
it("mostra erros de resgate dentro do modal, mantendo-o aberto", async () => {
  const u = userEvent.setup();
  const confirm = vi
    .fn()
    .mockResolvedValue({ ok: false, error: "Saldo insuficiente." });
  render(
    <Confirm
      reward={{ title: "Caderno", cost: 180 }}
      balance={200}
      busy={false}
      onClose={vi.fn()}
      onConfirm={confirm}
    />,
  );
  await u.click(
    screen.getByRole("button", { name: "Confirmar resgate", exact: true }),
  );
  expect(
    await within(screen.getByRole("dialog")).findByRole("alert"),
  ).toHaveTextContent("Saldo insuficiente.");
  expect(screen.getByRole("dialog")).toBeVisible();
});
it("impede confirmar um brinde que ficou sem saldo", () => {
  render(
    <Confirm
      reward={{ title: "Caderno", cost: 180 }}
      balance={100}
      busy={false}
      onClose={vi.fn()}
      onConfirm={vi.fn()}
    />,
  );
  expect(
    screen.getByRole("button", { name: "Confirmar resgate", exact: true }),
  ).toBeDisabled();
});
it("permite filtrar créditos e resgates no histórico", async () => {
  const u = userEvent.setup();
  render(
    <History
      movements={[
        {
          id: 1,
          title: "Energia",
          amount: 80,
          kind: "credit",
          date: "2026-10-26T12:00:00Z",
        },
        {
          id: 2,
          title: "Pack",
          amount: -80,
          kind: "redeem",
          date: "2026-10-26T12:02:00Z",
          code: "codigo-unico",
        },
      ]}
    />,
  );
  await u.click(screen.getByRole("button", { name: "Resgates", exact: true }));
  expect(screen.queryByText("Energia")).not.toBeInTheDocument();
  expect(screen.getByText("Pack")).toBeVisible();
  await u.click(screen.getByRole("button", { name: "Pontos ganhos" }));
  expect(screen.getByText("Energia")).toBeVisible();
  expect(screen.queryByText("Pack")).not.toBeInTheDocument();
});
it("copia o código completo e confirma a ação", async () => {
  const u = userEvent.setup();
  const copy = vi.spyOn(navigator.clipboard, "writeText").mockResolvedValue();
  render(
    <History
      movements={[
        {
          id: 1,
          title: "Pack",
          amount: -80,
          kind: "redeem",
          date: "2026-10-26T12:02:00Z",
          code: "codigo-unico",
        },
      ]}
    />,
  );
  await u.click(screen.getByRole("button", { name: "Copiar código de Pack" }));
  expect(copy).toHaveBeenCalledWith("codigo-unico");
  expect(await screen.findByRole("status")).toHaveTextContent(
    "Código copiado.",
  );
});
it("mostra a explicação num desafio já concluído", () => {
  render(
    <Challenge
      index={0}
      challenge={{
        id: "energia",
        title: "Energia",
        category: "Ciência",
        points: 80,
        completed: true,
        explanation: "O vento é renovável.",
      }}
    />,
  );
  expect(screen.getByText("O vento é renovável.")).toBeVisible();
  expect(
    screen.queryByRole("button", { name: /Validar resposta/ }),
  ).not.toBeInTheDocument();
});

it("apresenta uma alternativa quando não consegue copiar o código", async () => {
  const u = userEvent.setup();
  vi.spyOn(navigator.clipboard, "writeText").mockRejectedValue(
    new Error("indisponível"),
  );
  render(
    <History
      movements={[
        {
          id: 1,
          title: "Pack",
          amount: -80,
          kind: "redeem",
          date: "2026-10-26T12:02:00Z",
          code: "codigo-unico",
        },
      ]}
    />,
  );
  await u.click(screen.getByRole("button", { name: "Copiar código de Pack" }));
  expect(await screen.findByRole("status")).toHaveTextContent(
    "copia-o manualmente",
  );
});
it("exporta um CSV que não interpreta descrições como fórmulas", async () => {
  const u = userEvent.setup();
  let exported;
  const create = vi.fn((blob) => {
    exported = blob;
    return "blob:local";
  });
  vi.stubGlobal("URL", { createObjectURL: create, revokeObjectURL: vi.fn() });
  vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});
  render(
    <History
      movements={[
        {
          id: 1,
          title: "=2+3",
          amount: -80,
          kind: "redeem",
          date: "2026-10-26T12:02:00Z",
          code: "codigo-unico",
        },
      ]}
    />,
  );
  await u.click(screen.getByRole("button", { name: "Descarregar histórico" }));
  expect(create).toHaveBeenCalledTimes(1);
  const text = await new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.readAsText(exported);
  });
  expect(text).toContain('"\'=2+3"');
  expect(text).toContain('"-80"');
  await new Promise((resolve) => setTimeout(resolve, 1100));
  vi.unstubAllGlobals();
});

it("associa a validação recebida do servidor à palavra-passe", async () => {
  const u = userEvent.setup();
  api.mockRejectedValueOnce(
    Object.assign(new Error("Revê os campos"), {
      fields: { password: ["Escolhe uma palavra-passe menos comum."] },
    }),
  );
  render(<Auth onSuccess={vi.fn()} />);
  await u.click(
    screen.getByRole("button", { name: "Criar conta", exact: true }),
  );
  await u.type(screen.getByLabelText("Nome de utilizador"), "nova");
  await u.type(
    screen.getByLabelText("Palavra-passe", { exact: true }),
    "Bastante!Segura2026",
  );
  await u.type(
    screen.getByLabelText("Confirmar palavra-passe"),
    "Bastante!Segura2026",
  );
  await u.click(screen.getByRole("button", { name: /Criar conta e começar/ }));
  expect(
    await screen.findByText("Escolhe uma palavra-passe menos comum."),
  ).toBeVisible();
  await waitFor(() =>
    expect(
      screen.getByLabelText("Palavra-passe", { exact: true }),
    ).toHaveFocus(),
  );
});
