-- ============================================================================
-- F1T Workspace Manager - Database Schema
-- 版本: 1.0
-- 創建日期: 2025-10-21
-- 描述: Workspace 管理系統的 SQLite 資料庫結構
-- ============================================================================

-- ============================================================================
-- 主表：workspaces
-- 功能：存儲所有 Workspace 的基本資訊和完整配置
-- ============================================================================
CREATE TABLE IF NOT EXISTS workspaces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,              -- Workspace 名稱（唯一）
    description TEXT,                        -- 描述（可選）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 創建時間
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- 最後修改時間
    last_accessed_at TIMESTAMP,              -- 最後訪問時間（用於「最近使用」）
    active_tab_index INTEGER DEFAULT 0,     -- 當前選中的分頁索引
    
    -- 完整配置 JSON（用於快速載入整個 Workspace）
    config_json TEXT NOT NULL,
    
    -- 統計資訊（冗餘，用於快速顯示列表）
    total_tabs INTEGER DEFAULT 0,           -- 總分頁數（排除 HOME）
    total_windows INTEGER DEFAULT 0,        -- 總 MDI 視窗數
    
    -- 標籤（用於分類和過濾）
    tags TEXT,                               -- 逗號分隔的標籤，例如 "2025,USA,輪胎分析"
    
    -- 版本號（用於未來升級和相容性檢查）
    version TEXT DEFAULT '1.0',
    
    -- 約束
    CHECK(total_tabs >= 0),
    CHECK(total_windows >= 0)
);

-- ============================================================================
-- 元數據表：workspace_window_types
-- 功能：記錄每個 Workspace 包含的視窗類型及數量
-- 用途：快速搜索和過濾（例如：找出所有包含 Rain Analysis 的 Workspace）
-- ============================================================================
CREATE TABLE IF NOT EXISTS workspace_window_types (
    workspace_id INTEGER NOT NULL,
    window_type TEXT NOT NULL,              -- 視窗類型，例如 "tire_strategy"
    count INTEGER DEFAULT 1,                 -- 該類型視窗的數量
    
    PRIMARY KEY (workspace_id, window_type),
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
);

-- ============================================================================
-- 元數據表：workspace_parameters
-- 功能：記錄 Workspace 中使用的參數（年份、賽事、會話）
-- 用途：搜索特定賽事的分析（例如：找出所有分析 2025 USA GP 的 Workspace）
-- ============================================================================
CREATE TABLE IF NOT EXISTS workspace_parameters (
    workspace_id INTEGER NOT NULL,
    param_key TEXT NOT NULL,                -- 參數鍵，例如 "year", "race", "session"
    param_value TEXT NOT NULL,              -- 參數值，例如 "2025", "United States", "R"
    
    PRIMARY KEY (workspace_id, param_key, param_value),
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
);

-- ============================================================================
-- 索引：加速查詢
-- ============================================================================

-- 索引 1: 最近訪問時間（降序）- 用於「最近使用」列表
CREATE INDEX IF NOT EXISTS idx_workspaces_accessed 
ON workspaces(last_accessed_at DESC);

-- 索引 2: 修改時間（降序）- 用於排序
CREATE INDEX IF NOT EXISTS idx_workspaces_modified 
ON workspaces(modified_at DESC);

-- 索引 3: 視窗類型 - 用於過濾
CREATE INDEX IF NOT EXISTS idx_window_types 
ON workspace_window_types(window_type);

-- 索引 4: 參數搜索 - 用於找出特定賽事/年份
CREATE INDEX IF NOT EXISTS idx_parameters_key 
ON workspace_parameters(param_key, param_value);

-- ============================================================================
-- 觸發器：自動更新 modified_at
-- ============================================================================
CREATE TRIGGER IF NOT EXISTS update_workspace_modified_at
AFTER UPDATE ON workspaces
FOR EACH ROW
BEGIN
    UPDATE workspaces 
    SET modified_at = CURRENT_TIMESTAMP 
    WHERE id = OLD.id;
END;

-- ============================================================================
-- 示例數據（用於測試）
-- ============================================================================
-- INSERT INTO workspaces (name, description, config_json, total_tabs, total_windows, tags)
-- VALUES (
--     '2025_USA_GP_Analysis',
--     '2025 美國 GP 完整分析，包含輪胎策略、天氣分析、進站策略',
--     '{"active_tab_index":1,"tabs":[...]}',  -- 完整 JSON 省略
--     3,
--     8,
--     '2025,USA,輪胎,天氣'
-- );

-- ============================================================================
-- 查詢示例
-- ============================================================================

-- 1. 獲取所有 Workspace（按最近訪問排序）
-- SELECT id, name, description, total_tabs, total_windows, last_accessed_at
-- FROM workspaces
-- ORDER BY last_accessed_at DESC NULLS LAST
-- LIMIT 10;

-- 2. 搜索包含特定視窗類型的 Workspace
-- SELECT DISTINCT w.id, w.name, w.description
-- FROM workspaces w
-- JOIN workspace_window_types wt ON w.id = wt.workspace_id
-- WHERE wt.window_type = 'rain_analysis';

-- 3. 搜索特定賽事的 Workspace
-- SELECT DISTINCT w.id, w.name, w.description
-- FROM workspaces w
-- JOIN workspace_parameters wp ON w.id = wp.workspace_id
-- WHERE wp.param_key = 'race' AND wp.param_value = 'United States'
--   AND EXISTS (
--       SELECT 1 FROM workspace_parameters wp2
--       WHERE wp2.workspace_id = w.id
--         AND wp2.param_key = 'year' AND wp2.param_value = '2025'
--   );

-- 4. 統計視窗類型使用情況
-- SELECT window_type, SUM(count) as total_count
-- FROM workspace_window_types
-- GROUP BY window_type
-- ORDER BY total_count DESC;
