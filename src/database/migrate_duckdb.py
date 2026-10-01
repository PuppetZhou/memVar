"""Read-only PostgreSQL snapshot migration with full Parquet round-trip validation.

python -m Web.src.database.migrate_duckdb build --workers 3
python -m Web.src.database.migrate_duckdb catalog SNAPSHOT_DIRECTORY
"""

from __future__ import annotations
import argparse
import concurrent.futures
import datetime
import json
import re
import time
import subprocess
import shutil
import struct
from pathlib import Path
import duckdb
import psycopg
import pyarrow as pa
import pyarrow.parquet as pq
import yaml
from psycopg import sql
from psycopg.types.json import set_json_loads

WEB = Path(__file__).resolve().parents[2]
ARROW = {
    "text": pa.string(),
    "jsonb": pa.string(),
    "int4": pa.int32(),
    "int8": pa.int64(),
    "float4": pa.float32(),
    "float8": pa.float64(),
    "bool": pa.bool_(),
    "_text": pa.list_(pa.string()),
    "_float4": pa.list_(pa.float32()),
}
DUCK = {
    "text": "VARCHAR",
    "jsonb": "JSON",
    "int4": "INTEGER",
    "int8": "BIGINT",
    "float4": "FLOAT",
    "float8": "DOUBLE",
    "bool": "BOOLEAN",
    "_text": "VARCHAR[]",
    "_float4": "FLOAT[]",
}
WIDE_JSON = {"expression_gtex_gene_tpm", "expression_gtex_transcript_tpm"}
QTL = {"gtex_qtl_pair", "eqtlgen_cis", "qtlbase_association"}
MATERIALIZED = {
    "web_context.ppi_record",
    "web_disease.medgen_names",
    "web_disease.medgen_definitions",
    "web.protein_external_reference_all",
}


def qi(s):
    return '"' + s.replace('"', '""') + '"'


def write_json(path, value):
    """Replace metadata atomically; a reader never observes truncated JSON."""
    temporary = path.with_name(path.name + ".writing")
    temporary.write_text(json.dumps(value, indent=2, default=str))
    temporary.replace(path)


def config():
    c = yaml.safe_load((WEB / "config/database.yaml").read_text())
    env = dict(
        line.split("=", 1)
        for line in (WEB / c["credentials_file"]).read_text().splitlines()
        if "=" in line and not line.lstrip().startswith("#")
    )
    return dict(
        host=c["host"],
        port=c["port"],
        dbname=c["database"],
        user=env["POSTGRES_USER"],
        password=env["POSTGRES_PASSWORD"],
    )


def connect():
    p = psycopg.connect(**config())
    set_json_loads(lambda x: x.decode() if isinstance(x, bytes) else x, p)
    return p


def inventory(p):
    objects = []
    for schema, name, kind, estimate, size, definition in p.execute(
        "SELECT n.nspname,c.relname,c.relkind,c.reltuples::bigint,CASE WHEN c.relkind='v' THEN 0 ELSE pg_total_relation_size(c.oid) END,CASE WHEN c.relkind='v' THEN pg_get_viewdef(c.oid,true) END FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname LIKE 'web%' AND c.relkind IN ('r','v','m') ORDER BY n.nspname,c.relname"
    ):
        cols = [
            dict(name=a, pg_type=b, nullable=c)
            for a, b, c in p.execute(
                "SELECT a.attname,t.typname,CASE WHEN a.attnotnull THEN 'NO' ELSE 'YES' END FROM pg_attribute a JOIN pg_type t ON t.oid=a.atttypid JOIN pg_class c ON c.oid=a.attrelid JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname=%s AND c.relname=%s AND a.attnum>0 AND NOT a.attisdropped ORDER BY a.attnum",
                (schema, name),
            ).fetchall()
        ]
        keys = p.execute(
            "SELECT a.attname FROM pg_index i JOIN pg_class c ON c.oid=i.indrelid JOIN pg_namespace n ON n.oid=c.relnamespace JOIN pg_attribute a ON a.attrelid=c.oid AND a.attnum=ANY(i.indkey) WHERE n.nspname=%s AND c.relname=%s AND i.indisprimary ORDER BY array_position(i.indkey,a.attnum)",
            (schema, name),
        ).fetchall()
        objects.append(
            dict(
                schema=schema,
                name=name,
                kind=kind,
                estimated_rows=estimate,
                postgres_total_bytes=size,
                definition=definition,
                columns=cols,
                primary_key=[x[0] for x in keys],
                storage="logical_view"
                if kind == "v" and f"{schema}.{name}" not in MATERIALIZED
                else "parquet",
            )
        )
    return objects


