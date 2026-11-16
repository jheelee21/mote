-- Initial schema. See docs/architecture.md for how these tables are used.

CREATE TABLE libraries (
    id            INTEGER PRIMARY KEY,
    root_path     TEXT NOT NULL UNIQUE,
    name          TEXT NOT NULL,
    added_at      TEXT NOT NULL DEFAULT (datetime('now')),
    last_scan_at  TEXT,
    is_online     INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE photos (
    id            INTEGER PRIMARY KEY,
    library_id    INTEGER NOT NULL REFERENCES libraries(id) ON DELETE CASCADE,
    path          TEXT NOT NULL UNIQUE,
    size          INTEGER NOT NULL,
    mtime         REAL NOT NULL,
    file_hash     TEXT,
    format        TEXT NOT NULL,
    is_raw        INTEGER NOT NULL DEFAULT 0,
    width         INTEGER,
    height        INTEGER,
    taken_at      TEXT,
    camera        TEXT,
    lens          TEXT,
    focal_length  REAL,
    iso           INTEGER,
    aperture      REAL,
    shutter       TEXT,
    gps_lat       REAL,
    gps_lon       REAL,
    status        TEXT NOT NULL DEFAULT 'new'
                  CHECK (status IN ('new', 'thumbed', 'embedded', 'missing', 'failed')),
    error         TEXT
);
CREATE INDEX idx_photos_library ON photos(library_id);
CREATE INDEX idx_photos_status ON photos(status);
CREATE INDEX idx_photos_taken_at ON photos(taken_at);

CREATE TABLE thumbnails (
    photo_id    INTEGER NOT NULL REFERENCES photos(id) ON DELETE CASCADE,
    size        INTEGER NOT NULL,
    cache_path  TEXT NOT NULL,
    PRIMARY KEY (photo_id, size)
);

CREATE TABLE embeddings (
    photo_id    INTEGER NOT NULL REFERENCES photos(id) ON DELETE CASCADE,
    model_id    TEXT NOT NULL,
    dim         INTEGER NOT NULL,
    vector      BLOB NOT NULL,          -- float32, little-endian, L2-normalised
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (photo_id, model_id)
);

CREATE TABLE signals (
    photo_id        INTEGER PRIMARY KEY REFERENCES photos(id) ON DELETE CASCADE,
    palette         TEXT,               -- JSON list of hex colours
    warmth          REAL,
    saturation      REAL,
    brightness      REAL,
    contrast        REAL,
    sharpness       REAL,
    time_of_day     TEXT,
    season          TEXT,
    indoor_outdoor  TEXT,
    people_count    INTEGER
);

CREATE TABLE cluster_runs (
    id           INTEGER PRIMARY KEY,
    model_id     TEXT NOT NULL,
    params       TEXT NOT NULL,         -- JSON
    started_at   TEXT NOT NULL DEFAULT (datetime('now')),
    finished_at  TEXT,
    stats        TEXT                   -- JSON
);

CREATE TABLE stories (
    id              INTEGER PRIMARY KEY,
    title           TEXT NOT NULL,
    auto_title      TEXT,
    description     TEXT,
    kind            TEXT NOT NULL DEFAULT 'custom'
                    CHECK (kind IN ('places', 'people', 'mood', 'season', 'custom')),
    source          TEXT NOT NULL DEFAULT 'auto' CHECK (source IN ('auto', 'search', 'manual')),
    cover_photo_id  INTEGER REFERENCES photos(id) ON DELETE SET NULL,
    cluster_run_id  INTEGER REFERENCES cluster_runs(id) ON DELETE SET NULL,
    is_pinned       INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- membership: 'auto' from clustering; 'added'/'removed' are user overrides
-- that must survive re-clustering.
CREATE TABLE story_photos (
    story_id    INTEGER NOT NULL REFERENCES stories(id) ON DELETE CASCADE,
    photo_id    INTEGER NOT NULL REFERENCES photos(id) ON DELETE CASCADE,
    score       REAL,
    membership  TEXT NOT NULL DEFAULT 'auto' CHECK (membership IN ('auto', 'added', 'removed')),
    PRIMARY KEY (story_id, photo_id)
);

CREATE TABLE feedback (
    id          INTEGER PRIMARY KEY,
    story_id    INTEGER NOT NULL REFERENCES stories(id) ON DELETE CASCADE,
    photo_id    INTEGER NOT NULL REFERENCES photos(id) ON DELETE CASCADE,
    label       TEXT NOT NULL CHECK (label IN ('more', 'less')),
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE series (
    id          INTEGER PRIMARY KEY,
    story_id    INTEGER REFERENCES stories(id) ON DELETE SET NULL,
    title       TEXT NOT NULL,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE series_photos (
    series_id  INTEGER NOT NULL REFERENCES series(id) ON DELETE CASCADE,
    photo_id   INTEGER NOT NULL REFERENCES photos(id) ON DELETE CASCADE,
    position   INTEGER NOT NULL,
    PRIMARY KEY (series_id, photo_id)
);

CREATE TABLE settings (
    key    TEXT PRIMARY KEY,
    value  TEXT NOT NULL
);
