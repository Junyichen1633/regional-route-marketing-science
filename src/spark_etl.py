"""PySpark ETL layer for route-month analytical data preparation.

This module is intentionally upstream of the existing modeling scripts. It
builds a curated route-month Parquet dataset from the public and sourced inputs
already used by the project, then leaves modeling to the current Python stack.
"""

from __future__ import annotations

import os
from pathlib import Path

try:
    from pyspark.sql import DataFrame, SparkSession
    from pyspark.sql import functions as F
except ModuleNotFoundError as exc:  # pragma: no cover - exercised only without local dependency
    raise SystemExit(
        "PySpark is required to run this ETL module. "
        "Install project dependencies with: pip install -r requirements.txt"
    ) from exc


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = PROJECT_ROOT / "config"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
SPARK_OUTPUT_DIR = PROCESSED_DIR / "spark" / "route_month_curated"

INPUT_FILES = {
    "airports": CONFIG_DIR / "airports.csv",
    "route_month_skeleton": PROCESSED_DIR / "route_month_skeleton.csv",
    "screened_passengers": PROCESSED_DIR / "statcan_screened_monthly_passengers.csv",
    "annual_passengers": PROCESSED_DIR / "statcan_airport_annual_passengers.csv",
    "airport_movements": PROCESSED_DIR / "statcan_airport_monthly_movements.csv",
    "route_supply": PROCESSED_DIR / "route_supply_monthly_v0.csv",
}

MOVEMENT_FEATURES = [
    "domestic_total_itinerant_movements",
    "domestic_air_carrier_level_i_iii_movements",
    "domestic_air_carrier_level_iv_vi_movements",
    "domestic_air_carrier_all_levels_movements",
    "transborder_total_itinerant_movements",
    "other_international_total_itinerant_movements",
]

REQUIRED_KEYS = ["route_id", "period", "origin_iata", "destination_iata"]


def create_spark_session() -> SparkSession:
    builder = (
        SparkSession.builder.appName("regional-route-marketing-science-etl")
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.sql.sources.partitionOverwriteMode", "dynamic")
    )
    if not os.environ.get("SPARK_MASTER"):
        builder = builder.master("local[*]")
    return builder.getOrCreate()


def read_csv(spark: SparkSession, path: Path) -> DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing input file: {path.relative_to(PROJECT_ROOT)}")
    return (
        spark.read.option("header", "true")
        .option("mode", "FAILFAST")
        .option("nullValue", "")
        .option("emptyValue", "")
        .csv(str(path))
    )


def normalize_iata(column_name: str) -> F.Column:
    return F.upper(F.trim(F.col(column_name)))


def ratio_or_null(numerator: F.Column, denominator: F.Column) -> F.Column:
    return F.when(denominator.isNull() | (denominator == 0), F.lit(None)).otherwise(
        numerator / denominator
    )


def load_data(spark: SparkSession) -> dict[str, DataFrame]:
    return {name: read_csv(spark, path) for name, path in INPUT_FILES.items()}


def standardize_airports(airports: DataFrame) -> DataFrame:
    return (
        airports.withColumn("iata", normalize_iata("iata"))
        .select(
            "iata",
            F.col("name").alias("airport_name"),
            F.col("city").alias("airport_city"),
            F.col("province").alias("airport_province"),
            "airport_role",
        )
        .dropDuplicates(["iata"])
    )


def standardize_skeleton(skeleton: DataFrame) -> DataFrame:
    return (
        skeleton.withColumn("origin_iata", normalize_iata("origin_iata"))
        .withColumn("destination_iata", normalize_iata("destination_iata"))
        .withColumn("nearest_origin_hub_iata", normalize_iata("nearest_origin_hub_iata"))
        .withColumn(
            "route_id",
            F.coalesce(
                F.upper(F.trim(F.col("route_id"))),
                F.concat_ws("_", F.col("origin_iata"), F.col("destination_iata")),
            ),
        )
        .withColumn("period", F.to_date("month"))
        .withColumn("year", F.col("year").cast("int"))
        .withColumn("month_num", F.col("month_num").cast("int"))
        .withColumn("quarter", F.col("quarter").cast("int"))
        .withColumn("is_peak_travel_month", F.col("is_peak_travel_month").cast("int"))
        .withColumn("is_regional_origin", F.col("is_regional_origin").cast("int"))
        .withColumn("is_hub_destination", F.col("is_hub_destination").cast("int"))
        .withColumn("distance_km", F.col("distance_km").cast("double"))
        .withColumn(
            "nearest_origin_hub_distance_km",
            F.col("nearest_origin_hub_distance_km").cast("double"),
        )
        .drop("month")
    )


