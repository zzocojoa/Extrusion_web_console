import { createClient, type SupabaseClient } from "jsr:@supabase/supabase-js@2";

type Metric = {
  timestamp: string;
  device_id: string;
  temperature?: number | null;
  main_pressure?: number | null;
  billet_length?: number | null;
  container_temp_front?: number | null;
  container_temp_rear?: number | null;
  production_counter?: number | null;
  current_speed?: number | null;
  extrusion_end_position?: number | null;
  mold_1?: number | null;
  mold_2?: number | null;
  mold_3?: number | null;
  mold_4?: number | null;
  mold_5?: number | null;
  mold_6?: number | null;
  billet_temp?: number | null;
  at_pre?: number | null;
  at_temp?: number | null;
  die_id?: string | null;
  billet_cycle_id?: number | null;
};

type JsonMap = {
  [key: string]: unknown;
};

type UploadPayload = {
  records: ReadonlyArray<unknown>;
};

type LatestTimestampRow = {
  timestamp: string | null;
};

type NumericMetricKey = Exclude<
  keyof Metric,
  "timestamp" | "device_id" | "die_id"
>;

const ALLOWED_KEYS = new Set<keyof Metric>([
  "timestamp",
  "device_id",
  "temperature",
  "main_pressure",
  "billet_length",
  "container_temp_front",
  "container_temp_rear",
  "production_counter",
  "current_speed",
  "extrusion_end_position",
  "mold_1",
  "mold_2",
  "mold_3",
  "mold_4",
  "mold_5",
  "mold_6",
  "billet_temp",
  "at_pre",
  "at_temp",
  "die_id",
  "billet_cycle_id",
]);

const NUMERIC_KEYS = new Set<NumericMetricKey>([
  "temperature",
  "main_pressure",
  "billet_length",
  "container_temp_front",
  "container_temp_rear",
  "production_counter",
  "current_speed",
  "extrusion_end_position",
  "mold_1",
  "mold_2",
  "mold_3",
  "mold_4",
  "mold_5",
  "mold_6",
  "billet_temp",
  "at_pre",
  "at_temp",
  "billet_cycle_id",
]);

const UPSERT_BATCH_MAX_RECORDS = 1000;
const UPSERT_BATCH_MAX_BYTES = 512 * 1024;
const JSON_ENCODER = new TextEncoder();

function isJsonMap(value: unknown): value is JsonMap {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function hasRecordsArray(value: unknown): value is UploadPayload {
  return isJsonMap(value) && Array.isArray(value.records);
}

function toNonEmptyString(value: unknown): string | null {
  if (value === null || value === undefined) {
    return null;
  }

  const normalized = String(value).trim();
  if (normalized.length === 0) {
    return null;
  }

  return normalized;
}

function toNumberOrNull(value: unknown): number | null {
  if (value === null || value === undefined) {
    return null;
  }

  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }

  if (typeof value === "string" && value.trim().length > 0) {
    const normalized = Number(value);
    if (Number.isFinite(normalized)) {
      return normalized;
    }
  }

  return null;
}

function getRecordSizeBytes(record: Metric): number {
  return JSON_ENCODER.encode(JSON.stringify(record)).length + 1;
}

function splitIntoUpsertBatches(
  records: ReadonlyArray<Metric>,
  maxRecords: number,
  maxBytes: number,
): Metric[][] {
  const batches: Metric[][] = [];
  let currentBatch: Metric[] = [];
  let currentBytes = 0;

  for (const record of records) {
    const recordBytes = getRecordSizeBytes(record);
    const exceedsBatchLimit = currentBatch.length > 0 &&
      (
        currentBatch.length + 1 > maxRecords ||
        currentBytes + recordBytes > maxBytes
      );

    if (exceedsBatchLimit) {
      batches.push(currentBatch);
      currentBatch = [];
      currentBytes = 0;
    }

    currentBatch.push(record);
    currentBytes += recordBytes;
  }

  if (currentBatch.length > 0) {
    batches.push(currentBatch);
  }

  return batches;
}

function cleanRecord(raw: JsonMap): Metric | null {
  const cleaned: Partial<Metric> = {};

  for (const [key, value] of Object.entries(raw)) {
    const metricKey = key as keyof Metric;
    if (!ALLOWED_KEYS.has(metricKey)) {
      continue;
    }

    if (metricKey === "timestamp" || metricKey === "device_id") {
      const normalized = toNonEmptyString(value);
      if (normalized === null) {
        return null;
      }
      cleaned[metricKey] = normalized;
      continue;
    }

    if (metricKey === "die_id") {
      cleaned.die_id = toNonEmptyString(value);
      continue;
    }

    const numericKey = metricKey as NumericMetricKey;
    if (NUMERIC_KEYS.has(numericKey)) {
      cleaned[numericKey] = toNumberOrNull(value);
    }
  }

  if (
    typeof cleaned.timestamp !== "string" ||
    typeof cleaned.device_id !== "string"
  ) {
    return null;
  }

  return cleaned as Metric;
}

function getEnv(name: string): string | undefined {
  const value = Deno.env.get(name);
  if (!value) {
    console.warn("Environment variable is not configured.", { name });
  }
  return value;
}

