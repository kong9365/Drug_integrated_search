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
-- 품목마스터 중심 재설계 (Phase M-1) — item_seq 기준 정형화 마스터
--   기존 master_item(item_code, xlsx 880품목)은 그대로 두고,
--   스크린샷 9탭 구조를 품목기준코드(item_seq) 단위로 정형화한 신규 레이어.
--   APQR(연간품질평가)의 1차 데이터 소스.
-- ════════════════════════════════════════════════════════════════════════

-- 품목 기본 + 허가정보 (스크린샷 헤더 영역)
CREATE TABLE IF NOT EXISTS product_master (
    item_seq        TEXT PRIMARY KEY,   -- 품목기준코드 (예: 199401695)
    product_name    TEXT NOT NULL,      -- 제품명 (베니톨정)
    appearance      TEXT,               -- 성상
    form_type       TEXT,               -- 제형구분
    etc_otc         TEXT,               -- 의약품구분 (전문/일반)
    permit_type     TEXT,               -- 허가/신고
    permit_date     TEXT,               -- 허가일자
    permit_holder   TEXT,               -- 허가권자 (광동제약)
    permit_no       TEXT,               -- 허가번호
    consign_yn      TEXT,               -- 위수탁여부
    make_import     TEXT,               -- 제조/수입
    storage_temp    TEXT,               -- 보관조건(온도)
    shelf_life_dom  TEXT,               -- 사용기간(내수)
    shelf_life_exp  TEXT,               -- 사용기간(수출)
    storage_cont    TEXT,               -- 저장용기
    is_self         INTEGER DEFAULT 1,  -- 공정(자사) 여부
    remark          TEXT,               -- 비고
    make_unit       TEXT,               -- 제조단위
    edi_code        TEXT,               -- 보험코드
    atc_code        TEXT,               -- ATC 코드
    reexam_date     TEXT,               -- 재심사 기한일 (REEXAM_DATE)
    material_name   TEXT,               -- 주성분 상세 원문 (MATERIAL_NAME)
    pill_image_url  TEXT,               -- 낱알 이미지 (NO 563)
    enrich_status   TEXT DEFAULT 'pending',  -- pending|matched|unmatched
    enriched_at     TEXT,               -- 규제 API enrich 시각
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT
);

-- 원약분량 (원약분량 탭 — 원료별 1:N)
CREATE TABLE IF NOT EXISTS product_ingredient (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    item_seq        TEXT NOT NULL,
    ingr_name       TEXT,               -- 원료명
    ingr_code       TEXT,               -- 원료신코드
    purpose         TEXT,               -- 배합목적 (주성분/활택제/부형제)
    spec            TEXT,               -- 규격 (KP/JP/NF)
    permit_qty      TEXT,               -- 허가량
    unit            TEXT,               -- 단위
    stm_spec        TEXT,               -- STM규격
    stm_storage     TEXT,               -- STM보관조건
    stm_shelf       TEXT,               -- STM사용기간
    manufacturer    TEXT,               -- 제조처
    supplier        TEXT,               -- 공급처
    section         TEXT,               -- 구분 (속방부/서방부)
    FOREIGN KEY (item_seq) REFERENCES product_master(item_seq)
);
CREATE INDEX IF NOT EXISTS idx_ping_item ON product_ingredient(item_seq);

-- 포장 (포장단위 + 포장자재 탭)
CREATE TABLE IF NOT EXISTS product_packaging (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    item_seq        TEXT NOT NULL,
    pkg_type        TEXT,               -- 병(HDPE)/PTP 등
    spec_dom        TEXT,               -- 규격(내수용)
    spec_exp        TEXT,               -- 규격(수출용)
    production_yn   TEXT,               -- 생산여부
    FOREIGN KEY (item_seq) REFERENCES product_master(item_seq)
);
CREATE INDEX IF NOT EXISTS idx_ppkg_item ON product_packaging(item_seq);

-- 규제 이벤트 로그 (품목별 연중 누적 → APQR 핵심 소스)
CREATE TABLE IF NOT EXISTS product_reg_event (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    item_seq        TEXT NOT NULL,
    event_type      TEXT,               -- recall/disciplinary/safety_letter/review_due/reeval_done/permit_change/supplier_closure
    severity        TEXT,               -- CRITICAL/HIGH/LOW
    title           TEXT,
    summary         TEXT,
    event_date      TEXT,
    source_api      TEXT,               -- 내부 추적용 (화면 노출 X)
    detected_at     TEXT DEFAULT (datetime('now')),
    acknowledged    INTEGER DEFAULT 0,
    UNIQUE (item_seq, event_type, event_date, title),  -- 멱등 (중복 적재 방지)
    FOREIGN KEY (item_seq) REFERENCES product_master(item_seq)
);
CREATE INDEX IF NOT EXISTS idx_preg_item ON product_reg_event(item_seq);
CREATE INDEX IF NOT EXISTS idx_preg_ack  ON product_reg_event(acknowledged);

-- SAP/EDMS 연동 대기 테이블 (Phase M-4 스텁 — 스키마만 정의, 데이터 미적재)
CREATE TABLE IF NOT EXISTS product_batch (        -- SAP 연동 예정
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_seq TEXT, lot_no TEXT, mfg_date TEXT,
    test_result TEXT, oos_yn INTEGER DEFAULT 0,
    source TEXT DEFAULT 'SAP_PENDING'
);
CREATE TABLE IF NOT EXISTS product_document (      -- EDMS 연동 예정
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_seq TEXT, doc_type TEXT, doc_no TEXT,
    title TEXT, source TEXT DEFAULT 'EDMS_PENDING'
);