def standardize_monthly_passengers(passengers: DataFrame) -> DataFrame:
    return (
        passengers.filter(F.col("metric") == "total_screened_passengers")
        .withColumn("iata", normalize_iata("iata"))
        .withColumn("period", F.to_date("month"))
        .withColumn("monthly_screened_passengers", F.col("value").cast("long"))
        .groupBy("iata", "period")
        .agg(F.max("monthly_screened_passengers").alias("monthly_screened_passengers"))
    )


def standardize_annual_passengers(passengers: DataFrame) -> DataFrame:
    return (
        passengers.filter(F.col("metric") == "total_passengers_enplaned_deplaned")
        .withColumn("iata", normalize_iata("iata"))
        .withColumn("year", F.col("year").cast("int"))
        .withColumn("annual_passengers", F.col("value").cast("long"))
        .groupBy("iata", "year")
        .agg(F.max("annual_passengers").alias("annual_passengers"))
    )


def standardize_movements(movements: DataFrame) -> DataFrame:
    output = movements.withColumn("iata", normalize_iata("iata")).withColumn(
        "period", F.to_date("month")
    )
    for feature in MOVEMENT_FEATURES:
        output = output.withColumn(feature, F.col(feature).cast("long"))
    return output.select("iata", "period", *MOVEMENT_FEATURES).dropDuplicates(["iata", "period"])


def standardize_supply(supply: DataFrame) -> DataFrame:
    return (
        supply.withColumn("route_id", F.upper(F.trim(F.col("route_id"))))
        .withColumn("origin_iata", normalize_iata("origin_iata"))
        .withColumn("destination_iata", normalize_iata("destination_iata"))
        .withColumn("period", F.to_date("month"))
        .withColumn("route_active", F.col("route_active").cast("int"))
        .withColumn("direct_weekly_frequency_proxy", F.col("weekly_frequency_proxy").cast("double"))
        .withColumn("route_supply_event_count", F.col("route_supply_event_count").cast("int"))
        .withColumn("route_supply_confidence", F.coalesce(F.col("route_supply_confidence"), F.lit("uncovered")))
        .select(
            "route_id",
            "origin_iata",
            "destination_iata",
            "period",
            "route_active",
            "direct_weekly_frequency_proxy",
            "route_supply_confidence",
            F.coalesce(F.col("route_supply_event_count"), F.lit(0)).alias("route_supply_event_count"),
            "route_supply_event_ids",
            "route_supply_carriers",
            "route_supply_evidence_types",
        )
        .dropDuplicates(["route_id", "period"])
    )


def prefixed_airports(airports: DataFrame, key_column: str, prefix: str) -> DataFrame:
    return airports.select(
        F.col("iata").alias(key_column),
        F.col("airport_name").alias(f"{prefix}_airport_name"),
        F.col("airport_city").alias(f"{prefix}_airport_city"),
        F.col("airport_province").alias(f"{prefix}_airport_province"),
        F.col("airport_role").alias(f"{prefix}_airport_role"),
    )


def prefixed_passengers(passengers: DataFrame, key_column: str, prefix: str) -> DataFrame:
    return passengers.select(
        F.col("iata").alias(key_column),
        "period",
        F.col("monthly_screened_passengers").alias(f"{prefix}_monthly_screened_passengers"),
    )


def prefixed_annual_passengers(passengers: DataFrame, key_column: str, prefix: str) -> DataFrame:
    return passengers.select(
        F.col("iata").alias(key_column),
        "year",
        F.col("annual_passengers").alias(f"{prefix}_annual_passengers"),
    )


def prefixed_movements(movements: DataFrame, key_column: str, prefix: str) -> DataFrame:
    return movements.select(
        F.col("iata").alias(key_column),
        "period",
        *[F.col(feature).alias(f"{prefix}_{feature}") for feature in MOVEMENT_FEATURES],
    )


