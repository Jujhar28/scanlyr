export type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

export type ApiErrorBody = {
  code?: string;
  message?: string;
  detail?: string | unknown;
  details?: unknown;
};