def same_value(left, right):
    """Logical equality including nested lists, NULL, and IEEE NaN."""
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(
            same_value(x, y) for x, y in zip(left, right)
        )
    if (
        isinstance(left, float)
        and isinstance(right, float)
        and left != left
        and right != right
    ):
        return True
    return left == right


def same_typed_value(source, value, arrow_type):
    """Compare exact source precision rather than widening float4 decimal text."""
    if source is None or value is None:
        return source is value
    if pa.types.is_list(arrow_type):
        return len(source) == len(value) and all(
            same_typed_value(x, y, arrow_type.value_type) for x, y in zip(source, value)
        )
    if pa.types.is_floating(arrow_type):
        code = "f" if arrow_type.bit_width == 32 else "d"
        if source != source and value != value:
            return True
        return struct.pack("!" + code, source) == struct.pack("!" + code, value)
    return source == value


def export(obj, snapshot, root, batch_rows):
    start = time.monotonic()
    dest = root / "data" / obj["schema"] / obj["name"]
    dest.mkdir(parents=True)
    arrow_schema = pa.schema([(c["name"], ARROW[c["pg_type"]]) for c in obj["columns"]])
    extra_ctid = obj["name"] in {"eqtlgen_cis", "qtlbase_association"}
    if extra_ctid:
        arrow_schema = arrow_schema.append(pa.field("_source_ctid", pa.int64()))
    count = 0
    bytes_ = 0
    files = []
    with connect() as p:
        p.execute("BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY")
        p.execute(sql.SQL("SET TRANSACTION SNAPSHOT {}").format(sql.Literal(snapshot)))
        # Existing primary key order provides predictable ranges without changing records.
        order = (
            ["hgnc_id", "dataset_id"] if obj["name"] in QTL else obj["primary_key"][:2]
        )
        projection = (
            "*, ((split_part(trim(both '()' from ctid::text), ',', 1)::bigint * 65536) + split_part(trim(both '()' from ctid::text), ',', 2)::bigint) AS _source_ctid"
            if extra_ctid
            else "*"
        )
        query = sql.SQL("SELECT " + projection + " FROM {}.{}").format(
            sql.Identifier(obj["schema"]), sql.Identifier(obj["name"])
        )
        if order:
            query += sql.SQL(" ORDER BY ") + sql.SQL(",").join(
                map(sql.Identifier, order)
            )
        with p.cursor(name="migration_stream", binary=True) as cursor:
            cursor.execute(query)
            while True:
                rows = cursor.fetchmany(batch_rows)
                if not rows:
                    break
                table = pa.Table.from_arrays(
                    [
                        pa.array([r[i] for r in rows], type=f.type)
                        for i, f in enumerate(arrow_schema)
                    ],
                    schema=arrow_schema,
                )
                for column_index in range(table.num_columns):
                    source_values = [r[column_index] for r in rows]
                    arrow_values = table.column(column_index).to_pylist()
                    if not all(
                        same_typed_value(x, y, arrow_schema[column_index].type)
                        for x, y in zip(source_values, arrow_values)
                    ):
                        raise RuntimeError(
                            f"PostgreSQL→Arrow mismatch {obj['schema']}.{obj['name']}.{arrow_schema[column_index].name}"
                        )
                path = dest / f"part-{len(files):06d}.parquet"
                tmp = path.with_suffix(".parquet.tmp")
                pq.write_table(
                    table,
                    tmp,
                    compression="zstd",
                    compression_level=3,
                    row_group_size=256
                    if obj["name"] in WIDE_JSON
                    else min(batch_rows, 65536),
                    use_dictionary=True,
                    write_statistics=True,
                )
                recovered = pq.read_table(tmp)
                # Arrow equality treats NaN as unequal; compare buffers through Python only for such columns.
                for i in range(table.num_columns):
                    a, b = table.column(i), recovered.column(i)
                    if not a.equals(b):
                        if not all(
                            same_value(x, y)
                            for x, y in zip(a.to_pylist(), b.to_pylist())
                        ):
                            raise RuntimeError(
                                f"Parquet roundtrip mismatch {obj['schema']}.{obj['name']}.{arrow_schema[i].name}"
                            )
                tmp.replace(path)
                files.append(str(path.relative_to(root)))
                count += len(rows)
                bytes_ += path.stat().st_size
                write_json(
                    dest / "progress.json",
                    dict(
                        rows=count,
                        files=len(files),
                        bytes=bytes_,
                        elapsed_seconds=round(time.monotonic() - start, 2),
                    ),
                )
        baseline_count = p.execute(
            sql.SQL("SELECT count(*) FROM {}.{}").format(
                sql.Identifier(obj["schema"]), sql.Identifier(obj["name"])
            )
        ).fetchone()[0]
        if count != baseline_count:
            raise RuntimeError("Snapshot row count mismatch")
    if extra_ctid:
        obj = dict(
            obj,
            columns=obj["columns"]
            + [
                dict(
                    name="_source_ctid",
                    pg_type="int8",
                    nullable="NO",
                    role="original PostgreSQL tid tie-break, encoded block*65536+offset",
                )
            ],
        )
    result = dict(
        obj,
        rows=count,
        bytes=bytes_,
        files=files,
        order_by=order,
        row_group_rows=256 if obj["name"] in WIDE_JSON else min(batch_rows, 65536),
        verified="all fields of all exported rows: Arrow→Parquet→Arrow exact round-trip; same-snapshot count",
        elapsed_seconds=round(time.monotonic() - start, 2),
    )
    write_json(dest / "table.json", result)
    print(
        json.dumps(
            dict(
                table=f"{obj['schema']}.{obj['name']}",
                rows=count,
                bytes=bytes_,
                seconds=result["elapsed_seconds"],
            )
        ),
        flush=True,
    )
    return result


