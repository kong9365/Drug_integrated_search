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
    item_code    TEXT,
    ingr_name    TEXT,      -- 주성분명 (MTRAL_NM)
    ingr_code    TEXT,      -- MTRAL_CODE
    qty          TEXT,      -- 분량 (QNT)
    unit         TEXT,      -- 단위
    -- 9탭 원약분량 컬럼 설계 이관 (product_ingredient → master_ingredient; db.py _ensure_column 멱등)
    purpose      TEXT,      -- 배합목적 (주성분/활택제/부형제)
    spec         TEXT,      -- 규격 (KP/JP/NF)
    permit_qty   TEXT,      -- 허가량
    stm_spec     TEXT,      -- STM규격
    stm_storage  TEXT,      -- STM보관조건
    stm_shelf    TEXT,      -- STM사용기간
    manufacturer TEXT,      -- 제조처
    supplier     TEXT,      -- 공급처
    section      TEXT,      -- 구분 (속방부/서방부)
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
    is_mock             INTEGER DEFAULT 0,       -- 1=테스트/데모용 mock (UI에 [MOCK] 표시, 실데이터와 분리)
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

-- ════════════════════════════════════════════════════════════════════════
-- 품목마스터 9탭 정형화 (Phase M-재정렬) — master_item(880, item_code)이 유일 SSOT
--   product_master(item_seq) 레이어는 폐기. 9탭 컬럼 설계는 master_* 자식으로 이관:
--     · 원약분량 → master_ingredient (컬럼 확장: db.py _ensure_column 마이그레이션)
--     · 포장     → master_packaging (아래 신규)
--     · 규제이벤트 → 기존 event 테이블 흡수 (matched_item_codes JSON, lookup.events_for_item)
-- ════════════════════════════════════════════════════════════════════════

-- product_master(item_seq) 레이어 폐기 — 이전 M-1 빌드의 잔존 테이블 제거 (멱등)
-- ※ FK ON 상태이므로 자식(FK 보유)부터 DROP 후 부모(product_master) DROP
DROP TABLE IF EXISTS product_reg_event;
DROP TABLE IF EXISTS product_ingredient;
DROP TABLE IF EXISTS product_packaging;
DROP TABLE IF EXISTS product_master;

-- 포장 (포장단위 + 포장자재 탭) — item_code FK
CREATE TABLE IF NOT EXISTS master_packaging (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    item_code       TEXT NOT NULL,
    pkg_type        TEXT,               -- 병(HDPE)/PTP 등
    spec_dom        TEXT,               -- 규격(내수용)
    spec_exp        TEXT,               -- 규격(수출용)
    production_yn   TEXT,               -- 생산여부
    FOREIGN KEY (item_code) REFERENCES master_item(item_code)
);
CREATE INDEX IF NOT EXISTS idx_mpkg_item ON master_packaging(item_code);

-- ════════════════════════════════════════════════════════════════════════
-- 광동 허가 백본 (Phase HYB — 공공 기준 역방향)
--   식약처 NO140을 entp_name='광동제약' 으로 통째 조회한 "허가 사실" 미러.
--   master_item(사내 880)이 내부정보 오버레이, official_approval(공공 N)이 허가 SSOT.
--   "수동 업데이트" 클릭 시 재조회 → upsert + 사내 재링크.
-- ════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS official_approval (
    item_seq        TEXT PRIMARY KEY,   -- 식약처 품목기준코드 (ITEM_SEQ)
    item_name       TEXT NOT NULL,
    entp_name       TEXT,               -- 허가권자 (광동제약(주) 등)
    permit_no       TEXT,               -- 허가번호 (PRDUCT_PRMISN_NO)
    permit_date     TEXT,               -- 허가일 (ITEM_PERMIT_DATE)
    cancel_date     TEXT,               -- 취하/취소일
    cancel_name     TEXT,               -- 취소 사유/상태 (정상/취하 등)
    reexam_date     TEXT,               -- 재심사 기한
    atc_code        TEXT,
    edi_code        TEXT,
    bar_code        TEXT,
    chart           TEXT,               -- 성상
    storage_method  TEXT,
    material_name   TEXT,               -- 주성분 상세 원문
    etc_otc         TEXT,               -- 전문/일반 구분
    norm_name       TEXT,               -- 정규화 품목명 (사내 재링크용 로컬 매칭 키)
    synced_at       TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_oa_norm ON official_approval(norm_name);
CREATE INDEX IF NOT EXISTS idx_oa_entp ON official_approval(entp_name);

-- SAP/EDMS 연동 대기 테이블 (Phase M-4 스텁 — item_code 키, 빈 상태)
CREATE TABLE IF NOT EXISTS product_batch (        -- SAP 연동 예정
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_code TEXT, lot_no TEXT, mfg_date TEXT,
    test_result TEXT, oos_yn INTEGER DEFAULT 0,
    source TEXT DEFAULT 'SAP_PENDING'
);
CREATE TABLE IF NOT EXISTS product_document (      -- EDMS 연동 예정
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_code TEXT, doc_type TEXT, doc_no TEXT,
    title TEXT, source TEXT DEFAULT 'EDMS_PENDING'
);
