# Recent AWS analytics launches (2025–2026)

Reference data for `analytics-agent`. Confidence is noted inline per item; vendor "up to"
figures are AWS-stated, not benchmarked. Re-check region and feature availability against
the live docs before scripting against any of it.

- **OpenSearch GPU-accelerated, auto-optimized vector indexes** (GA 2025-12-02) — build
  billion-scale vector indexes ~10× faster at a quarter of the **indexing** cost;
  serverless GPUs activate dynamically and bill only when boosting; auto-optimize
  balances quality/speed/cost. GPU regions: us-east-1, us-west-2, ap-southeast-2,
  eu-west-1, ap-northeast-1 (OpenSearch 3.1+); auto-optimize in 9 regions (2.17+). Plan
  GPU-region placement + serverless-GPU billing. (AWS-measured 6.4–13.8×; "10×"/"¼ cost"
  are representative / indexing-only.)
- **OpenSearch Agentic Search** (3.3+, 2025-11-25, Commercial + GovCloud US) —
  natural-language query planning/orchestration (vector/neural/lexical), no hand-written
  DSL. (Medium confidence: GA inferred from launch language + live docs.)
- **AWS Glue 5.1** (GA 2025-11-26) — Spark 3.5.6 / Python 3.11 / Scala 2.12.18; updated
  Hudi/Iceberg/Delta libs; **Apache Iceberg v3** (deletion vectors for merge-on-read, row
  lineage, default column values). Plan engine-version migrations.
- **Iceberg V3 across the stack** (2025-11) — deletion vectors + row lineage on EMR 7.12,
  Glue, S3 Tables, Glue Data Catalog, SageMaker. Affects table-format choices for lakehouse pipelines.
- **Glue Data Catalog Iceberg materialized views** (GA 2025-11-30, 19 regions) — Athena/
  EMR/Glue Spark engines auto-rewrite queries to the MV (up to 8× faster — vendor upper
  bound; refresh is scheduled/eventually-consistent, requires AWS Spark 3.5.6+).
- **EMR Serverless serverless storage** (GA 2025-12-02, requires EMR 7.12+) — no manual
  local-storage provisioning; up to ~20% cheaper (more on shuffle-heavy) and avoids
  disk-capacity job failures. (Spark 4.0.1 is **preview**, 2025-11-21.)
- **Glue zero-ETL → S3 Tables** (GA 2025-07-16, ~14 regions) — from DynamoDB + 8 SaaS apps
  (Salesforce/SAP/ServiceNow/Zendesk…) into S3 Tables (Iceberg), no custom pipeline.
  (Limitations: ~15–30 min lag, KMS required, schema caps.)
- **Amazon QuickSight → Amazon Quick Suite** (global UI/branding GA 2025-10-09) — classic
  BI unchanged (evolution, not migration); new agentic features (Quick Research/Flows/
  Automate/Index) GA in 4 regions (us-east-1, us-west-2, eu-west-1, ap-southeast-2).
- **Amazon Q in QuickSight (generative BI)** +7 regions (GA 2025-07-08) — data stories:
  generate docs/slide decks/exec summaries. **Amazon Data Firehose → S3 Tables** GA 2025-03-14.

> Still **not verified** in-window: **Athena** (engine/provisioned-capacity/federated) and
> **Kinesis Data Streams** (vs Firehose) — not researched, not "quiet"; re-check before
> assuming none. Vendor "up to" figures are AWS-stated, not benchmarked.
> Sources: https://aws.amazon.com/about-aws/whats-new/2025/12/amazon-opensearch-service-gpu-accelerated-auto-optimized-vector-indexes ·
> https://docs.aws.amazon.com/opensearch-service/latest/developerguide/agentic-search.html ·
> https://aws.amazon.com/about-aws/whats-new/2025/11/aws-glue-5-1 ·
> https://aws.amazon.com/about-aws/whats-new/2025/11/aws-apache-iceberg-v3-deletion-vectors-row-lineage ·
> https://aws.amazon.com/about-aws/whats-new/2025/11/aws-glue-apache-iceberg-based-materialized-views/ ·
> https://aws.amazon.com/about-aws/whats-new/2025/12/amazon-emr-serverless-local-storage-provisioning-apache-spark-workloads ·
> https://aws.amazon.com/about-aws/whats-new/2025/07/aws-glue-zero-etl-integrations-amazon-dynamodb-applications-s3-tables ·
> https://aws.amazon.com/blogs/business-intelligence/reimagine-business-intelligence-amazon-quicksight-evolves-to-amazon-quick-suite/ ·
> https://aws.amazon.com/about-aws/whats-new/2025/07/amazon-q-in-quicksight-7-additional-regions/ ·
> https://aws.amazon.com/about-aws/whats-new/2025/03/amazon-data-firehose-real-time-streaming-data-s3-tables/