def catalog(root):
    manifest = json.loads((root / "manifest.json").read_text())
    target = root / "catalog.duckdb"
    temporary = root / "catalog.building.duckdb"
    temporary.unlink(missing_ok=True)
    with duckdb.connect(str(temporary)) as d:
        for schema in sorted({x["schema"] for x in manifest["objects"]}):
            d.execute("CREATE SCHEMA " + qi(schema))
        for obj in manifest["objects"]:
            if obj["storage"] != "parquet":
                continue
            projection = ",".join(
                f"CAST({qi(c['name'])} AS {DUCK[c['pg_type']]}) AS {qi(c['name'])}"
                for c in obj["columns"]
            )
            path = str(root / "data" / obj["schema"] / obj["name"] / "part-*.parquet")
            if not obj["files"]:
                # Empty tables still retain their exact field contract.
                pa_schema = pa.schema(
                    [(c["name"], ARROW[c["pg_type"]]) for c in obj["columns"]]
                )
                empty_path = (
                    root / "data" / obj["schema"] / obj["name"] / "part-empty.parquet"
                )
                pq.write_table(pa.Table.from_batches([], schema=pa_schema), empty_path)
                obj["files"] = [str(empty_path.relative_to(root))]
                obj["bytes"] = empty_path.stat().st_size
            d.execute(
                f"CREATE VIEW {qi(obj['schema'])}.{qi(obj['name'])} AS SELECT {projection} FROM read_parquet('{path.replace(chr(39), chr(39) * 2)}')"
            )
        pending = [x for x in manifest["objects"] if x["storage"] == "logical_view"]
        while pending:
            failures = []
            for obj in pending:
                definition = re.sub(r"::jsonb\b", "::JSON", obj["definition"])
                try:
                    d.execute(
                        f"CREATE VIEW {qi(obj['schema'])}.{qi(obj['name'])} AS "
                        + definition
                    )
                except duckdb.Error:
                    from ..api.duckdb_sql import translate

                    try:
                        d.execute(
                            f"CREATE VIEW {qi(obj['schema'])}.{qi(obj['name'])} AS "
                            + translate(obj["definition"])
                        )
                    except Exception as translated_error:
                        failures.append((obj, str(translated_error)))
            if len(failures) == len(pending):
                raise RuntimeError(
                    "View translation errors: "
                    + json.dumps(
                        [(x["schema"] + "." + x["name"], e) for x, e in failures]
                    )
                )
            pending = [x for x, e in failures]
        d.execute("CHECKPOINT")
    temporary.replace(target)
    write_json(root / "manifest.json", manifest)
    return target


