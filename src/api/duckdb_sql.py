"""Parse PostgreSQL API SQL and emit equivalent read-only DuckDB SQL.

Transforms syntax trees rather than replacing SQL text: literals, identifiers,
parameter values and aggregate FILTER / ORDER BY scopes stay intact.
"""
from functools import lru_cache
import sqlglot
from sqlglot import exp


def function(name, *args):
    return exp.Anonymous(this=name, expressions=list(args))


def json_table_alias(node):
    alias = node.args.get('alias')
    if alias is not None and alias.args.get('columns'):
        return alias.copy()
    name = node.alias or 'jsonb_array_elements'
    return exp.TableAlias(this=exp.to_identifier(name + '_elements'), columns=[exp.to_identifier(name)])


@lru_cache(maxsize=512)
def translate(sql: str) -> str:
    tree = sqlglot.parse_one(sql, read='postgres')
    for select in tree.find_all(exp.Select):
        # PG keeps the source column label through an unaliased cast; DuckDB
        # labels that projection with its expression text instead.
        select.set('expressions', [exp.alias_(item, item.this.name) if isinstance(item, exp.Cast) and isinstance(item.this, exp.Column) else item
            for item in select.expressions])
    for exists in tree.find_all(exp.Exists):
        select = exists.this
        if isinstance(select, exp.Select):
            limit, offset = select.args.get('limit'), select.args.get('offset')
            if limit is not None and isinstance(limit.expression, exp.Literal) and limit.expression.this == '1' and (offset is None or isinstance(offset.expression, exp.Literal) and offset.expression.this == '0'):
                # This PG planning barrier is truth-preserving but makes DuckDB
                # decorrelation build giant partitioned row-number windows.
                select.set('limit', None)
                select.set('offset', None)
    for equality in list(tree.find_all(exp.EQ)):
        if isinstance(equality.expression, exp.Any):
            items = equality.expression.this
            if isinstance(items, exp.Paren):
                items = items.this
            if isinstance(items, exp.StringToArray):
                value = equality.this
                # Row-local ANY must stay row-local: DuckDB decorrelation would
                # otherwise expand every consequence row before gene filtering.
                # Preserve PostgreSQL three-valued ANY semantics, including
                # NULL elements and the empty-array / NULL-value exception.
                equality.replace(exp.Case(ifs=[
                    exp.If(this=function('list_contains', items.copy(), value.copy()), true=exp.true()),
                    exp.If(this=exp.Is(this=items.copy(), expression=exp.Null()), true=exp.Null()),
                    exp.If(this=exp.EQ(this=function('len', items.copy()), expression=exp.Literal.number(0)), true=exp.false()),
                    exp.If(this=exp.Or(this=exp.Is(this=value.copy(), expression=exp.Null()),
                        expression=exp.Not(this=exp.Is(this=function('list_position', items.copy(), exp.Null()), expression=exp.Null()))), true=exp.Null())
                ], default=exp.false()))
    # Table functions need a named value column, because PostgreSQL exposes a
    # single JSON scalar through its table alias while DuckDB exposes a struct.
    for lateral in list(tree.find_all(exp.Lateral)):
        call = lateral.this
        if isinstance(call, exp.Unnest):
            call.set('alias', lateral.args.get('alias'))
            lateral.replace(call)
            continue
        if isinstance(call, exp.Anonymous) and call.name.lower() == 'jsonb_array_elements':
            lateral.set('this', exp.Unnest(expressions=[function('json_extract', call.expressions[0], exp.Literal.string('$[*]'))]))
            lateral.set('alias', json_table_alias(lateral))
    for table in list(tree.find_all(exp.Table)):
        call = table.this
        if isinstance(call, exp.Anonymous) and call.name.lower() == 'jsonb_array_elements':
            table.replace(exp.Unnest(expressions=[function('json_extract', call.expressions[0], exp.Literal.string('$[*]'))],
                alias=json_table_alias(table)))
    for node in reversed(list(tree.walk())):
        if isinstance(node, exp.StringToArray):
            node.replace(exp.Case(ifs=[exp.If(this=exp.EQ(this=node.this.copy(), expression=exp.Literal.string('')), true=exp.Array(expressions=[]))],
                default=function('string_to_array', node.this.copy(), node.expression.copy())))
        elif isinstance(node, (exp.Like, exp.ILike)) and not isinstance(node.parent, exp.Escape):
            # PostgreSQL defaults to backslash escapes; DuckDB requires ESCAPE.
            node.replace(exp.Escape(this=node.copy(), expression=exp.Literal.string(chr(92))))
        elif isinstance(node, exp.ArrayContainsAll):
            # All API @> operands are JSON context objects, never SQL arrays.
            node.replace(function('json_contains', node.this, node.expression))
        elif isinstance(node, exp.JSONBContainsTopKey):
            # API ? operands are JSON arrays of identifiers / candidate accessions.
            node.replace(function('list_contains', function('json_extract_string', node.this, exp.Literal.string('$[*]')), node.expression))
        elif isinstance(node, exp.Anonymous):
            name = node.name.lower()
            if name == 'to_regclass':
                # Runtime availability checks must also work without PostgreSQL.
                value = node.expressions[0]
                node.replace(exp.Subquery(this=exp.select('table_name').from_('information_schema.tables').where(
                    exp.EQ(this=exp.Concat(expressions=[exp.column('table_schema'), exp.Literal.string('.'), exp.column('table_name')]), expression=value)).limit(1)))
            elif name == 'to_regnamespace':
                node.replace(exp.Subquery(this=exp.select('schema_name').from_('information_schema.schemata').where(
                    exp.EQ(this=exp.column('schema_name'), expression=node.expressions[0])).limit(1)))
            elif name == 'jsonb_build_object':
                node.set('this', 'json_object')
            elif name == 'jsonb_object':
                node.replace(function('to_json', function('map', *node.expressions)))
            elif name == 'jsonb_agg':
                node.set('this', 'list')
                aggregate = node.parent if isinstance(node.parent, exp.Filter) else node
                result = function('to_json', aggregate.copy())
                if isinstance(node.expressions[0], exp.Distinct):
                    result = function('memvar_pg_json_distinct_list', result)
                aggregate.replace(result)
        elif isinstance(node, exp.Cast) and isinstance(node.this, exp.Literal) and node.this.this == '{}':
            if node.args['to'].is_type(exp.DataType.Type.ARRAY):
                node.set('this', exp.Array(expressions=[]))
    # PostgreSQL array coalesce uses an implicitly typed '{}' literal.
    for node in tree.find_all(exp.Coalesce):
        if any(isinstance(a, exp.ArrayAgg) for a in node.walk()):
            for child in node.expressions:
                if isinstance(child, exp.Literal) and child.this == '{}':
                    child.replace(exp.Array(expressions=[]))
    for order in list(tree.find_all(exp.Order)):
        # DISTINCT aggregate ordering must refer to its argument. Its scalar
        # result is re-sorted below instead of adding an unrelated order key.
        if isinstance(order.this, exp.Distinct) or isinstance(order.parent, exp.WithinGroup):
            continue
        terms = []
        for ordered in order.expressions:
            value = ordered.this
            if isinstance(value, exp.Literal) and not value.is_string:
                # Numeric ORDER BY positions refer to projected columns.
                terms.append(ordered)
                continue
            text_value = exp.Case(ifs=[exp.If(this=exp.EQ(this=function('typeof', value.copy()), expression=exp.Literal.string('VARCHAR')),
                true=exp.Cast(this=value.copy(), to=exp.DataType.build('VARCHAR')))])
            key_order = ordered.copy()
            key_order.set('this', function('memvar_pg_text_key', text_value))
            terms.extend([key_order, ordered])
        order.set('expressions', terms)
    for aggregate in list(tree.find_all(exp.ArrayAgg)):
        # PostgreSQL DISTINCT array aggregation sorts its values even when the
        # SQL has no explicit ORDER BY. Current API DISTINCT arrays are text.
        argument = aggregate.this
        if isinstance(argument, exp.Distinct) or (isinstance(argument, exp.Order) and isinstance(argument.this, exp.Distinct)):
            container = aggregate.parent if isinstance(aggregate.parent, exp.Filter) else aggregate
            container.replace(function('memvar_pg_text_list', container.copy()))
    return tree.sql(dialect='duckdb', unsupported_level=sqlglot.ErrorLevel.RAISE)
