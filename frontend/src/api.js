// Auxílio de IA identificado em AI_USAGE.md. Os cookies de sessão são HttpOnly;
// o único cookie lido aqui é o token CSRF, que não é uma credencial de login.
export class ApiError extends Error {
  constructor(
    message,
    { status = 0, code = "network_error", fields = {}, retryAfter = null } = {},
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.fields = fields;
    this.retryAfter = retryAfter;
  }
}

async function request(path, data, { signal, timeout = 25000 } = {}) {
  const controller = new AbortController();
  let timedOut = false;
  const abort = () => controller.abort();
  if (signal?.aborted) abort();
  signal?.addEventListener("abort", abort, { once: true });
  const timer = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, timeout);
  const token = document.cookie
    .split("; ")
    .find((value) => value.startsWith("csrftoken="))
    ?.split("=")[1];
  try {
    const response = await fetch(`/api/${path}/`, {
      method: data === undefined ? "GET" : "POST",
      credentials: "same-origin",
      cache: "no-store",
      signal: controller.signal,
      headers: {
        Accept: "application/json",
        ...(data === undefined
          ? {}
          : { "Content-Type": "application/json", "X-CSRFToken": token || "" }),
      },
      ...(data === undefined ? {} : { body: JSON.stringify(data) }),
    });
    let payload;
    try {
      payload = await response.json();
    } catch {
      throw new ApiError(
        "O servidor enviou uma resposta inesperada. Atualiza a página e tenta novamente.",
        { status: response.status, code: "invalid_response" },
      );
    }
    if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
      throw new ApiError(
        "Não foi possível interpretar a resposta do servidor.",
        { status: response.status, code: "invalid_response" },
      );
    }
    if (!response.ok) {
      throw new ApiError(
        payload.error || "Não foi possível concluir o pedido.",
        {
          status: response.status,
          code: payload.code,
          fields: payload.fields,
          retryAfter: payload.retry_after,
        },
      );
    }
    if (
      !Object.hasOwn(payload, "user") ||
      (payload.user !== null &&
        (!payload.user ||
          typeof payload.user.username !== "string" ||
          !Number.isSafeInteger(payload.balance) ||
          payload.balance < 0 ||
          !Array.isArray(payload.challenges) ||
          !Array.isArray(payload.rewards) ||
          !Array.isArray(payload.movements)))
    ) {
      throw new ApiError("A resposta não contém um estado válido da conta.", {
        status: response.status,
        code: "invalid_response",
      });
    }
    return payload;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (signal?.aborted)
      throw new ApiError("Pedido cancelado.", { code: "aborted" });
    throw new ApiError(
      timedOut
        ? "A resposta está a demorar mais do que o esperado. Vamos confirmar o estado antes de repetires a operação."
        : "A ligação foi interrompida. Confirma a tua ligação à Internet e tenta novamente.",
      { code: timedOut ? "timeout" : "network_error" },
    );
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener("abort", abort);
  }
}

export async function api(path, data, options = {}) {
  try {
    return await request(path, data, options);
  } catch (error) {
    // Só repetimos automaticamente quando o middleware confirmou que rejeitou
    // o pedido ANTES da operação. Uma falha de rede nunca autoriza repetir um débito.
    if (data !== undefined && error.code === "csrf_failed") {
      await request("session", undefined, options);
      return request(path, data, options);
    }
    throw error;
  }
}
