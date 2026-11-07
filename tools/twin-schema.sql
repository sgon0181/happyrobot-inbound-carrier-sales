-- Bootstrap only. Select the intended Twin environment in the SQL console first.
-- Execute each statement separately. Existing tables and rows are never replaced.
-- This matches the observed submission staging table shape on 2026-11-07.
-- The service supplies version=1 and object data on insert, then uses version-checked writes.
CREATE TABLE IF NOT EXISTS calls (id text PRIMARY KEY, version bigint, data jsonb);
CREATE TABLE IF NOT EXISTS bookings (id text PRIMARY KEY, version bigint, data jsonb);
CREATE TABLE IF NOT EXISTS negotiations (id text PRIMARY KEY, version bigint, data jsonb);