def capture_view_baselines(objects, snapshot, root):
    """Bind logical view counts and complete representative values to the source snapshot."""
    destination = root / "view-baseline"
    destination.mkdir(exist_ok=True)

    def capture(obj):
        with connect() as connection:
            connection.execute("BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY")
            connection.execute(
                sql.SQL("SET TRANSACTION SNAPSHOT {}").format(sql.Literal(snapshot))
            )
            name = sql.SQL("{}.{}").format(
                sql.Identifier(obj["schema"]), sql.Identifier(obj["name"])
            )
            started = time.monotonic()
            count = connection.execute(
                sql.SQL("SELECT count(*) FROM ") + name
            ).fetchone()[0]
            rows = connection.execute(
                sql.SQL("SELECT * FROM ") + name + sql.SQL(" LIMIT 16")
            ).fetchall()
            write_json(
                destination / f"{obj['schema']}.{obj['name']}.json",
                dict(
                    schema=obj["schema"],
                    name=obj["name"],
                    rows=count,
                    columns=obj["columns"],
                    sample_rows=rows,
                    seconds=time.monotonic() - started,
                ),
            )

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        list(
            executor.map(
                capture, [obj for obj in objects if obj["storage"] == "logical_view"]
            )
        )


def canonical(value, pg_type):
    """Canonical comparison only: stored source JSON and floating values are never changed."""
    if value is None:
        return None
    if pg_type == "jsonb":
        return json.dumps(
            json.loads(value) if isinstance(value, str) else value,
            sort_keys=True,
            separators=(",", ":"),
        )
    if pg_type in {"float4", "float8"}:
        if value != value:
            return "IEEE NaN"
        return struct.pack("!" + ("f" if pg_type == "float4" else "d"), value).hex()
    if pg_type.startswith("_"):
        return tuple(
            canonical(item, {"_text": "text", "_float4": "float4"}[pg_type])
            for item in value
        )
    return value


def verify_views(root):
    """Check every logical view schema/count and complete sampled source rows."""
    root = root.resolve()
    manifest = json.loads((root / "manifest.json").read_text())
    results = []
    with duckdb.connect(str(root / "catalog.duckdb"), read_only=True) as database:
        database.execute("SET memory_limit='6GB'")
        database.execute("SET threads=4")
        for obj in manifest["objects"]:
            if obj["storage"] != "logical_view":
                continue
            source = json.loads(
                (
                    root / "view-baseline" / f"{obj['schema']}.{obj['name']}.json"
                ).read_text()
            )
            relation = qi(obj["schema"]) + "." + qi(obj["name"])
            actual_schema = [
                (row[0], row[1])
                for row in database.execute(
                    "DESCRIBE SELECT * FROM " + relation
                ).fetchall()
            ]
            expected_schema = [
                (column["name"], DUCK[column["pg_type"]]) for column in obj["columns"]
            ]
            if actual_schema != expected_schema:
                raise RuntimeError(
                    f"View schema mismatch {relation}: {actual_schema} != {expected_schema}"
                )
            started = time.monotonic()
            count = database.execute("SELECT count(*) FROM " + relation).fetchone()[0]
            if count != source["rows"]:
                raise RuntimeError(
                    f"View count mismatch {relation}: {count} != {source['rows']}"
                )
            rows = source["sample_rows"]
            if rows:
                first_col = qi(obj["columns"][0]["name"])
                keys = list(dict.fromkeys(row[0] for row in rows if row[0] is not None))
                candidates = database.execute(
                    f"SELECT * FROM {relation} WHERE {first_col} IN (SELECT unnest(?)) OR {first_col} IS NULL",
                    [keys],
                ).fetchall()

                def normalized(row):
                    return tuple(
                        canonical(value, column["pg_type"])
                        for value, column in zip(row, obj["columns"])
                    )

                observed = set(map(normalized, candidates))
                if any(normalized(row) not in observed for row in rows):
                    raise RuntimeError("View full sample value mismatch " + relation)
            results.append(
                dict(
                    schema=obj["schema"],
                    name=obj["name"],
                    rows=count,
                    sampled_rows=len(rows),
                    seconds=round(time.monotonic() - started, 3),
                    checks="exact field contract; full count; all fields in representative source rows",
                )
            )
            write_json(
                root / "view-verification.json", dict(status="running", views=results)
            )
    write_json(root / "view-verification.json", dict(status="passed", views=results))
    return results