def join_sources(sources: dict[str, DataFrame]) -> DataFrame:
    skeleton = standardize_skeleton(sources["route_month_skeleton"])
    airports = standardize_airports(sources["airports"])
    monthly_passengers = standardize_monthly_passengers(sources["screened_passengers"])
    annual_passengers = standardize_annual_passengers(sources["annual_passengers"])
    movements = standardize_movements(sources["airport_movements"])
    supply = standardize_supply(sources["route_supply"])

    curated = (
        skeleton.join(prefixed_airports(airports, "origin_iata", "origin"), on="origin_iata", how="left")
        .join(prefixed_airports(airports, "destination_iata", "destination"), on="destination_iata", how="left")
        .join(prefixed_passengers(monthly_passengers, "origin_iata", "origin"), on=["origin_iata", "period"], how="left")
        .join(
            prefixed_passengers(monthly_passengers, "destination_iata", "destination"),
            on=["destination_iata", "period"],
            how="left",
        )
        .join(
            prefixed_passengers(monthly_passengers, "nearest_origin_hub_iata", "nearest_origin_hub"),
            on=["nearest_origin_hub_iata", "period"],
            how="left",
        )
        .join(prefixed_annual_passengers(annual_passengers, "origin_iata", "origin"), on=["origin_iata", "year"], how="left")
        .join(
            prefixed_annual_passengers(annual_passengers, "destination_iata", "destination"),
            on=["destination_iata", "year"],
            how="left",
        )
        .join(
            prefixed_annual_passengers(annual_passengers, "nearest_origin_hub_iata", "nearest_origin_hub"),
            on=["nearest_origin_hub_iata", "year"],
            how="left",
        )
        .join(prefixed_movements(movements, "origin_iata", "origin"), on=["origin_iata", "period"], how="left")
        .join(prefixed_movements(movements, "destination_iata", "destination"), on=["destination_iata", "period"], how="left")
        .join(
            prefixed_movements(movements, "nearest_origin_hub_iata", "nearest_origin_hub"),
            on=["nearest_origin_hub_iata", "period"],
            how="left",
        )
        .join(supply, on=["route_id", "origin_iata", "destination_iata", "period"], how="left")
    )
    return curated.dropDuplicates(["route_id", "period"])


def transform_data(curated: DataFrame) -> DataFrame:
    output = (
        curated.withColumn("route_month_key", F.concat_ws("__", F.col("route_id"), F.date_format("period", "yyyy-MM-dd")))
        .withColumn("supply_label_covered", F.when(F.col("route_active").isin(0, 1), F.lit(1)).otherwise(F.lit(0)))
        .withColumn("has_direct_frequency_proxy", F.when(F.col("direct_weekly_frequency_proxy").isNotNull(), F.lit(1)).otherwise(F.lit(0)))
        .withColumn(
            "has_origin_passenger_context",
            F.when(F.col("origin_monthly_screened_passengers").isNotNull(), F.lit(1)).otherwise(F.lit(0)),
        )
        .withColumn(
            "has_destination_passenger_context",
            F.when(F.col("destination_monthly_screened_passengers").isNotNull(), F.lit(1)).otherwise(F.lit(0)),
        )
        .withColumn(
            "destination_to_origin_screened_ratio",
            ratio_or_null(
                F.col("destination_monthly_screened_passengers").cast("double"),
                F.col("origin_monthly_screened_passengers").cast("double"),
            ),
        )
        .withColumn(
            "hub_to_origin_air_carrier_movement_ratio",
            ratio_or_null(
                F.col("nearest_origin_hub_domestic_air_carrier_all_levels_movements").cast("double"),
                F.col("origin_domestic_air_carrier_all_levels_movements").cast("double"),
            ),
        )
        .withColumn(
            "origin_destination_same_province",
            F.when(F.col("origin_province") == F.col("destination_province"), F.lit(1)).otherwise(F.lit(0)),
        )
        .fillna({"route_supply_confidence": "uncovered", "route_supply_event_count": 0})
    )

    selected_columns = [
        "route_month_key",
        "route_id",
        "period",
        "year",
        "month_num",
        "quarter",
        "season",
        "covid_period",
        "is_peak_travel_month",
        "origin_iata",
        "destination_iata",
        "nearest_origin_hub_iata",
        "origin_airport_name",
        "destination_airport_name",
        "origin_city",
        "destination_city",
        "origin_province",
        "destination_province",
        "origin_airport_role",
        "destination_airport_role",
        "route_group",
        "strategic_role",
        "status_assumption",
        "route_segment",
        "distance_km",
        "nearest_origin_hub_distance_km",
        "is_regional_origin",
        "is_hub_destination",
        "origin_monthly_screened_passengers",
        "destination_monthly_screened_passengers",
        "nearest_origin_hub_monthly_screened_passengers",
        "origin_annual_passengers",
        "destination_annual_passengers",
        "nearest_origin_hub_annual_passengers",
        "origin_domestic_air_carrier_all_levels_movements",
        "destination_domestic_air_carrier_all_levels_movements",
        "nearest_origin_hub_domestic_air_carrier_all_levels_movements",
        "destination_to_origin_screened_ratio",
        "hub_to_origin_air_carrier_movement_ratio",
        "origin_destination_same_province",
        "route_active",
        "direct_weekly_frequency_proxy",
        "route_supply_confidence",
        "route_supply_event_count",
        "route_supply_event_ids",
        "route_supply_carriers",
        "route_supply_evidence_types",
        "supply_label_covered",
        "has_direct_frequency_proxy",
        "has_origin_passenger_context",
        "has_destination_passenger_context",
    ]
    return output.select(*selected_columns)