function createSupabaseClient(req: Request): SupabaseClient {
  const url = getEnv("SUPABASE_URL") ??
    "http://supabase_kong_Extrusion_web_console:8000";
  const anonKey = getEnv("SUPABASE_ANON_KEY");
  const authHeader = req.headers.get("Authorization");

  if (!anonKey) {
    throw new Error("SUPABASE_ANON_KEY is not configured.");
  }

  return createClient(url, anonKey, {
    global: {
      headers: authHeader === null ? {} : { Authorization: authHeader },
    },
    auth: {
      persistSession: false,
    },
  });
}

function jsonResponse(body: unknown, status: number): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
    },
  });
}

function getDeviceIdFromRequest(req: Request): string | null {
  const url = new URL(req.url);
  return toNonEmptyString(url.searchParams.get("device_id"));
}

function extractRawRecords(body: unknown): ReadonlyArray<unknown> | null {
  if (Array.isArray(body)) {
    return body;
  }

  if (hasRecordsArray(body)) {
    return body.records;
  }

  return null;
}

async function readLatestTimestampByDevice(
  supabase: SupabaseClient,
  deviceId: string,
): Promise<string | null> {
  const { data, error } = await supabase
    .from("all_metrics")
    .select("timestamp")
    .eq("device_id", deviceId)
    .order("timestamp", { ascending: false })
    .limit(1);

  if (error) {
    throw new Error(
      `Latest timestamp query failed(device_id=${deviceId}, message=${error.message}, code=${
        error.code ?? "unknown"
      })`,
    );
  }

  if (!Array.isArray(data) || data.length === 0) {
    return null;
  }

  const row = data[0] as LatestTimestampRow;
  return row.timestamp ?? null;
}

async function upsertMetricBatch(
  supabase: SupabaseClient,
  batch: ReadonlyArray<Metric>,
): Promise<number> {
  const { data, error } = await supabase
    .from("all_metrics")
    .upsert(batch, {
      onConflict: "timestamp,device_id",
    })
    .select("timestamp,device_id");

  if (error) {
    throw new Error(
      `Metric upsert failed(message=${error.message}, code=${
        error.code ?? "unknown"
      }, batch_size=${batch.length})`,
    );
  }

  return Array.isArray(data) ? data.length : 0;
}

async function handleGet(req: Request): Promise<Response> {
  const deviceId = getDeviceIdFromRequest(req);
  if (deviceId === null) {
    return jsonResponse(
      {
        success: false,
        error: "device_id query parameter is required.",
      },
      400,
    );
  }

  let supabase: SupabaseClient;
  try {
    supabase = createSupabaseClient(req);
  } catch (error) {
    console.error("Failed to create Supabase client.", { error, deviceId });
    return jsonResponse(
      {
        success: false,
        error: "Server configuration error.",
      },
      500,
    );
  }

  try {
    const latestTimestamp = await readLatestTimestampByDevice(
      supabase,
      deviceId,
    );
    return jsonResponse(
      {
        success: true,
        latest_timestamp: latestTimestamp,
      },
      200,
    );
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    console.error("Latest timestamp request failed.", {
      error: message,
      deviceId,
    });
    return jsonResponse(
      {
        success: false,
        error: message,
      },
      500,
    );
  }
}

async function handlePost(req: Request): Promise<Response> {
  let body: unknown;
  try {
    body = await req.json();
  } catch (error) {
    console.error("Failed to parse JSON body.", { error });
    return jsonResponse(
      {
        success: false,
        error: "A valid JSON body is required.",
      },
      400,
    );
  }

  const rawRecords = extractRawRecords(body);
  if (rawRecords === null) {
    return jsonResponse(
      {
        success: false,
        error: 'Body must be an array or include a "records" array.',
      },
      400,
    );
  }

  if (rawRecords.length === 0) {
    return jsonResponse(
      {
        success: false,
        error: "No records to upload.",
      },
      400,
    );
  }

  const cleaned: Metric[] = [];
  for (const record of rawRecords) {
    if (!isJsonMap(record)) {
      continue;
    }

    const cleanedRecord = cleanRecord(record);
    if (cleanedRecord !== null) {
      cleaned.push(cleanedRecord);
    }
  }

  if (cleaned.length === 0) {
    return jsonResponse(
      {
        success: false,
        error: "No valid records remained after cleaning.",
      },
      400,
    );
  }

  let supabase: SupabaseClient;
  try {
    supabase = createSupabaseClient(req);
  } catch (error) {
    console.error("Failed to create Supabase client.", { error });
    return jsonResponse(
      {
        success: false,
        error: "Server configuration error.",
      },
      500,
    );
  }

  const upsertBatches = splitIntoUpsertBatches(
    cleaned,
    UPSERT_BATCH_MAX_RECORDS,
    UPSERT_BATCH_MAX_BYTES,
  );

  let totalAccepted = 0;
  try {
    for (const batch of upsertBatches) {
      totalAccepted += await upsertMetricBatch(supabase, batch);
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    console.error("Batch upsert failed.", {
      error: message,
      recordCount: cleaned.length,
      batchCount: upsertBatches.length,
    });
    return jsonResponse(
      {
        success: false,
        error: message,
      },
      500,
    );
  }

  return jsonResponse(
    {
      success: true,
      accepted: totalAccepted,
      inserted: totalAccepted,
    },
    200,
  );
}

Deno.serve(async (req: Request): Promise<Response> => {
  console.log("upload-metrics request received.", { method: req.method });

  if (req.method === "GET") {
    return await handleGet(req);
  }

  if (req.method === "POST") {
    return await handlePost(req);
  }

  return jsonResponse(
    {
      success: false,
      error: "Method not allowed. Use GET or POST.",
    },
    405,
  );
});
