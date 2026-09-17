CREATE TABLE IF NOT EXISTS vehicles (
    vehicle_id TEXT PRIMARY KEY,
    current_firmware_version TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS firmware_versions (
    id SERIAL PRIMARY KEY,
    version TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS rollouts (
    id SERIAL PRIMARY KEY,
    firmware_version_id INTEGER NOT NULL REFERENCES firmware_versions(id),
    stages INTEGER[] NOT NULL,
    current_stage_index INTEGER NOT NULL DEFAULT -1,
    status TEXT NOT NULL DEFAULT 'pending',
    failure_threshold_percent DOUBLE PRECISION NOT NULL DEFAULT 15,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS rollout_batches (
    id SERIAL PRIMARY KEY,
    rollout_id INTEGER NOT NULL REFERENCES rollouts(id),
    vehicle_id TEXT NOT NULL REFERENCES vehicles(vehicle_id),
    stage_index INTEGER NOT NULL,
    stage_percent INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (rollout_id, vehicle_id)
);

CREATE INDEX IF NOT EXISTS idx_rollout_batches_rollout_id ON rollout_batches (rollout_id);
CREATE INDEX IF NOT EXISTS idx_rollout_batches_status ON rollout_batches (status);
