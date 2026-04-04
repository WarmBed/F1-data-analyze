"""
測試 4: CLI_modules/cli/core/function_mapper.py - 功能映射器
=============================================================
驗證 F1AnalysisFunctionMapper 的結構完整性：
- function_mapping 包含預期的功能 ID 範圍
- sub_function_mapping 包含預期的子功能
- _standardize_result() 統一格式化輸出
- execute_function_by_number() 對無效 ID 回傳正確錯誤格式

注意：不載入實際 F1 數據，只測試結構與邏輯層。
"""
import pytest
from CLI_modules.cli.core.function_mapper import F1AnalysisFunctionMapper


# ── 類別初始化 ───────────────────────────────────────────────────────────────

class TestFunctionMapperInit:
    """F1AnalysisFunctionMapper 可在無資料載入器的情況下初始化。"""

    def test_can_create_without_args(self):
        """不帶任何參數應可成功建立實例。"""
        mapper = F1AnalysisFunctionMapper()
        assert mapper is not None

    def test_default_driver_is_ver(self):
        """預設主要車手應為 VER。"""
        mapper = F1AnalysisFunctionMapper()
        assert mapper.driver == "VER"

    def test_default_driver2_is_lec(self):
        """預設次要車手應為 LEC。"""
        mapper = F1AnalysisFunctionMapper()
        assert mapper.driver2 == "LEC"

    def test_data_loader_is_none_by_default(self):
        """預設 data_loader 應為 None。"""
        mapper = F1AnalysisFunctionMapper()
        assert mapper.data_loader is None


# ── function_mapping 結構驗證 ────────────────────────────────────────────────

class TestFunctionMappingStructure:
    """function_mapping 字典的結構完整性。"""

    @pytest.fixture(scope="class")
    def mapper(self):
        return F1AnalysisFunctionMapper()

    def test_function_mapping_is_dict(self, mapper):
        """function_mapping 必須是字典。"""
        assert isinstance(mapper.function_mapping, dict)

    def test_function_mapping_is_non_empty(self, mapper):
        """function_mapping 不得為空。"""
        assert len(mapper.function_mapping) > 0

    def test_function_mapping_has_at_least_50_entries(self, mapper):
        """function_mapping 至少應有 50 個功能。"""
        assert len(mapper.function_mapping) >= 50

    @pytest.mark.parametrize("fid", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    def test_basic_function_ids_1_to_10_exist(self, mapper, fid: int):
        """功能 ID 1-10（基礎分析）必須存在。"""
        assert fid in mapper.function_mapping, f"功能 {fid} 不在 function_mapping 中"

    @pytest.mark.parametrize("fid", [11, 12, 13, 15, 16, 17, 18])
    def test_advanced_function_ids_exist(self, mapper, fid: int):
        """進階分析功能 ID 應存在。"""
        assert fid in mapper.function_mapping, f"功能 {fid} 不在 function_mapping 中"

    def test_all_mapping_values_are_callable(self, mapper):
        """function_mapping 的所有值必須是可呼叫的（方法）。"""
        for fid, func in mapper.function_mapping.items():
            assert callable(func), f"功能 {fid} 的值 {func!r} 不是可呼叫的"


# ── sub_function_mapping 結構驗證 ────────────────────────────────────────────

class TestSubFunctionMappingStructure:
    """sub_function_mapping 字典的結構完整性。"""

    @pytest.fixture(scope="class")
    def mapper(self):
        return F1AnalysisFunctionMapper()

    def test_sub_function_mapping_is_dict(self, mapper):
        """sub_function_mapping 必須是字典。"""
        assert isinstance(mapper.sub_function_mapping, dict)

    def test_sub_function_mapping_is_non_empty(self, mapper):
        """sub_function_mapping 不得為空。"""
        assert len(mapper.sub_function_mapping) > 0

    @pytest.mark.parametrize("sub_id", ["4.1", "4.2", "6.1", "6.2", "7.1"])
    def test_known_sub_function_ids_exist(self, mapper, sub_id: str):
        """已知的子功能 ID 必須存在。"""
        assert sub_id in mapper.sub_function_mapping, f"子功能 {sub_id!r} 不在映射中"

    def test_all_sub_mapping_values_are_callable(self, mapper):
        """sub_function_mapping 的所有值必須是可呼叫的。"""
        for sub_id, func in mapper.sub_function_mapping.items():
            assert callable(func), f"子功能 {sub_id} 的值不是可呼叫的"


# ── _standardize_result 格式化邏輯 ───────────────────────────────────────────

class TestStandardizeResult:
    """_standardize_result() 必須統一所有輸出格式。"""

    @pytest.fixture(scope="class")
    def mapper(self):
        return F1AnalysisFunctionMapper()

    def test_none_result_returns_failure(self, mapper):
        """傳入 None 應回傳 success=False。"""
        result = mapper._standardize_result(None, function_id=1, function_name="Test")
        assert result["success"] is False

    def test_none_result_contains_function_id(self, mapper):
        """None 結果應包含 function_id 欄位。"""
        result = mapper._standardize_result(None, function_id=5, function_name="Test")
        assert result["function_id"] == "5"

    def test_standard_dict_preserved(self, mapper):
        """已是標準格式的 dict 應保留原有的 success 值。"""
        input_result = {"success": True, "data": {"key": "val"}, "message": "OK"}
        result = mapper._standardize_result(input_result, function_id=2)
        assert result["success"] is True
        assert result["data"] == {"key": "val"}

    def test_non_dict_result_wrapped(self, mapper):
        """非 dict 結果應被包裝為標準格式且 success=True。"""
        result = mapper._standardize_result("some string result", function_id=3)
        assert result["success"] is True
        assert result["data"] == "some string result"
        assert "function_id" in result

    def test_result_always_has_required_keys(self, mapper):
        """標準化結果必須包含所有必要欄位。"""
        result = mapper._standardize_result({"success": True}, function_id=10)
        for key in ("success", "function_id", "message", "data"):
            assert key in result, f"缺少必要欄位: {key}"
