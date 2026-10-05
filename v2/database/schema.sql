-- ============================================================
-- EARTHQUAKE 3D
-- Esquema inicial de base de datos
-- Version del modelo: 2.0.0
-- Clasificacion: experimental
-- No constituye una alerta oficial ni una prediccion determinista.
-- ============================================================

PRAGMA foreign_keys = ON;

CREATE TABLE data_sources (
    source_id INTEGER PRIMARY KEY,
    source_code TEXT NOT NULL UNIQUE,
    source_name TEXT NOT NULL,
    source_type TEXT NOT NULL,
    authority_level TEXT NOT NULL,
    base_url TEXT,
    active INTEGER NOT NULL DEFAULT 1,
    created_at_utc TEXT NOT NULL
);

CREATE TABLE source_imports (
    import_id INTEGER PRIMARY KEY,
    source_id INTEGER NOT NULL,
    started_at_utc TEXT NOT NULL,
    completed_at_utc TEXT,
    status TEXT NOT NULL,
    records_received INTEGER DEFAULT 0,
    records_accepted INTEGER DEFAULT 0,
    records_rejected INTEGER DEFAULT 0,
    content_hash TEXT,
    error_summary TEXT,
    FOREIGN KEY (source_id) REFERENCES data_sources(source_id)
);

CREATE TABLE seismic_events (
    event_id INTEGER PRIMARY KEY,
    canonical_event_key TEXT NOT NULL UNIQUE,
    origin_time_utc TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    depth_km REAL,
    magnitude REAL,
    magnitude_type TEXT,
    place_description TEXT,
    review_status TEXT,
    event_class TEXT,
    is_deep_candidate INTEGER NOT NULL DEFAULT 0,
    is_induced_candidate INTEGER NOT NULL DEFAULT 0,
    created_at_utc TEXT NOT NULL,
    CHECK (latitude BETWEEN -90 AND 90),
    CHECK (longitude BETWEEN -180 AND 180),
    CHECK (depth_km IS NULL OR depth_km >= 0)
);

CREATE TABLE seismic_event_revisions (
    revision_id INTEGER PRIMARY KEY,
    event_id INTEGER NOT NULL,
    source_id INTEGER NOT NULL,
    source_event_id TEXT NOT NULL,
    source_updated_at_utc TEXT,
    origin_time_utc TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    depth_km REAL,
    magnitude REAL,
    magnitude_type TEXT,
    raw_payload TEXT NOT NULL,
    imported_at_utc TEXT NOT NULL,
    FOREIGN KEY (event_id) REFERENCES seismic_events(event_id),
    FOREIGN KEY (source_id) REFERENCES data_sources(source_id),
    UNIQUE (source_id, source_event_id, source_updated_at_utc)
);

CREATE TABLE map_versions (
    map_version_id INTEGER PRIMARY KEY,
    version_code TEXT NOT NULL UNIQUE,
    source_file_name TEXT NOT NULL,
    source_hash TEXT NOT NULL,
    description TEXT,
    is_original INTEGER NOT NULL DEFAULT 0,
    created_at_utc TEXT NOT NULL
);

CREATE TABLE map_nodes (
    node_id INTEGER PRIMARY KEY,
    map_version_id INTEGER NOT NULL,
    node_code TEXT NOT NULL,
    node_type TEXT NOT NULL,
    label TEXT,
    latitude REAL,
    longitude REAL,
    geometry_source TEXT NOT NULL,
    confidence REAL,
    notes TEXT,
    FOREIGN KEY (map_version_id) REFERENCES map_versions(map_version_id),
    UNIQUE (map_version_id, node_code),
    CHECK (node_type IN ('D','X','VOLCANO','BRANCH','REFLECTION','INTERMEDIATE')),
    CHECK (confidence IS NULL OR confidence BETWEEN 0 AND 1)
);

CREATE TABLE corridors (
    corridor_id INTEGER PRIMARY KEY,
    map_version_id INTEGER NOT NULL,
    corridor_code TEXT NOT NULL,
    corridor_name TEXT,
    start_node_id INTEGER,
    end_node_id INTEGER,
    direction_type TEXT NOT NULL,
    geological_class TEXT,
    geometry_geojson TEXT,
    length_km REAL,
    digitization_confidence REAL,
    active INTEGER NOT NULL DEFAULT 1,
    notes TEXT,
    FOREIGN KEY (map_version_id) REFERENCES map_versions(map_version_id),
    FOREIGN KEY (start_node_id) REFERENCES map_nodes(node_id),
    FOREIGN KEY (end_node_id) REFERENCES map_nodes(node_id),
    UNIQUE (map_version_id, corridor_code),
    CHECK (digitization_confidence IS NULL OR digitization_confidence BETWEEN 0 AND 1)
);

CREATE TABLE corridor_segments (
    segment_id INTEGER PRIMARY KEY,
    corridor_id INTEGER NOT NULL,
    segment_order INTEGER NOT NULL,
    segment_code TEXT NOT NULL UNIQUE,
    start_distance_km REAL NOT NULL,
    end_distance_km REAL NOT NULL,
    administrative_region TEXT,
    baseline_event_rate REAL,
    baseline_period_code TEXT,
    geometry_geojson TEXT,
    FOREIGN KEY (corridor_id) REFERENCES corridors(corridor_id),
    UNIQUE (corridor_id, segment_order),
    CHECK (segment_order >= 1),
    CHECK (start_distance_km >= 0),
    CHECK (end_distance_km > start_distance_km)
);

