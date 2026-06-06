export const LOCAL_TOKEN_HEADER = "X-EWC-Local-Token";
export const LOCAL_TOKEN_ERROR_CODE = "local_token_required";
export const LOCAL_TOKEN_MESSAGE_EN =
  "Local console session is no longer valid. Restart the web console from the launcher.";
export const LOCAL_TOKEN_MESSAGE_KO =
  "로컬 콘솔 세션이 유효하지 않습니다. 런처로 다시 실행하세요.";

declare global {
  interface Window {
    __EWC_BOOTSTRAP__?: {
      localApiToken?: string;
    };
  }
}

export class LocalTokenApiError extends Error {
  code = LOCAL_TOKEN_ERROR_CODE;
  status: number;

  constructor(status: number) {
    super(localTokenOperatorMessage());
    this.name = "LocalTokenApiError";
    this.status = status;
  }
}

export function getLocalApiToken(): string | null {
  const token = window.__EWC_BOOTSTRAP__?.localApiToken;
  return typeof token === "string" && token.length > 0 ? token : null;
}

export async function apiFetch(
  input: RequestInfo | URL,
  init: RequestInit = {},
  options: { mutating?: boolean } = {},
): Promise<Response> {
  const requestInit = { ...init };
  if (options.mutating && isSameOriginApiRequest(input)) {
    const token = getLocalApiToken();
    if (token) {
      const headers = new Headers(requestInit.headers);
      headers.set(LOCAL_TOKEN_HEADER, token);
      requestInit.headers = headers;
    }
  }
  const response = await fetch(input, requestInit);
  if (response.status === 403 && (await isLocalTokenResponse(response.clone()))) {
    throw new LocalTokenApiError(response.status);
  }
  return response;
}

export function isLocalTokenApiError(error: unknown): error is LocalTokenApiError {
  return error instanceof LocalTokenApiError;
}

function localTokenOperatorMessage(): string {
  const language =
    typeof window !== "undefined" ? window.localStorage.getItem("ewc.language") : null;
  return language === "en" ? LOCAL_TOKEN_MESSAGE_EN : LOCAL_TOKEN_MESSAGE_KO;
}

function isSameOriginApiRequest(input: RequestInfo | URL): boolean {
  const url = toUrl(input);
  return url.origin === window.location.origin && url.pathname.startsWith("/api/");
}

function toUrl(input: RequestInfo | URL): URL {
  if (input instanceof URL) return input;
  if (typeof input === "string") return new URL(input, window.location.origin);
  return new URL(input.url, window.location.origin);
}

async function isLocalTokenResponse(response: Response): Promise<boolean> {
  const raw = await response.json().catch(() => null);
  return raw?.detail?.code === LOCAL_TOKEN_ERROR_CODE;
}
