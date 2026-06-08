-- Independent Extrusion Web Console upload contract.
--
-- Derived from the legacy all_metrics schema and the
-- 20260421000001 device-scope restore migration. This clean baseline keeps
-- only the Core Ops upload/preview surface needed by the web console.

CREATE TABLE IF NOT EXISTS public.all_metrics (
    "timestamp" timestamp with time zone NOT NULL,
    device_id text NOT NULL,
    temperature double precision,
    main_pressure double precision,
    billet_length double precision,
    container_temp_front double precision,
    container_temp_rear double precision,
    production_counter bigint,
    current_speed double precision,
    extrusion_end_position double precision,
    mold_1 double precision,
    mold_2 double precision,
    mold_3 double precision,
    mold_4 double precision,
    mold_5 double precision,
    mold_6 double precision,
    billet_temp double precision,
    at_pre double precision,
    at_temp double precision,
    die_id text,
    billet_cycle_id bigint
);

ALTER TABLE public.all_metrics OWNER TO postgres;

ALTER TABLE public.all_metrics
    DROP CONSTRAINT IF EXISTS all_metrics_timestamp_device_id_key;

ALTER TABLE public.all_metrics
    ADD CONSTRAINT all_metrics_timestamp_device_id_key
        UNIQUE ("timestamp", device_id);

CREATE INDEX IF NOT EXISTS idx_all_metrics_latest_timestamp_by_device
    ON public.all_metrics (device_id, "timestamp" DESC);

CREATE INDEX IF NOT EXISTS idx_all_metrics_timestamp
    ON public.all_metrics ("timestamp");

ALTER TABLE public.all_metrics ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS allow_anon_insert_all_metrics ON public.all_metrics;
CREATE POLICY allow_anon_insert_all_metrics ON public.all_metrics
FOR INSERT
TO anon
WITH CHECK (true);

DROP POLICY IF EXISTS allow_anon_select_all_metrics ON public.all_metrics;
CREATE POLICY allow_anon_select_all_metrics ON public.all_metrics
FOR SELECT
TO anon
USING (true);

DROP POLICY IF EXISTS allow_anon_update_all_metrics ON public.all_metrics;
CREATE POLICY allow_anon_update_all_metrics ON public.all_metrics
FOR UPDATE
TO anon
USING (true)
WITH CHECK (true);

GRANT SELECT, INSERT, UPDATE ON TABLE public.all_metrics TO anon;
GRANT SELECT, INSERT, UPDATE ON TABLE public.all_metrics TO authenticated;
GRANT ALL ON TABLE public.all_metrics TO service_role;