def print_stage_count(label: str, df: DataFrame) -> None:
    print(f"[count] {label}: {df.count():,} rows")


def validate_required_keys(df: DataFrame) -> None:
    failures = []
    for field in REQUIRED_KEYS:
        missing = df.filter(F.col(field).isNull()).count()
        print(f"[quality] null {field}: {missing:,}")
        if missing:
            failures.append(f"{field} has {missing:,} null rows")
    if failures:
        raise ValueError("; ".join(failures))


def validate_route_time_uniqueness(df: DataFrame) -> None:
    duplicate_keys = df.groupBy("route_id", "period").count().filter(F.col("count") > 1).count()
    print(f"[quality] duplicate route-period keys: {duplicate_keys:,}")
    if duplicate_keys:
        raise ValueError("Curated dataset must be unique at route_id x period grain.")


def validate_route_identifiers(df: DataFrame) -> None:
    invalid = df.filter(~F.col("route_id").rlike(r"^[A-Z0-9]{3}_[A-Z0-9]{3}$")).count()
    print(f"[quality] invalid route_id format: {invalid:,}")
    if invalid:
        raise ValueError("Found invalid route identifiers.")


def validate_schema(df: DataFrame) -> None:
    expected_types = {
        "route_id": "string",
        "period": "date",
        "year": "int",
        "month_num": "int",
        "distance_km": "double",
        "route_active": "int",
        "direct_weekly_frequency_proxy": "double",
    }
    actual_types = dict(df.dtypes)
    mismatches = {
        column: (expected, actual_types.get(column))
        for column, expected in expected_types.items()
        if actual_types.get(column) != expected
    }
    print(f"[quality] schema checks: {len(expected_types) - len(mismatches)}/{len(expected_types)} passed")
    if mismatches:
        raise TypeError(f"Schema mismatches: {mismatches}")


def validate_numeric_sanity(df: DataFrame) -> None:
    non_negative_fields = [
        "distance_km",
        "nearest_origin_hub_distance_km",
        "origin_monthly_screened_passengers",
        "destination_monthly_screened_passengers",
        "origin_domestic_air_carrier_all_levels_movements",
        "destination_domestic_air_carrier_all_levels_movements",
        "direct_weekly_frequency_proxy",
    ]
    failures = []
    for field in non_negative_fields:
        bad_rows = df.filter(F.col(field) < 0).count()
        print(f"[quality] negative {field}: {bad_rows:,}")
        if bad_rows:
            failures.append(f"{field} has {bad_rows:,} negative rows")
    if failures:
        raise ValueError("; ".join(failures))


def validate_data(stages: dict[str, DataFrame], curated: DataFrame) -> None:
    for label, df in stages.items():
        print_stage_count(label, df)
    validate_required_keys(curated)
    validate_route_time_uniqueness(curated)
    validate_route_identifiers(curated)
    validate_schema(curated)
    validate_numeric_sanity(curated)
    coverage = curated.agg(
        F.avg("supply_label_covered").alias("supply_label_coverage"),
        F.avg("has_destination_passenger_context").alias("destination_passenger_context_coverage"),
    ).collect()[0]
    print(f"[quality] supply label coverage: {coverage['supply_label_coverage']:.1%}")
    print(
        "[quality] destination passenger context coverage: "
        f"{coverage['destination_passenger_context_coverage']:.1%}"
    )


def write_output(df: DataFrame, output_dir: Path = SPARK_OUTPUT_DIR) -> None:
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    (
        df.write.mode("overwrite")
        .partitionBy("year")
        .parquet(str(output_dir))
    )
    print(f"[write] curated Parquet dataset: {output_dir.relative_to(PROJECT_ROOT)}")


def load_curated_parquet_to_pandas(output_dir: Path = SPARK_OUTPUT_DIR):
    """Small bridge for existing Pandas-style model exploration."""
    import pandas as pd

    return pd.read_parquet(output_dir)


def main() -> None:
    spark = create_spark_session()
    try:
        sources = load_data(spark)
        joined = join_sources(sources)
        curated = transform_data(joined)
        validate_data({**sources, "joined_curated": joined, "final_curated": curated}, curated)
        write_output(curated)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
