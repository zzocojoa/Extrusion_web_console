export const LOCAL_TOKEN_HEADER = "X-EWC-Local-Token";
export const LOCAL_TOKEN_ERROR_CODE = "local_token_required";
export const LOCAL_TOKEN_MISSING_REASON = "local_token_missing";
export const LOCAL_TOKEN_INVALID_REASON = "local_token_invalid";
export const LOCAL_TOKEN_MESSAGE_EN =
  "Local console session is not valid. Open the console from the tray or restart it from the launcher.";
export const LOCAL_TOKEN_MESSAGE_KO =
  "로컬 콘솔 세션이 유효하지 않습니다. 트레이 아이콘에서 Open을 누르거나 런처로 다시 실행하세요.";
export const LOCAL_TOKEN_STALE_MESSAGE_EN =
  "This browser tab is using an old local console session. Open the console from the tray or restart it from the launcher.";
export const LOCAL_TOKEN_STALE_MESSAGE_KO =
  "이 브라우저 탭의 로컬 콘솔 세션이 오래되었습니다. 트레이 아이콘에서 Open을 눌러 새 탭을 열거나 런처로 다시 실행하세요.";

declare global {
  interface Window {
    __EWC_BOOTSTRAP__?: {
      localApiToken?: string;
    };
  }
}

export class LocalTokenApiError extends Error {
  code = LOCAL_TOKEN_ERROR_CODE;
  reason: string;
  status: number;
  recovery: string | null;

  constructor(status: number, reason: string = LOCAL_TOKEN_MISSING_REASON, recovery: string | null = null) {
    super(localTokenOperatorMessage(reason));
    this.name = "LocalTokenApiError";
    this.status = status;
    this.reason = reason;
    this.recovery = recovery;
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
  const localTokenDetail = response.status === 403 ? await readLocalTokenResponse(response.clone()) : null;
  if (localTokenDetail) {
    throw new LocalTokenApiError(response.status, localTokenDetail.reason, localTokenDetail.recovery);
  }
  return response;
}

export function isLocalTokenApiError(error: unknown): error is LocalTokenApiError {
  return error instanceof LocalTokenApiError;
}

function localTokenOperatorMessage(reason: string): string {
  const language =
    typeof window !== "undefined" ? window.localStorage.getItem("ewc.language") : null;
  if (reason === LOCAL_TOKEN_INVALID_REASON) {
    return language === "en" ? LOCAL_TOKEN_STALE_MESSAGE_EN : LOCAL_TOKEN_STALE_MESSAGE_KO;
  }
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

async function readLocalTokenResponse(response: Response): Promise<{ reason: string; recovery: string | null } | null> {
  const raw = await response.json().catch(() => null);
  if (raw?.detail?.code !== LOCAL_TOKEN_ERROR_CODE) return null;
  const reason = typeof raw?.detail?.reason === "string" ? raw.detail.reason : LOCAL_TOKEN_MISSING_REASON;
  const recovery = typeof raw?.detail?.recovery === "string" ? raw.detail.recovery : null;
  return { reason, recovery };
}
