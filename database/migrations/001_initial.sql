-- Migration 001: Initial schema
-- Identical to schema.sql — serves as the first versioned checkpoint
BEGIN;
-- Run: psql -U raksha -d rakshaai -f database/schema.sql
COMMIT;
