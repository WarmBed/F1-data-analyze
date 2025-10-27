"""
F1T Workspace Database Manager
管理 Workspace 的 SQLite 資料庫操作

版本: 1.0
創建日期: 2025-10-21
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path


class WorkspaceDatabase:
    """Workspace 資料庫管理器"""
    
    def __init__(self, db_path: str = "workspaces/workspaces.db"):
        """
        初始化資料庫連接
        
        Args:
            db_path: 資料庫檔案路徑
        """
        self.db_path = db_path
        self._ensure_database_directory()
        self.conn: Optional[sqlite3.Connection] = None
        self._init_database()
    
    def _ensure_database_directory(self):
        """確保資料庫目錄存在"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
            print(f"[WORKSPACE] 📁 已創建資料庫目錄: {db_dir}")
    
    def _init_database(self):
        """初始化資料庫連接和 schema"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # 允許按列名訪問
            print(f"[WORKSPACE] 🗄️ 已連接到資料庫: {self.db_path}")
            
            # 執行 schema 創建
            self._create_schema()
            
        except Exception as e:
            print(f"[WORKSPACE] ❌ 資料庫初始化失敗: {e}")
            raise
    
    def _create_schema(self):
        """創建資料庫 schema"""
        try:
            cursor = self.conn.cursor()
            
            # 讀取 schema 檔案
            schema_path = Path(__file__).parent / "workspace_db_schema.sql"
            if schema_path.exists():
                with open(schema_path, 'r', encoding='utf-8') as f:
                    schema_sql = f.read()
                
                # 執行 schema（分割多個語句）
                cursor.executescript(schema_sql)
                self.conn.commit()
                print(f"[WORKSPACE] ✅ 資料庫 schema 已創建")
            else:
                print(f"[WORKSPACE] ⚠️ 找不到 schema 檔案: {schema_path}")
                # 如果找不到檔案，創建基本 schema
                self._create_basic_schema(cursor)
                self.conn.commit()
                
        except Exception as e:
            print(f"[WORKSPACE] ❌ 創建 schema 失敗: {e}")
            raise
    
    def _create_basic_schema(self, cursor):
        """創建基本 schema（備用方案）"""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workspaces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed_at TIMESTAMP,
                active_tab_index INTEGER DEFAULT 0,
                config_json TEXT NOT NULL,
                total_tabs INTEGER DEFAULT 0,
                total_windows INTEGER DEFAULT 0,
                tags TEXT,
                version TEXT DEFAULT '1.0'
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workspace_window_types (
                workspace_id INTEGER NOT NULL,
                window_type TEXT NOT NULL,
                count INTEGER DEFAULT 1,
                PRIMARY KEY (workspace_id, window_type),
                FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workspace_parameters (
                workspace_id INTEGER NOT NULL,
                param_key TEXT NOT NULL,
                param_value TEXT NOT NULL,
                PRIMARY KEY (workspace_id, param_key, param_value),
                FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
            )
        """)
        
        print(f"[WORKSPACE] ✅ 已創建基本 schema")
    
    # ============================================================================
    # CRUD 操作：Create, Read, Update, Delete
    # ============================================================================
    
    def create_workspace(
        self,
        name: str,
        config_json: Dict,
        description: str = "",
        tags: str = "",
        active_tab_index: int = 0,
        total_tabs: int = 0,
        total_windows: int = 0
    ) -> int:
        """
        創建新 Workspace
        
        Args:
            name: Workspace 名稱
            config_json: 完整配置 JSON（字典格式）
            description: 描述
            tags: 標籤（逗號分隔）
            active_tab_index: 當前選中的分頁索引
            total_tabs: 總分頁數
            total_windows: 總視窗數
            
        Returns:
            新創建的 Workspace ID
        """
        try:
            cursor = self.conn.cursor()
            
            # 將 config_json 轉換為 JSON 字串
            config_str = json.dumps(config_json, ensure_ascii=False)
            
            cursor.execute("""
                INSERT INTO workspaces (
                    name, description, config_json, tags,
                    active_tab_index, total_tabs, total_windows
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (name, description, config_str, tags, active_tab_index, total_tabs, total_windows))
            
            workspace_id = cursor.lastrowid
            self.conn.commit()
            
            print(f"[WORKSPACE] ✅ 已創建 Workspace: {name} (ID: {workspace_id})")
            return workspace_id
            
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                print(f"[WORKSPACE] ⚠️ Workspace 名稱已存在: {name}")
                raise ValueError(f"Workspace '{name}' 已存在")
            raise
        except Exception as e:
            print(f"[WORKSPACE] ❌ 創建 Workspace 失敗: {e}")
            raise
    
    def get_workspace_by_id(self, workspace_id: int) -> Optional[Dict]:
        """
        根據 ID 獲取 Workspace
        
        Args:
            workspace_id: Workspace ID
            
        Returns:
            Workspace 資訊字典，如果不存在則返回 None
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM workspaces WHERE id = ?", (workspace_id,))
            row = cursor.fetchone()
            
            if row:
                workspace = dict(row)
                # 將 config_json 字串轉換回字典
                workspace['config_json'] = json.loads(workspace['config_json'])
                return workspace
            return None
            
        except Exception as e:
            print(f"[WORKSPACE] ❌ 獲取 Workspace 失敗: {e}")
            return None
    
    def get_workspace_by_name(self, name: str) -> Optional[Dict]:
        """
        根據名稱獲取 Workspace
        
        Args:
            name: Workspace 名稱
            
        Returns:
            Workspace 資訊字典，如果不存在則返回 None
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM workspaces WHERE name = ?", (name,))
            row = cursor.fetchone()
            
            if row:
                workspace = dict(row)
                workspace['config_json'] = json.loads(workspace['config_json'])
                return workspace
            return None
            
        except Exception as e:
            print(f"[WORKSPACE] ❌ 獲取 Workspace 失敗: {e}")
            return None
    
    def list_workspaces(
        self,
        order_by: str = "modified_at",
        ascending: bool = False,
        limit: int = None
    ) -> List[Dict]:
        """
        列出所有 Workspace
        
        Args:
            order_by: 排序欄位 ("modified_at", "last_accessed_at", "name", "created_at")
            ascending: 是否升序排列
            limit: 限制返回數量
            
        Returns:
            Workspace 列表（不包含完整 config_json，僅包含基本資訊）
        """
        try:
            cursor = self.conn.cursor()
            
            # 驗證排序欄位
            valid_order_fields = ["modified_at", "last_accessed_at", "name", "created_at"]
            if order_by not in valid_order_fields:
                order_by = "modified_at"
            
            # 構建查詢
            order_direction = "ASC" if ascending else "DESC"
            
            # 如果是 last_accessed_at，NULL 值放在最後
            if order_by == "last_accessed_at":
                order_clause = f"last_accessed_at {order_direction} NULLS LAST"
            else:
                order_clause = f"{order_by} {order_direction}"
            
            query = f"""
                SELECT 
                    id, name, description, created_at, modified_at, last_accessed_at,
                    total_tabs, total_windows, tags, version, config_json
                FROM workspaces
                ORDER BY {order_clause}
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            workspaces = [dict(row) for row in rows]
            print(f"[WORKSPACE] 📋 已列出 {len(workspaces)} 個 Workspace")
            return workspaces
            
        except Exception as e:
            print(f"[WORKSPACE] ❌ 列出 Workspace 失敗: {e}")
            return []
    
    def update_workspace(
        self,
        workspace_id: int,
        config_json: Dict = None,
        name: str = None,
        description: str = None,
        tags: str = None,
        active_tab_index: int = None,
        total_tabs: int = None,
        total_windows: int = None
    ) -> bool:
        """
        更新 Workspace
        
        Args:
            workspace_id: Workspace ID
            config_json: 新的配置 JSON（可選）
            name: 新名稱（可選）
            description: 新描述（可選）
            tags: 新標籤（可選）
            active_tab_index: 新的當前分頁索引（可選）
            total_tabs: 新的總分頁數（可選）
            total_windows: 新的總視窗數（可選）
            
        Returns:
            是否更新成功
        """
        try:
            cursor = self.conn.cursor()
            
            # 構建更新語句
            updates = []
            params = []
            
            if config_json is not None:
                updates.append("config_json = ?")
                params.append(json.dumps(config_json, ensure_ascii=False))
            
            if name is not None:
                updates.append("name = ?")
                params.append(name)
            
            if description is not None:
                updates.append("description = ?")
                params.append(description)
            
            if tags is not None:
                updates.append("tags = ?")
                params.append(tags)
            
            if active_tab_index is not None:
                updates.append("active_tab_index = ?")
                params.append(active_tab_index)
            
            if total_tabs is not None:
                updates.append("total_tabs = ?")
                params.append(total_tabs)
            
            if total_windows is not None:
                updates.append("total_windows = ?")
                params.append(total_windows)
            
            if not updates:
                print(f"[WORKSPACE] ⚠️ 沒有需要更新的欄位")
                return False
            
            # modified_at 會自動通過觸發器更新
            params.append(workspace_id)
            
            query = f"UPDATE workspaces SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            self.conn.commit()
            
            print(f"[WORKSPACE] ✅ 已更新 Workspace ID: {workspace_id}")
            return True
            
        except Exception as e:
            print(f"[WORKSPACE] ❌ 更新 Workspace 失敗: {e}")
            return False
    
    def delete_workspace(self, workspace_id: int) -> bool:
        """
        刪除 Workspace
        
        Args:
            workspace_id: Workspace ID
            
        Returns:
            是否刪除成功
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM workspaces WHERE id = ?", (workspace_id,))
            self.conn.commit()
            
            if cursor.rowcount > 0:
                print(f"[WORKSPACE] 🗑️ 已刪除 Workspace ID: {workspace_id}")
                return True
            else:
                print(f"[WORKSPACE] ⚠️ Workspace ID {workspace_id} 不存在")
                return False
            
        except Exception as e:
            print(f"[WORKSPACE] ❌ 刪除 Workspace 失敗: {e}")
            return False
    
    def update_last_accessed(self, workspace_id: int) -> bool:
        """
        更新 Workspace 的最後訪問時間
        
        Args:
            workspace_id: Workspace ID
            
        Returns:
            是否更新成功
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE workspaces 
                SET last_accessed_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (workspace_id,))
            self.conn.commit()
            
            return True
            
        except Exception as e:
            print(f"[WORKSPACE] ❌ 更新訪問時間失敗: {e}")
            return False
    
    # ============================================================================
    # 元數據管理：window_types 和 parameters
    # ============================================================================
    
    def set_window_types(self, workspace_id: int, window_types: Dict[str, int]):
        """
        設置 Workspace 的視窗類型統計
        
        Args:
            workspace_id: Workspace ID
            window_types: 視窗類型字典 {window_type: count}
        """
        try:
            cursor = self.conn.cursor()
            
            # 先刪除舊的記錄
            cursor.execute(
                "DELETE FROM workspace_window_types WHERE workspace_id = ?",
                (workspace_id,)
            )
            
            # 插入新記錄
            for window_type, count in window_types.items():
                cursor.execute("""
                    INSERT INTO workspace_window_types (workspace_id, window_type, count)
                    VALUES (?, ?, ?)
                """, (workspace_id, window_type, count))
            
            self.conn.commit()
            print(f"[WORKSPACE] 📊 已設置視窗類型統計: {len(window_types)} 種類型")
            
        except Exception as e:
            print(f"[WORKSPACE] ❌ 設置視窗類型失敗: {e}")
    
    def set_parameters(self, workspace_id: int, parameters: Dict[str, List[str]]):
        """
        設置 Workspace 的參數索引
        
        Args:
            workspace_id: Workspace ID
            parameters: 參數字典 {param_key: [param_values]}
        """
        try:
            cursor = self.conn.cursor()
            
            # 先刪除舊的記錄
            cursor.execute(
                "DELETE FROM workspace_parameters WHERE workspace_id = ?",
                (workspace_id,)
            )
            
            # 插入新記錄
            for param_key, param_values in parameters.items():
                for param_value in set(param_values):  # 去重
                    cursor.execute("""
                        INSERT INTO workspace_parameters (workspace_id, param_key, param_value)
                        VALUES (?, ?, ?)
                    """, (workspace_id, param_key, str(param_value)))
            
            self.conn.commit()
            print(f"[WORKSPACE] 📊 已設置參數索引: {len(parameters)} 個參數")
            
        except Exception as e:
            print(f"[WORKSPACE] ❌ 設置參數索引失敗: {e}")
    
    def get_recent_workspaces(self, limit: int = 10) -> List[Dict]:
        """
        獲取最近使用的 Workspace
        
        Args:
            limit: 返回數量
            
        Returns:
            最近使用的 Workspace 列表
        """
        return self.list_workspaces(order_by="last_accessed_at", limit=limit)
    
    def search_workspaces(
        self,
        keyword: str = None,
        window_type: str = None,
        param_filters: Dict[str, str] = None
    ) -> List[Dict]:
        """
        搜索 Workspace
        
        Args:
            keyword: 關鍵字（搜索名稱和描述）
            window_type: 視窗類型過濾
            param_filters: 參數過濾 {param_key: param_value}
            
        Returns:
            符合條件的 Workspace 列表
        """
        try:
            cursor = self.conn.cursor()
            
            query = """
                SELECT DISTINCT w.id, w.name, w.description, w.created_at, w.modified_at,
                       w.last_accessed_at, w.total_tabs, w.total_windows, w.tags, w.version
                FROM workspaces w
            """
            
            conditions = []
            params = []
            
            # 關鍵字搜索
            if keyword:
                query += " WHERE (w.name LIKE ? OR w.description LIKE ? OR w.tags LIKE ?)"
                keyword_pattern = f"%{keyword}%"
                params.extend([keyword_pattern, keyword_pattern, keyword_pattern])
            
            # 視窗類型過濾
            if window_type:
                query += " JOIN workspace_window_types wt ON w.id = wt.workspace_id"
                conditions.append("wt.window_type = ?")
                params.append(window_type)
            
            # 參數過濾
            if param_filters:
                for i, (param_key, param_value) in enumerate(param_filters.items()):
                    alias = f"wp{i}"
                    query += f" JOIN workspace_parameters {alias} ON w.id = {alias}.workspace_id"
                    conditions.append(f"{alias}.param_key = ? AND {alias}.param_value = ?")
                    params.extend([param_key, str(param_value)])
            
            # 組合條件
            if conditions:
                if keyword:
                    query += " AND " + " AND ".join(conditions)
                else:
                    query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY w.modified_at DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            workspaces = [dict(row) for row in rows]
            print(f"[WORKSPACE] 🔍 搜索到 {len(workspaces)} 個 Workspace")
            return workspaces
            
        except Exception as e:
            print(f"[WORKSPACE] ❌ 搜索 Workspace 失敗: {e}")
            return []
    
    # ============================================================================
    # 工具方法
    # ============================================================================
    
    def close(self):
        """關閉資料庫連接"""
        if self.conn:
            self.conn.close()
            print(f"[WORKSPACE] 🔒 資料庫連接已關閉")
    
    def __enter__(self):
        """支援 with 語句"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """支援 with 語句"""
        self.close()


# ============================================================================
# 測試代碼（僅在直接執行時運行）
# ============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("WorkspaceDatabase 測試")
    print("=" * 60)
    
    # 創建測試資料庫
    with WorkspaceDatabase("workspaces/test_workspaces.db") as db:
        # 測試 1: 創建 Workspace
        print("\n[測試 1] 創建 Workspace")
        config = {
            "version": "1.0",
            "active_tab_index": 1,
            "tabs": [
                {
                    "tab_index": 1,
                    "tab_name": "Tab 1",
                    "is_popped_out": False,
                    "mdi_windows": [
                        {
                            "window_type": "tire_strategy",
                            "parameters": {"year": 2025, "race": "United States", "session": "R"}
                        }
                    ]
                }
            ]
        }
        
        workspace_id = db.create_workspace(
            name="2025_USA_GP_Test",
            config_json=config,
            description="測試 Workspace",
            tags="2025,USA,測試",
            total_tabs=1,
            total_windows=1
        )
        
        # 測試 2: 設置元數據
        print("\n[測試 2] 設置元數據")
        db.set_window_types(workspace_id, {"tire_strategy": 1})
        db.set_parameters(workspace_id, {"year": ["2025"], "race": ["United States"], "session": ["R"]})
        
        # 測試 3: 獲取 Workspace
        print("\n[測試 3] 獲取 Workspace")
        workspace = db.get_workspace_by_id(workspace_id)
        print(f"獲取到 Workspace: {workspace['name']}")
        print(f"配置: {workspace['config_json']}")
        
        # 測試 4: 列出所有 Workspace
        print("\n[測試 4] 列出所有 Workspace")
        workspaces = db.list_workspaces()
        for ws in workspaces:
            print(f"  - {ws['name']} ({ws['total_tabs']} 分頁, {ws['total_windows']} 視窗)")
        
        # 測試 5: 搜索
        print("\n[測試 5] 搜索 Workspace")
        results = db.search_workspaces(keyword="USA")
        print(f"搜索結果: {len(results)} 個")
        
        print("\n" + "=" * 60)
        print("測試完成！")
        print("=" * 60)