CREATE TABLE event_corridor_projections (
    projection_id INTEGER PRIMARY KEY,
    event_id INTEGER NOT NULL,
    corridor_id INTEGER NOT NULL,
    segment_id INTEGER,
    perpendicular_distance_km REAL NOT NULL,
    along_corridor_distance_km REAL NOT NULL,
    direction_compatible INTEGER,
    node_d_distance_km REAL,
    node_x_distance_km REAL,
    projection_algorithm TEXT NOT NULL,
    algorithm_version TEXT NOT NULL,
    created_at_utc TEXT NOT NULL,
    FOREIGN KEY (event_id) REFERENCES seismic_events(event_id),
    FOREIGN KEY (corridor_id) REFERENCES corridors(corridor_id),
    FOREIGN KEY (segment_id) REFERENCES corridor_segments(segment_id),
    UNIQUE (event_id, corridor_id, projection_algorithm, algorithm_version),
    CHECK (perpendicular_distance_km >= 0),
    CHECK (along_corridor_distance_km >= 0)
);

CREATE TABLE forecasts (
    forecast_id INTEGER PRIMARY KEY,
    forecast_code TEXT NOT NULL UNIQUE,
    model_version TEXT NOT NULL,
    issued_at_utc TEXT NOT NULL,
    valid_from_utc TEXT NOT NULL,
    valid_to_utc TEXT NOT NULL,
    formation_start_utc TEXT NOT NULL,
    formation_end_utc TEXT NOT NULL,
    current_version INTEGER NOT NULL DEFAULT 1,
    public_status TEXT NOT NULL,
    experimental_label INTEGER NOT NULL DEFAULT 1,
    warning_text TEXT NOT NULL,
    CHECK (current_version >= 1)
);

CREATE TABLE forecast_versions (
    forecast_version_id INTEGER PRIMARY KEY,
    forecast_id INTEGER NOT NULL,
    version_number INTEGER NOT NULL,
    created_at_utc TEXT NOT NULL,
    trigger_event_id INTEGER,
    action_type TEXT NOT NULL,
    confidence_score REAL,
    magnitude_lower REAL,
    magnitude_upper REAL,
    rules_snapshot TEXT NOT NULL,
    parameters_snapshot TEXT NOT NULL,
    rationale TEXT NOT NULL,
    supersedes_version_id INTEGER,
    FOREIGN KEY (forecast_id) REFERENCES forecasts(forecast_id),
    FOREIGN KEY (trigger_event_id) REFERENCES seismic_events(event_id),
    FOREIGN KEY (supersedes_version_id) REFERENCES forecast_versions(forecast_version_id),
    UNIQUE (forecast_id, version_number),
    CHECK (version_number >= 1),
    CHECK (action_type IN ('CREATE','MAINTAIN','CONFIRM','DISPLACE','SPLIT','CANCEL','RESTART')),
    CHECK (confidence_score IS NULL OR confidence_score BETWEEN 0 AND 1)
);

CREATE TABLE forecast_regions (
    forecast_region_id INTEGER PRIMARY KEY,
    forecast_version_id INTEGER NOT NULL,
    corridor_id INTEGER,
    segment_id INTEGER,
    region_name TEXT NOT NULL,
    region_type TEXT NOT NULL,
    priority_weight REAL,
    geometry_method TEXT NOT NULL,
    geometry_geojson TEXT,
    FOREIGN KEY (forecast_version_id) REFERENCES forecast_versions(forecast_version_id),
    FOREIGN KEY (corridor_id) REFERENCES corridors(corridor_id),
    FOREIGN KEY (segment_id) REFERENCES corridor_segments(segment_id),
    CHECK (priority_weight IS NULL OR priority_weight BETWEEN 0 AND 1)
);

CREATE TABLE forecast_evaluations (
    evaluation_id INTEGER PRIMARY KEY,
    forecast_version_id INTEGER NOT NULL,
    evaluated_at_utc TEXT NOT NULL,
    outcome_class TEXT NOT NULL,
    matched_event_id INTEGER,
    temporal_hit INTEGER NOT NULL DEFAULT 0,
    spatial_hit INTEGER NOT NULL DEFAULT 0,
    magnitude_hit INTEGER,
    distance_to_region_km REAL,
    along_corridor_error_km REAL,
    magnitude_error REAL,
    relevant_events_inside INTEGER NOT NULL DEFAULT 0,
    relevant_events_outside INTEGER NOT NULL DEFAULT 0,
    false_positive INTEGER NOT NULL DEFAULT 0,
    false_negative INTEGER NOT NULL DEFAULT 0,
    evaluation_parameters TEXT NOT NULL,
    FOREIGN KEY (forecast_version_id) REFERENCES forecast_versions(forecast_version_id),
    FOREIGN KEY (matched_event_id) REFERENCES seismic_events(event_id),
    CHECK (outcome_class IN ('FULL_HIT','SPATIAL_TEMPORAL_HIT','PARTIAL_HIT','MISS','FALSE_ALARM','FALSE_NEGATIVE','NOT_EVALUATED'))
);

CREATE INDEX idx_events_origin_time ON seismic_events(origin_time_utc);
CREATE INDEX idx_events_depth ON seismic_events(depth_km);
CREATE INDEX idx_events_magnitude ON seismic_events(magnitude);
CREATE INDEX idx_events_deep_candidate ON seismic_events(is_deep_candidate);
CREATE INDEX idx_projections_event ON event_corridor_projections(event_id);
CREATE INDEX idx_projections_corridor ON event_corridor_projections(corridor_id);
CREATE INDEX idx_forecasts_validity ON forecasts(valid_from_utc, valid_to_utc);
CREATE INDEX idx_forecast_versions_forecast ON forecast_versions(forecast_id, version_number);
CREATE INDEX idx_evaluations_version ON forecast_evaluations(forecast_version_id);

-- ============================================================
-- FIN DEL ESQUEMA INICIAL
-- ============================================================
