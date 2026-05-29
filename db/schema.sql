-- KD-IRIS 1차 빌드 — SQLite 스키마 (기능재설계 v2 §11.3)
-- 의약품QA × 자사 품목 마스터 × 모니터링
-- 모든 테이블 IF NOT EXISTS — init_db() 멱등 실행.

-- ────────────────────────────────────────────────────────────────────────
-- 자사 품목 마스터 (모든 조인의 키)
--   사내 입력 컬럼(xlsx) + 공공데이터 enrichment 컬럼(NO 140/35/145)
-- ────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS master_item (
    item_code         TEXT PRIMARY KEY,   -- 사내 품목코드
    item_name         TEXT NOT NULL,
    item_name_alt     TEXT,               -- 품목명2 (보조 매칭)
    category          TEXT,               -- 전문분류 (전문/일반/의약외품/향정/식품)
    sub_category      TEXT,               -- 품목분류 (외주/주성분/고형제 등)
    gubun             TEXT,               -- 품목구분 (포장제품/제조제품/의약외품/상품)
    shelf_life_mo     INTEGER,            -- 유효기간(개월)
    pack_spec         TEXT,               -- 포장규격
    batch_size        TEXT,               -- 배치사이즈
    consign_maker     TEXT,               -- 위탁처 (사내 입력)
    self_or_consign   TEXT,               -- 자사/위탁
    is_herbal         INTEGER DEFAULT 0,  -- 한약(생약) 추정 플래그 (1=한약)
    active            INTEGER DEFAULT 1,
    -- enrichment 결과 (NO 140/35/145로 채움)
    item_seq          TEXT,               -- NO 140 ITEM_SEQ
    permit_no         TEXT,               -- 허가번호 (PRDUCT_PRMISN_NO)
    permit_date       TEXT,               -- 실허가일 (placeholder 아닌 진짜)
    reexam_date       TEXT,               -- 재심사 예정일 (REEXAM_DATE)
    entp_name         TEXT,               -- 허가권자 (보통 광동제약)
    atc_code          TEXT,
    edi_code          TEXT,
    bar_code          TEXT,
    chart             TEXT,               -- 성상
    storage_method    TEXT,
    material_name     TEXT,               -- 주성분 상세 원문
    source_api        TEXT,               -- 'NO140' | 'NO35' | 'NO145' | 'unmatched'
    enrich_status     TEXT DEFAULT 'pending',  -- 'pending'|'matched'|'review'|'unmatched'|'manual'
    enrich_confidence TEXT,               -- 'high' | 'medium' | 'low'
    enrich_candidates JSON,               -- review 큐용 후보 1~3건
    enriched_at       TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_mi_item_seq ON master_item(item_seq);
CREATE INDEX IF NOT EXISTS idx_mi_enrich  ON master_item(enrich_status);
CREATE INDEX IF NOT EXISTS idx_mi_entp    ON master_item(entp_name);

-- ────────────────────────────────────────────────────────────────────────
-- 품목-성분 매핑 (N:M, enrichment 결과 — NO 140 주성분)
-- ────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS master_ingredient (
    item_code  TEXT,
    ingr_name  TEXT,      -- 주성분명 (MTRAL_NM)
    ingr_code  TEXT,      -- MTRAL_CODE
    qty        TEXT,      -- 분량 (QNT)
    unit       TEXT,      -- 단위
    FOREIGN KEY (item_code) REFERENCES master_item(item_code)
);
CREATE INDEX IF NOT EXISTS idx_ingr_name ON master_ingredient(ingr_name);
CREATE INDEX IF NOT EXISTS idx_ingr_item ON master_ingredient(item_code);

-- ────────────────────────────────────────────────────────────────────────
-- API별 일일 스냅샷 (단일 테이블 + api_id 구분)
--   natural_key: 회수 STD_CD+ITEM_SEQ / 처분 ENTP_NAME+처분일 / 서한 SAFT_LETT_NO / GMP BSSH_NM+FCTR_ADDR
-- ────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS snapshot (
    snap_date    DATE,
    api_id       TEXT,        -- 'NO539'|'NO564'|'NO547'|'NO132'  (+'NO90' hook)
    natural_key  TEXT,
    payload      JSON,
    PRIMARY KEY (snap_date, api_id, natural_key)
);
CREATE INDEX IF NOT EXISTS idx_snap_date_api ON snapshot(snap_date, api_id);

-- ────────────────────────────────────────────────────────────────────────
-- diff 결과 = 이벤트
-- ────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS event (
    event_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    detected_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    event_date          TEXT,                    -- 이벤트 발생/공표일 (YYYYMMDD)
    api_id              TEXT,
    event_type          TEXT,                    -- 'recall'|'sanction'|'safety_letter'|'gmp_expiry'
    severity            TEXT,                    -- CRITICAL/HIGH/LOW
    impact_level        TEXT,                    -- 'direct'|'same_ingredient'|'manufacturer'|'competitor'
    title               TEXT,
    entity              TEXT,
    summary             TEXT,
    matched_item_codes  JSON,                    -- 매칭된 자사 품목코드 배열
    matched_ingredients JSON,                    -- 매칭된 자사 성분명 배열
    raw_payload         JSON,
    status              TEXT DEFAULT 'new',      -- 'new'|'reviewing'|'closed'
    note                TEXT,
    UNIQUE (api_id, event_date, title, entity)   -- 멱등 (동일 이벤트 중복 적재 방지)
);
CREATE INDEX IF NOT EXISTS idx_event_status   ON event(status);
CREATE INDEX IF NOT EXISTS idx_event_severity ON event(severity);
CREATE INDEX IF NOT EXISTS idx_event_detected ON event(detected_at);

-- ────────────────────────────────────────────────────────────────────────
-- 알람 발송 로그 (dry-run 포함)
-- ────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS alert_log (
    alert_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id   INTEGER,
    team       TEXT,
    channel    TEXT,                      -- 채널 ID 또는 'DRY_RUN'
    sent_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    payload    JSON,
    FOREIGN KEY (event_id) REFERENCES event(event_id)
);
CREATE INDEX IF NOT EXISTS idx_alert_event ON alert_log(event_id);
