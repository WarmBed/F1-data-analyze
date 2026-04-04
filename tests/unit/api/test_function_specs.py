"""
測試 2: api/models/function_specs.py - 功能 ID 正規化
=======================================================
驗證 normalize_function_id() 和 function_id_sort_key() 的行為
符合文件所定義的規則。
"""
import pytest

from api.models.function_specs import normalize_function_id, function_id_sort_key, FunctionSpec


# ── normalize_function_id ────────────────────────────────────────────────────

class TestNormalizeFunctionId:
    """normalize_function_id() 必須將各種格式統一為標準字串。"""

    @pytest.mark.parametrize("raw, expected", [
        # 整數輸入
        (1, "1"),
        (6, "6"),
        (100, "100"),
        (143, "143"),
        # 帶前綴的字串
        ("F14", "14"),
        ("F14.2", "14.2"),
        ("function_3", "3"),
        ("function_03", "3"),
        ("func_100", "100"),
        ("Mode 6", "6"),
        ("id_52", "52"),
        # 純數字字串
        ("13", "13"),
        ("13.1", "13.1"),
        # 補零清除
        ("007", "7"),
        ("014.20", "14.2"),
        # 帶小數點
        ("6.1", "6.1"),
        ("120.1", "120.1"),
    ])
    def test_normalize_roundtrip(self, raw, expected):
        assert normalize_function_id(raw) == expected, (
            f"normalize_function_id({raw!r}) 應回傳 {expected!r}"
        )

    @pytest.mark.parametrize("invalid", [
        "",
        "   ",
        "abc",
        "no_number_here",
    ])
    def test_invalid_input_raises_value_error(self, invalid):
        with pytest.raises(ValueError):
            normalize_function_id(invalid)

    def test_none_raises_value_error(self):
        with pytest.raises(ValueError):
            normalize_function_id(None)

    def test_accepts_function_spec_instance(self):
        """也應接受 FunctionSpec 物件，讀取其 function_id 欄位。"""
        spec = FunctionSpec(
            function_id="13",
            name="Driver Comparison",
            description="Compare two drivers",
            required_params=["year", "race", "session", "driver1", "driver2"],
        )
        assert normalize_function_id(spec) == "13"


# ── function_id_sort_key ─────────────────────────────────────────────────────

class TestFunctionIdSortKey:
    """function_id_sort_key() 必須確保排序符合：14 < 14.1 < 14.2 < 15。"""

    def test_integer_ids_sort_numerically(self):
        ids = ["10", "2", "1", "100", "15"]
        sorted_ids = sorted(ids, key=function_id_sort_key)
        assert sorted_ids == ["1", "2", "10", "15", "100"]

    def test_sub_functions_sort_after_parent(self):
        ids = ["14", "14.2", "14.1", "15"]
        sorted_ids = sorted(ids, key=function_id_sort_key)
        assert sorted_ids == ["14", "14.1", "14.2", "15"]

    def test_mixed_int_and_sub_function_sort(self):
        ids = ["6.1", "6", "5", "7", "6.2"]
        sorted_ids = sorted(ids, key=function_id_sort_key)
        assert sorted_ids == ["5", "6", "6.1", "6.2", "7"]

    def test_returns_tuple_of_three_elements(self):
        key = function_id_sort_key("13")
        assert isinstance(key, tuple)
        assert len(key) == 3
        # (major: int, minor_parts: tuple, normalized: str)
        assert isinstance(key[0], int)
        assert isinstance(key[1], tuple)
        assert isinstance(key[2], str)


# ── FunctionSpec Dataclass ───────────────────────────────────────────────────

class TestFunctionSpec:
    """FunctionSpec 資料模型的基本完整性。"""

    def test_minimal_spec_creation(self):
        spec = FunctionSpec(
            function_id="1",
            name="Rain Intensity",
            description="Analyse rain intensity during race",
            required_params=["year", "race", "session"],
        )
        assert spec.function_id == "1"
        assert spec.name == "Rain Intensity"
        assert "year" in spec.required_params

    def test_spec_is_frozen(self):
        """FunctionSpec 必須是 frozen dataclass（不可變）。"""
        spec = FunctionSpec(
            function_id="1",
            name="Rain",
            description="test",
            required_params=[],
        )
        with pytest.raises((TypeError, AttributeError)):
            spec.function_id = "2"

    def test_optional_params_default_to_empty_list(self):
        spec = FunctionSpec(
            function_id="1",
            name="Test",
            description="desc",
            required_params=[],
        )
        assert spec.optional_params == []

    def test_cache_patterns_default_to_empty_list(self):
        spec = FunctionSpec(
            function_id="1",
            name="Test",
            description="desc",
            required_params=[],
        )
        assert spec.cache_patterns == []