def build_record_file_locator(root):
    """Index exact Parquet footer ranges without reading source rows or JSON."""
    root = root.resolve()
    manifest = json.loads((root / "manifest.json").read_text())
    obj = next(
        item
        for item in manifest["objects"]
        if item["schema"] == "web_variant" and item["name"] == "variant_source_record"
    )
    files = []
    for relative_path in obj["files"]:
        parquet = pq.ParquetFile(root / relative_path)
        column = parquet.schema_arrow.names.index("record_id")
        lower = []
        upper = []
        complete = True
        for group in range(parquet.num_row_groups):
            stats = parquet.metadata.row_group(group).column(column).statistics
            if stats is None or not stats.has_min_max:
                complete = False
                break
            lower.append(stats.min)
            upper.append(stats.max)
        files.append(
            dict(
                path=relative_path,
                rows=parquet.metadata.num_rows,
                min_record_id=min(lower) if complete and lower else None,
                max_record_id=max(upper) if complete and upper else None,
            )
        )
    if sum(item["rows"] for item in files) != obj["rows"]:
        raise RuntimeError("Record locator footer row count mismatch")
    value = dict(
        format_version=1,
        snapshot_id=manifest["snapshot_id"],
        relation="web_variant.variant_source_record",
        key="record_id",
        comparison="binary UTF-8 Parquet statistics; return every overlapping file; unknown bounds match every key",
        rows=obj["rows"],
        files=files,
    )
    target = root / "source-record-files.json"
    write_json(target, value)
    return target


def locate_record_files(root, record_id):
    """Return all overlapping files: locale-sorted source ranges may overlap."""
    locator = json.loads((root / "source-record-files.json").read_text())
    return [
        root / item["path"]
        for item in locator["files"]
        if item["min_record_id"] is None
        or item["min_record_id"] <= record_id <= item["max_record_id"]
    ]


def source_metadata(connection):
    """Record relationship keys and locale within the same exported snapshot."""
    columns = [
        "schema",
        "table",
        "name",
        "kind",
        "validated",
        "definition",
        "referenced_schema",
        "referenced_table",
        "columns",
        "referenced_columns",
    ]
    records = connection.execute("""
        SELECT ns.nspname,t.relname,c.conname,c.contype,c.convalidated,
               pg_get_constraintdef(c.oid,true),rns.nspname,rt.relname,
               ARRAY(SELECT a.attname FROM unnest(c.conkey) WITH ORDINALITY k(attnum,ord)
                     JOIN pg_attribute a ON a.attrelid=c.conrelid AND a.attnum=k.attnum ORDER BY k.ord),
               ARRAY(SELECT a.attname FROM unnest(c.confkey) WITH ORDINALITY k(attnum,ord)
                     JOIN pg_attribute a ON a.attrelid=c.confrelid AND a.attnum=k.attnum ORDER BY k.ord)
        FROM pg_constraint c JOIN pg_namespace ns ON ns.oid=c.connamespace
        JOIN pg_class t ON t.oid=c.conrelid
        LEFT JOIN pg_class rt ON rt.oid=c.confrelid
        LEFT JOIN pg_namespace rns ON rns.oid=rt.relnamespace
        WHERE ns.nspname LIKE 'web%' ORDER BY 1,2,3
        """).fetchall()
    collation = connection.execute(
        "SELECT datcollate,datctype FROM pg_database WHERE datname=current_database()"
    ).fetchone()
    indexes = connection.execute(
        "SELECT schemaname,tablename,indexname,indexdef FROM pg_indexes WHERE schemaname LIKE 'web%' ORDER BY 1,2,3"
    ).fetchall()
    routines = connection.execute(
        "SELECT n.nspname,p.proname,pg_get_functiondef(p.oid) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname LIKE 'web%' AND p.prokind <> 'a'"
    ).fetchall()
    return dict(
        constraints=[dict(zip(columns, row)) for row in records],
        collation=dict(datcollate=collation[0], datctype=collation[1]),
        indexes=indexes,
        routines=routines,
    )


