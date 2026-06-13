export type StateContextClass =
  | "operator_package"
  | "development_default"
  | "qa_temporary"
  | "configured"
  | "unknown"
  | "inaccessible"
  | string;

export type StateStorageStatus = "present" | "missing" | "inaccessible" | "unknown" | string;

export interface StateContext {
  contextClass: StateContextClass;
  label: string;
  storageStatus: StateStorageStatus;
  source: "default" | "env" | "init" | "unknown" | string;
}

export const unknownStateContext: StateContext = {
  contextClass: "unknown",
  label: "Unknown state",
  storageStatus: "unknown",
  source: "unknown",
};
