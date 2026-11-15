{#
  A model's schema is used exactly as configured: `serving` means `serving`.

  dbt's default would build `<target schema>_<custom schema>`, which keeps
  developers apart in a shared warehouse. Here every developer and every CI run
  has a database of its own, the schemas are created and granted by Alembic,
  and the product service reads `serving` by that name.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
