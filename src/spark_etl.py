"""Consolidated PySpark builder for the route-month analytical panel.

The legacy project keeps small standard-library scripts for each upstream step:
route-month skeleton, passenger context, movement context, and route-supply
context. This module implements the same data-preparation layer in Spark while
leaving the downstream marketing science workflow unchanged.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

try:
    from pyspark.sql import DataFrame, SparkSession, Window
    from pyspark.sql import functions as F
except ModuleNotFoundError as exc:  # pragma: no cover - exercised only without local dependency
    raise SystemExit(
        "PySpark is required to run this ETL module. "
        "Install project dependencies with: pip install -r requirements.txt"
    ) from exc


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = PROJECT_ROOT / "config"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
SPARK_DIR = PROCESSED_DIR / "spark"

START_YEAR = 2020
END_YEAR = 2025

LEGACY_PANEL_FILE = PROCESSED_DIR / "route_month_panel_v2.csv"
SPARK_PANEL_PARQUET_DIR = SPARK_DIR / "route_month_panel_v2.parquet"
SPARK_PANEL_CSV_FILE = SPARK_DIR / "route_month_panel_v2.csv"

INPUT_FILES = {
    "airports": CONFIG_DIR / "airports.csv",
    "seed_routes": CONFIG_DIR / "seed_routes.csv",
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

PANEL_COLUMNS = [
    "route_id",
    "origin_iata",
    "destination_iata",
    "origin_city",
    "destination_city",
    "origin_province",
    "destination_province",
    "month",
    "year",
    "month_num",
    "quarter",
    "season",
    "covid_period",
    "is_peak_travel_month",
    "route_group",
    "strategic_role",
    "status_assumption",
    "is_regional_origin",
    "is_hub_destination",
    "distance_km",
    "route_segment",
    "nearest_origin_hub_iata",
    "nearest_origin_hub_distance_km",
    "notes",
    "origin_monthly_screened_passengers",
    "destination_monthly_screened_passengers",
    "nearest_origin_hub_monthly_screened_passengers",
    "origin_annual_passengers",
    "destination_annual_passengers",
    "nearest_origin_hub_annual_passengers",
    "observed_route_passengers",
    "flight_frequency_proxy",
    "route_active",
    "simulated_marketing_spend",
    "origin_domestic_total_itinerant_movements",
    "origin_domestic_air_carrier_level_i_iii_movements",
    "origin_domestic_air_carrier_level_iv_vi_movements",
    "origin_domestic_air_carrier_all_levels_movements",
    "origin_transborder_total_itinerant_movements",
    "origin_other_international_total_itinerant_movements",
    "destination_domestic_total_itinerant_movements",
    "destination_domestic_air_carrier_level_i_iii_movements",
    "destination_domestic_air_carrier_level_iv_vi_movements",
    "destination_domestic_air_carrier_all_levels_movements",
    "destination_transborder_total_itinerant_movements",
    "destination_other_international_total_itinerant_movements",
    "nearest_origin_hub_domestic_total_itinerant_movements",
    "nearest_origin_hub_domestic_air_carrier_level_i_iii_movements",
    "nearest_origin_hub_domestic_air_carrier_level_iv_vi_movements",
    "nearest_origin_hub_domestic_air_carrier_all_levels_movements",
    "nearest_origin_hub_transborder_total_itinerant_movements",
    "nearest_origin_hub_other_international_total_itinerant_movements",
    "direct_weekly_frequency_proxy",
    "route_supply_confidence",
    "route_supply_event_count",
    "route_supply_event_ids",
    "route_supply_carriers",
    "route_supply_evidence_types",
    "route_supply_source_titles",
    "route_supply_source_urls",
]

REQUIRED_COLUMNS = ["route_id", "origin_iata", "destination_iata", "month"]
LEGACY_COMPARE_FIELDS = [
    "origin_monthly_screened_passengers",
    "destination_monthly_screened_passengers",
    "nearest_origin_hub_monthly_screened_passengers",
    "origin_domestic_air_carrier_all_levels_movements",
    "destination_domestic_air_carrier_all_levels_movements",
    "nearest_origin_hub_domestic_air_carrier_all_levels_movements",
    "route_active",
    "direct_weekly_frequency_proxy",
    "route_supply_confidence",
    "route_supply_event_count",
]


def create_spark_session() -> SparkSession:
    builder = (
        SparkSession.builder.appName("regional-route-marketing-science-panel-etl")
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


def load_data(spark: SparkSession) -> dict[str, DataFrame]:
    return {name: read_csv(spark, path) for name, path in INPUT_FILES.items()}


def standardize_airports(airports: DataFrame) -> DataFrame:
    return (
        airports.withColumn("iata", normalize_iata("iata"))
        .withColumn("latitude", F.col("latitude").cast("double"))
        .withColumn("longitude", F.col("longitude").cast("double"))
        .select(
            "iata",
            "icao",
            "name",
            "city",
            "province",
            "country",
            "latitude",
            "longitude",
            "airport_role",
            "notes",
        )
        .dropDuplicates(["iata"])
    )


def standardize_routes(routes: DataFrame) -> DataFrame:
    return (
        routes.withColumn("origin_iata", normalize_iata("origin_iata"))
        .withColumn("destination_iata", normalize_iata("destination_iata"))
        .withColumn(
            "route_id",
            F.coalesce(
                F.upper(F.trim(F.col("route_id"))),
                F.concat_ws("_", F.col("origin_iata"), F.col("destination_iata")),
            ),
        )
        .select(
            "route_id",
            "origin_iata",
            "destination_iata",
            "route_group",
            "strategic_role",
            "status_assumption",
            "notes",
        )
    )


def haversine_km(lat1: F.Column, lon1: F.Column, lat2: F.Column, lon2: F.Column) -> F.Column:
    radius_km = F.lit(6371.0088)
    phi1 = F.radians(lat1)
    phi2 = F.radians(lat2)
    delta_phi = F.radians(lat2 - lat1)
    delta_lambda = F.radians(lon2 - lon1)
    a = F.pow(F.sin(delta_phi / F.lit(2.0)), 2) + (
        F.cos(phi1) * F.cos(phi2) * F.pow(F.sin(delta_lambda / F.lit(2.0)), 2)
    )
    return F.lit(2.0) * radius_km * F.asin(F.least(F.lit(1.0), F.sqrt(a)))


def route_segment(distance_column: F.Column) -> F.Column:
    return (
        F.when(distance_column < 300, F.lit("short_haul"))
        .when(distance_column < 1500, F.lit("medium_haul"))
        .otherwise(F.lit("long_haul"))
    )


def season(month_column: F.Column) -> F.Column:
    return (
        F.when(month_column.isin(12, 1, 2), F.lit("winter"))
        .when(month_column.isin(3, 4, 5), F.lit("spring"))
        .when(month_column.isin(6, 7, 8), F.lit("summer"))
        .otherwise(F.lit("fall"))
    )


def covid_period(year_column: F.Column) -> F.Column:
    return (
        F.when(year_column == 2020, F.lit("covid_shock"))
        .when(year_column == 2021, F.lit("covid_restriction"))
        .when(year_column == 2022, F.lit("recovery"))
        .otherwise(F.lit("post_recovery"))
    )


def build_months(spark: SparkSession) -> DataFrame:
    return spark.sql(
        f"""
        select explode(
            sequence(
                to_date('{START_YEAR}-01-01'),
                to_date('{END_YEAR}-12-01'),
                interval 1 month
            )
        ) as month_date
        """
    )


def nearest_origin_hubs(airports: DataFrame) -> DataFrame:
    origins = airports.select(
        F.col("iata").alias("origin_iata"),
        F.col("latitude").alias("origin_latitude"),
        F.col("longitude").alias("origin_longitude"),
    )
    hubs = airports.filter(F.col("airport_role") == "hub").select(
        F.col("iata").alias("nearest_origin_hub_iata"),
        F.col("latitude").alias("hub_latitude"),
        F.col("longitude").alias("hub_longitude"),
    )
    ranked = (
        origins.crossJoin(hubs)
        .withColumn(
            "nearest_origin_hub_distance_km",
            F.round(
                haversine_km(
                    F.col("origin_latitude"),
                    F.col("origin_longitude"),
                    F.col("hub_latitude"),
                    F.col("hub_longitude"),
                ),
                1,
            ),
        )
        .withColumn(
            "hub_rank",
            F.row_number().over(
                Window.partitionBy("origin_iata").orderBy("nearest_origin_hub_distance_km")
            ),
        )
    )
    return ranked.filter(F.col("hub_rank") == 1).select(
        "origin_iata",
        "nearest_origin_hub_iata",
        "nearest_origin_hub_distance_km",
    )


def build_route_month_skeleton(sources: dict[str, DataFrame], spark: SparkSession) -> DataFrame:
    airports = standardize_airports(sources["airports"])
    routes = standardize_routes(sources["seed_routes"])
    months = build_months(spark)
    hubs = nearest_origin_hubs(airports)

    origins = airports.select(
        F.col("iata").alias("origin_iata"),
        F.col("city").alias("origin_city"),
        F.col("province").alias("origin_province"),
        F.col("airport_role").alias("origin_airport_role"),
        F.col("latitude").alias("origin_latitude"),
        F.col("longitude").alias("origin_longitude"),
    )
    destinations = airports.select(
        F.col("iata").alias("destination_iata"),
        F.col("city").alias("destination_city"),
        F.col("province").alias("destination_province"),
        F.col("airport_role").alias("destination_airport_role"),
        F.col("latitude").alias("destination_latitude"),
        F.col("longitude").alias("destination_longitude"),
    )

    route_context = (
        routes.join(origins, on="origin_iata", how="inner")
        .join(destinations, on="destination_iata", how="inner")
        .join(hubs, on="origin_iata", how="left")
        .withColumn(
            "distance_km",
            F.round(
                haversine_km(
                    F.col("origin_latitude"),
                    F.col("origin_longitude"),
                    F.col("destination_latitude"),
                    F.col("destination_longitude"),
                ),
                1,
            ),
        )
        .withColumn("route_segment", route_segment(F.col("distance_km")))
        .withColumn("is_regional_origin", (F.col("origin_airport_role") == "regional").cast("int"))
        .withColumn("is_hub_destination", (F.col("destination_airport_role") == "hub").cast("int"))
    )

    return (
        route_context.crossJoin(months)
        .withColumn("month", F.date_format("month_date", "yyyy-MM-dd"))
        .withColumn("year", F.year("month_date").cast("int"))
        .withColumn("month_num", F.month("month_date").cast("int"))
        .withColumn("quarter", F.quarter("month_date").cast("int"))
        .withColumn("season", season(F.col("month_num")))
        .withColumn("covid_period", covid_period(F.col("year")))
        .withColumn("is_peak_travel_month", F.col("month_num").isin(3, 6, 7, 8, 12).cast("int"))
        .select(
            "route_id",
            "origin_iata",
            "destination_iata",
            "origin_city",
            "destination_city",
            "origin_province",
            "destination_province",
            "month",
            "year",
            "month_num",
            "quarter",
            "season",
            "covid_period",
            "is_peak_travel_month",
            "route_group",
            "strategic_role",
            "status_assumption",
            "is_regional_origin",
            "is_hub_destination",
            "distance_km",
            "route_segment",
            "nearest_origin_hub_iata",
            "nearest_origin_hub_distance_km",
            "notes",
        )
    )


def standardize_monthly_passengers(passengers: DataFrame) -> DataFrame:
    return (
        passengers.filter(F.col("metric") == "total_screened_passengers")
        .withColumn("iata", normalize_iata("iata"))
        .withColumn("month", F.date_format(F.to_date("month"), "yyyy-MM-dd"))
        .withColumn("monthly_screened_passengers", F.col("value").cast("long"))
        .groupBy("iata", "month")
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
        "month", F.date_format(F.to_date("month"), "yyyy-MM-dd")
    )
    for feature in MOVEMENT_FEATURES:
        output = output.withColumn(feature, F.col(feature).cast("long"))
    return output.select("iata", "month", *MOVEMENT_FEATURES).dropDuplicates(["iata", "month"])


def standardize_supply(supply: DataFrame) -> DataFrame:
    return (
        supply.withColumn("route_id", F.upper(F.trim(F.col("route_id"))))
        .withColumn("origin_iata", normalize_iata("origin_iata"))
        .withColumn("destination_iata", normalize_iata("destination_iata"))
        .withColumn("month", F.date_format(F.to_date("month"), "yyyy-MM-dd"))
        .withColumn("route_active", F.col("route_active").cast("int"))
        .withColumn("weekly_frequency_proxy", F.col("weekly_frequency_proxy").cast("double"))
        .withColumn("route_supply_event_count", F.col("route_supply_event_count").cast("int"))
        .withColumn("route_supply_confidence", F.coalesce(F.col("route_supply_confidence"), F.lit("uncovered")))
        .select(
            "route_id",
            "origin_iata",
            "destination_iata",
            "month",
            "route_active",
            "weekly_frequency_proxy",
            "route_supply_confidence",
            F.coalesce(F.col("route_supply_event_count"), F.lit(0)).alias("route_supply_event_count"),
            "route_supply_event_ids",
            "route_supply_carriers",
            "route_supply_evidence_types",
            "route_supply_source_titles",
            "route_supply_source_urls",
        )
        .dropDuplicates(["route_id", "month"])
    )


def prefixed_passengers(passengers: DataFrame, key_column: str, prefix: str) -> DataFrame:
    return passengers.select(
        F.col("iata").alias(key_column),
        "month",
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
        "month",
        *[F.col(feature).alias(f"{prefix}_{feature}") for feature in MOVEMENT_FEATURES],
    )


def add_passenger_context(panel: DataFrame, sources: dict[str, DataFrame]) -> DataFrame:
    monthly = standardize_monthly_passengers(sources["screened_passengers"])
    annual = standardize_annual_passengers(sources["annual_passengers"])
    return (
        panel.join(prefixed_passengers(monthly, "origin_iata", "origin"), on=["origin_iata", "month"], how="left")
        .join(
            prefixed_passengers(monthly, "destination_iata", "destination"),
            on=["destination_iata", "month"],
            how="left",
        )
        .join(
            prefixed_passengers(monthly, "nearest_origin_hub_iata", "nearest_origin_hub"),
            on=["nearest_origin_hub_iata", "month"],
            how="left",
        )
        .join(prefixed_annual_passengers(annual, "origin_iata", "origin"), on=["origin_iata", "year"], how="left")
        .join(
            prefixed_annual_passengers(annual, "destination_iata", "destination"),
            on=["destination_iata", "year"],
            how="left",
        )
        .join(
            prefixed_annual_passengers(annual, "nearest_origin_hub_iata", "nearest_origin_hub"),
            on=["nearest_origin_hub_iata", "year"],
            how="left",
        )
        .withColumn("observed_route_passengers", F.lit(None).cast("long"))
        .withColumn("flight_frequency_proxy", F.lit(None).cast("double"))
        .withColumn("route_active", F.lit(None).cast("int"))
        .withColumn("simulated_marketing_spend", F.lit(None).cast("double"))
    )


def add_movement_context(panel: DataFrame, sources: dict[str, DataFrame]) -> DataFrame:
    movements = standardize_movements(sources["airport_movements"])
    return (
        panel.join(prefixed_movements(movements, "origin_iata", "origin"), on=["origin_iata", "month"], how="left")
        .join(
            prefixed_movements(movements, "destination_iata", "destination"),
            on=["destination_iata", "month"],
            how="left",
        )
        .join(
            prefixed_movements(movements, "nearest_origin_hub_iata", "nearest_origin_hub"),
            on=["nearest_origin_hub_iata", "month"],
            how="left",
        )
    )


def add_supply_context(panel: DataFrame, sources: dict[str, DataFrame]) -> DataFrame:
    supply = standardize_supply(sources["route_supply"])
    with_supply = (
        panel.drop("route_active", "flight_frequency_proxy")
        .join(supply, on=["route_id", "origin_iata", "destination_iata", "month"], how="left")
        .withColumn("route_supply_confidence", F.coalesce(F.col("route_supply_confidence"), F.lit("uncovered")))
        .withColumn("route_supply_event_count", F.coalesce(F.col("route_supply_event_count"), F.lit(0)))
        .withColumnRenamed("weekly_frequency_proxy", "direct_weekly_frequency_proxy")
    )
    return with_supply.withColumn("flight_frequency_proxy", F.col("direct_weekly_frequency_proxy"))


def build_panel_v2(sources: dict[str, DataFrame], spark: SparkSession) -> DataFrame:
    skeleton = build_route_month_skeleton(sources, spark)
    panel_v0 = add_passenger_context(skeleton, sources)
    panel_v1 = add_movement_context(panel_v0, sources)
    panel_v2 = add_supply_context(panel_v1, sources)
    return panel_v2.select(*PANEL_COLUMNS).dropDuplicates(["route_id", "month"])


def print_stage_count(label: str, df: DataFrame) -> None:
    print(f"[count] {label}: {df.count():,} rows")


def validate_required_columns(df: DataFrame) -> None:
    missing = [column for column in PANEL_COLUMNS if column not in df.columns]
    print(f"[quality] required output columns present: {len(PANEL_COLUMNS) - len(missing)}/{len(PANEL_COLUMNS)}")
    if missing:
        raise ValueError(f"Missing expected panel columns: {missing}")


def validate_required_keys(df: DataFrame) -> None:
    failures = []
    for field in REQUIRED_COLUMNS:
        missing = df.filter(F.col(field).isNull()).count()
        print(f"[quality] null {field}: {missing:,}")
        if missing:
            failures.append(f"{field} has {missing:,} null rows")
    if failures:
        raise ValueError("; ".join(failures))


def validate_route_time_uniqueness(df: DataFrame) -> None:
    duplicate_keys = df.groupBy("route_id", "month").count().filter(F.col("count") > 1).count()
    print(f"[quality] duplicate route-month keys: {duplicate_keys:,}")
    if duplicate_keys:
        raise ValueError("Curated dataset must be unique at route_id x month grain.")


def validate_route_identifiers(df: DataFrame) -> None:
    invalid = df.filter(~F.col("route_id").rlike(r"^[A-Z0-9]{3}_[A-Z0-9]{3}$")).count()
    print(f"[quality] invalid route_id format: {invalid:,}")
    if invalid:
        raise ValueError("Found invalid route identifiers.")


def validate_schema(df: DataFrame) -> None:
    expected_types = {
        "route_id": "string",
        "month": "string",
        "year": "int",
        "month_num": "int",
        "quarter": "int",
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


def coverage_summary(df: DataFrame) -> dict[str, object]:
    summary = df.agg(
        F.count("*").alias("rows"),
        F.countDistinct("route_id").alias("routes"),
        F.min("month").alias("min_month"),
        F.max("month").alias("max_month"),
    ).collect()[0]
    return {
        "rows": int(summary["rows"]),
        "routes": int(summary["routes"]),
        "min_month": summary["min_month"],
        "max_month": summary["max_month"],
    }


def summarize_coverage(label: str, df: DataFrame) -> dict[str, object]:
    summary = coverage_summary(df)
    print(
        f"[quality] {label}: rows={summary['rows']:,}, routes={summary['routes']:,}, "
        f"month_range={summary['min_month']}..{summary['max_month']}"
    )
    return summary


def null_counts(df: DataFrame, fields: list[str]) -> dict[str, int]:
    if not fields:
        return {}
    row = df.agg(
        *[
            F.sum(F.when(F.col(field).isNull(), F.lit(1)).otherwise(F.lit(0))).alias(field)
            for field in fields
        ]
    ).collect()[0]
    return {field: int(row[field]) for field in fields}


def validate_against_legacy(spark: SparkSession, spark_panel: DataFrame) -> None:
    if not LEGACY_PANEL_FILE.exists():
        print(f"[legacy] skipped comparison; missing {LEGACY_PANEL_FILE.relative_to(PROJECT_ROOT)}")
        return

    legacy = read_csv(spark, LEGACY_PANEL_FILE)
    validate_required_columns(spark_panel)
    validate_required_columns(legacy)
    legacy_summary = summarize_coverage("legacy panel", legacy)
    spark_summary = summarize_coverage("spark panel", spark_panel)
    for key in ["rows", "routes", "min_month", "max_month"]:
        if legacy_summary[key] != spark_summary[key]:
            raise ValueError(
                f"Legacy and Spark panel coverage differ for {key}: "
                f"legacy={legacy_summary[key]}, spark={spark_summary[key]}"
            )

    legacy_duplicates = legacy.groupBy("route_id", "month").count().filter(F.col("count") > 1).count()
    spark_duplicates = spark_panel.groupBy("route_id", "month").count().filter(F.col("count") > 1).count()
    print(f"[legacy] duplicate keys: legacy={legacy_duplicates:,}, spark={spark_duplicates:,}")
    if legacy_duplicates or spark_duplicates:
        raise ValueError("Legacy comparison requires unique route_id x month keys.")

    legacy_counts = null_counts(legacy, REQUIRED_COLUMNS + LEGACY_COMPARE_FIELDS)
    spark_counts = null_counts(spark_panel, REQUIRED_COLUMNS + LEGACY_COMPARE_FIELDS)
    print("[legacy] null coverage comparison:")
    for field in REQUIRED_COLUMNS + LEGACY_COMPARE_FIELDS:
        print(f"  - {field}: legacy={legacy_counts[field]:,}, spark={spark_counts[field]:,}")

    legacy_compare = legacy.select(
        "route_id",
        "month",
        F.lit(1).alias("legacy_present"),
        *[
            F.coalesce(F.col(field).cast("string"), F.lit("")).alias(f"legacy_{field}")
            for field in LEGACY_COMPARE_FIELDS
        ],
    )
    spark_compare = spark_panel.select(
        "route_id",
        "month",
        F.lit(1).alias("spark_present"),
        *[
            F.coalesce(F.col(field).cast("string"), F.lit("")).alias(f"spark_{field}")
            for field in LEGACY_COMPARE_FIELDS
        ],
    )
    joined = legacy_compare.join(spark_compare, on=["route_id", "month"], how="full")
    missing_in_spark = joined.filter(F.col("spark_present").isNull()).count()
    missing_in_legacy = joined.filter(F.col("legacy_present").isNull()).count()
    mismatch_conditions = [
        F.col(f"legacy_{field}") != F.col(f"spark_{field}") for field in LEGACY_COMPARE_FIELDS
    ]
    any_mismatch = mismatch_conditions[0]
    for condition in mismatch_conditions[1:]:
        any_mismatch = any_mismatch | condition
    mismatches = joined.filter(any_mismatch).count()

    print(f"[legacy] keys missing in spark: {missing_in_spark:,}")
    print(f"[legacy] keys missing in legacy: {missing_in_legacy:,}")
    print(f"[legacy] joined-field mismatches: {mismatches:,}")
    if missing_in_spark or missing_in_legacy:
        raise ValueError("Spark and legacy panels do not cover the same route-month keys.")
    if mismatches:
        print("[legacy] Note: mismatches may reflect deterministic formatting/type differences; inspect before using as a drop-in replacement.")


def validate_data(spark: SparkSession, stages: dict[str, DataFrame], panel: DataFrame) -> None:
    for label, df in stages.items():
        print_stage_count(label, df)
    validate_required_columns(panel)
    validate_required_keys(panel)
    validate_route_time_uniqueness(panel)
    validate_route_identifiers(panel)
    validate_schema(panel)
    validate_numeric_sanity(panel)
    validate_against_legacy(spark, panel)


def remove_path(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def write_single_csv(df: DataFrame, output_file: Path) -> None:
    temp_dir = output_file.with_name(f"{output_file.name}.tmp")
    remove_path(temp_dir)
    remove_path(output_file)
    (
        df.coalesce(1)
        .write.mode("overwrite")
        .option("header", "true")
        .option("nullValue", "")
        .option("emptyValue", "")
        .csv(str(temp_dir))
    )
    part_files = sorted(temp_dir.glob("part-*.csv"))
    if not part_files:
        raise FileNotFoundError(f"No Spark CSV part file produced under {temp_dir}")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(part_files[0]), output_file)
    shutil.rmtree(temp_dir)


def write_outputs(panel: DataFrame) -> None:
    SPARK_DIR.mkdir(parents=True, exist_ok=True)
    remove_path(SPARK_PANEL_PARQUET_DIR)
    panel.write.mode("overwrite").partitionBy("year").parquet(str(SPARK_PANEL_PARQUET_DIR))
    write_single_csv(panel.orderBy("route_id", "month"), SPARK_PANEL_CSV_FILE)
    print(f"[write] parquet: {SPARK_PANEL_PARQUET_DIR.relative_to(PROJECT_ROOT)}")
    print(f"[write] csv: {SPARK_PANEL_CSV_FILE.relative_to(PROJECT_ROOT)}")


def load_spark_panel_to_pandas(csv_file: Path = SPARK_PANEL_CSV_FILE):
    """Small bridge for existing Pandas-style model exploration."""
    import pandas as pd

    return pd.read_csv(csv_file)


def main() -> None:
    spark = create_spark_session()
    try:
        sources = load_data(spark)
        skeleton = build_route_month_skeleton(sources, spark)
        panel_v0 = add_passenger_context(skeleton, sources)
        panel_v1 = add_movement_context(panel_v0, sources)
        panel_v2 = add_supply_context(panel_v1, sources).select(*PANEL_COLUMNS)
        validate_data(
            spark,
            {
                **sources,
                "spark_skeleton": skeleton,
                "spark_panel_v0": panel_v0,
                "spark_panel_v1": panel_v1,
                "spark_panel_v2": panel_v2,
            },
            panel_v2,
        )
        write_outputs(panel_v2)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