def build(args):
    root = (WEB / args.output).resolve()
    root.mkdir(parents=True, exist_ok=False)
    args._created_output = True
    if (WEB / "data/catalog_statistics.json").exists():
        shutil.copy2(
            WEB / "data/catalog_statistics.json", root / "catalog_statistics.json"
        )
    with connect() as keeper:
        keeper.execute("BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY")
        snap = keeper.execute("SELECT pg_export_snapshot()").fetchone()[0]
        meta = keeper.execute(
            "SELECT current_database(),version(),transaction_timestamp()::text,pg_current_snapshot()::text"
        ).fetchone()
        objects = inventory(keeper)
        metadata = source_metadata(keeper)
        metadata["snapshot_id"] = snap
        write_json(root / "source-metadata.json", metadata)
        constraints = metadata["constraints"]
        code_version = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=WEB, capture_output=True, text=True
        ).stdout.strip()
        source_versions = {}
        for o in objects:
            if o["name"].endswith("build_manifest"):
                source_versions[o["schema"] + "." + o["name"]] = [
                    dict(zip([c["name"] for c in o["columns"]], row))
                    for row in keeper.execute(
                        sql.SQL("SELECT * FROM {}.{}").format(
                            sql.Identifier(o["schema"]), sql.Identifier(o["name"])
                        )
                    )
                ]
        manifest = dict(
            format_version=1,
            code_version=code_version,
            code_dirty=bool(
                subprocess.run(
                    ["git", "status", "--porcelain"],
                    cwd=WEB,
                    capture_output=True,
                    text=True,
                ).stdout
            ),
            executed_export_profile="binary PostgreSQL transport; typed PG→Arrow bit comparison; full Arrow→Parquet→Arrow field equality; snapshot count",
            source_versions=source_versions,
            status="building",
            snapshot_id=snap,
            source=dict(
                database=meta[0],
                server=meta[1],
                transaction_time=meta[2],
                snapshot=meta[3],
            ),
            compression="zstd level 3",
            objects=objects,
            constraints=constraints,
            collation=metadata["collation"],
        )
        write_json(root / "manifest.json", manifest)
        selected = sorted(
            [x for x in objects if x["storage"] == "parquet"],
            key=lambda x: -x["postgres_total_bytes"],
        )
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = {
                pool.submit(export, obj, snap, root, args.batch_rows): (
                    obj["schema"],
                    obj["name"],
                )
                for obj in selected
            }
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                objects[
                    objects.index(
                        next(
                            x
                            for x in objects
                            if (x["schema"], x["name"]) == futures[future]
                        )
                    )
                ] = result
                write_json(root / "manifest.json", manifest)
        manifest["status"] = "exported"
        write_json(root / "manifest.json", manifest)
        capture_view_baselines(objects, snap, root)
        catalog(root)
        verify_views(root)
        build_record_file_locator(root)
        manifest = json.loads((root / "manifest.json").read_text())
        manifest["runtime_sidecars"] = [
            "catalog_statistics.json",
            "source-record-files.json",
        ]
        manifest["record_locator"] = "source-record-files.json"
        manifest["status"] = "storage_validated"
        manifest["parquet_bytes"] = sum(x.get("bytes", 0) for x in manifest["objects"])
        write_json(root / "manifest.json", manifest)
    print(str(root), flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest="command", required=True)
    b = s.add_parser("build")
    b.add_argument("--workers", type=int, default=3)
    b.add_argument("--batch-rows", type=int, default=65536)
    b.add_argument(
        "--output",
        default="data/duckdb-candidate/snapshot-"
        + datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
    )
    locator_parser = s.add_parser("record-locator")
    locator_parser.add_argument("directory", type=Path)
    v = s.add_parser("verify-views")
    v.add_argument("directory", type=Path)
    c = s.add_parser("catalog")
    c.add_argument("directory", type=Path)
    a = p.parse_args()
    if a.command == "record-locator":
        print(build_record_file_locator(a.directory.resolve()))
    elif a.command == "verify-views":
        print(json.dumps(verify_views(a.directory.resolve())))
    elif a.command == "catalog":
        print(catalog(a.directory.resolve()))
    else:
        try:
            build(a)
        except BaseException as error:
            root = (WEB / a.output).resolve()
            path = root / "manifest.json"
            if getattr(a, "_created_output", False) and path.exists():
                value = json.loads(path.read_text())
                value["status"] = (
                    "interrupted" if isinstance(error, KeyboardInterrupt) else "failed"
                )
                # Database credentials and connection parameters are never included in status errors.
                value["failure_type"] = type(error).__name__
                write_json(path, value)
            raise


if __name__ == "__main__":
    main()
