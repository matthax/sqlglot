from tests.dialects.test_dialect import Validator


class TestClickhouse(Validator):
    dialect = "clickhouse"

    def test_clickhouse(self):
        self.validate_identity("SELECT INTERVAL t.days day")
        self.validate_identity("SELECT match('abc', '([a-z]+)')")
        self.validate_identity("dictGet(x, 'y')")
        self.validate_identity("SELECT * FROM x FINAL")
        self.validate_identity("SELECT * FROM x AS y FINAL")
        self.validate_identity("'a' IN mapKeys(map('a', 1, 'b', 2))")
        self.validate_identity("CAST((1, 2) AS Tuple(a Int8, b Int16))")
        self.validate_identity("SELECT * FROM foo LEFT ANY JOIN bla")
        self.validate_identity("SELECT * FROM foo LEFT ASOF JOIN bla")
        self.validate_identity("SELECT * FROM foo ASOF JOIN bla")
        self.validate_identity("SELECT * FROM foo ANY JOIN bla")
        self.validate_identity("SELECT quantile(0.5)(a)")
        self.validate_identity("SELECT quantiles(0.5)(a) AS x FROM t")
        self.validate_identity("SELECT quantiles(0.1, 0.2, 0.3)(a)")
        self.validate_identity("SELECT histogram(5)(a)")
        self.validate_identity("SELECT groupUniqArray(2)(a)")
        self.validate_identity("SELECT exponentialTimeDecayedAvg(60)(a, b)")
        self.validate_identity("SELECT * FROM foo WHERE x GLOBAL IN (SELECT * FROM bar)")
        self.validate_identity("position(haystack, needle)")
        self.validate_identity("position(haystack, needle, position)")

        self.validate_all(
            "SELECT fname, lname, age FROM person ORDER BY age DESC NULLS FIRST, fname ASC NULLS LAST, lname",
            write={
                "clickhouse": "SELECT fname, lname, age FROM person ORDER BY age DESC NULLS FIRST, fname, lname",
                "spark": "SELECT fname, lname, age FROM person ORDER BY age DESC NULLS FIRST, fname NULLS LAST, lname NULLS LAST",
            },
        )
        self.validate_all(
            "CAST(1 AS NULLABLE(Int64))",
            write={
                "clickhouse": "CAST(1 AS Nullable(Int64))",
            },
        )
        self.validate_all(
            "CAST(1 AS Nullable(DateTime64(6, 'UTC')))",
            write={
                "clickhouse": "CAST(1 AS Nullable(DateTime64(6, 'UTC')))",
            },
        )
        self.validate_all(
            "SELECT x #! comment",
            write={"": "SELECT x /* comment */"},
        )
        self.validate_all(
            "SELECT quantileIf(0.5)(a, true)",
            write={
                "clickhouse": "SELECT quantileIf(0.5)(a, TRUE)",
            },
        )
        self.validate_all(
            "SELECT position(needle IN haystack)",
            write={"clickhouse": "SELECT position(haystack, needle)"},
        )

    def test_cte(self):
        self.validate_identity("WITH 'x' AS foo SELECT foo")
        self.validate_identity("WITH SUM(bytes) AS foo SELECT foo FROM system.parts")
        self.validate_identity("WITH (SELECT foo) AS bar SELECT bar + 5")
        self.validate_identity("WITH test1 AS (SELECT i + 1, j + 1 FROM test1) SELECT * FROM test1")

    def test_signed_and_unsigned_types(self):
        data_types = [
            "UInt8",
            "UInt16",
            "UInt32",
            "UInt64",
            "UInt128",
            "UInt256",
            "Int8",
            "Int16",
            "Int32",
            "Int64",
            "Int128",
            "Int256",
        ]
        for data_type in data_types:
            self.validate_all(
                f"pow(2, 32)::{data_type}",
                write={"clickhouse": f"CAST(POWER(2, 32) AS {data_type})"},
            )

    def test_parameterization(self):
        # Ensure we support parameterization within the select clause
        self.validate_all(
            "SELECT {abc: UInt32}, {b: String}, {c: DateTime},{d: Map(String, Array(UInt8))}, {e: Tuple(UInt8, String)}",
            write={
                "clickhouse": "SELECT {abc: UInt32}, {b: TEXT}, {c: DateTime64}, {d: Map(TEXT, Array(UInt8))}, {e: Tuple(UInt8, String)}",
                "": "SELECT :abc, :b, :c, :d, :e",
            },
        )
        # Ensure we support parameterization for "Identity" parameters including those that can be used in a FROM clause
        self.validate_all(
            "SELECT * FROM {table: Identifier}",
            write={"clickhouse": "SELECT * FROM {table: Identifier}"},
        )
