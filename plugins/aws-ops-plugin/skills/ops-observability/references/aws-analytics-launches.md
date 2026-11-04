# Recent AWS analytics launches (2025–2026)

Reference data for `analytics-agent`. Vendor "up to" figures are AWS-stated, not benchmarked.
Re-check region and feature availability against the live docs before scripting against any of it.

Launch news already covered by official skills is not repeated here. See official
`aws-data-analytics:amazon-opensearch-service` (GPU vector indexes, Agentic Search),
`aws-data-analytics:ingesting-into-data-lake` (Glue 5.1, Iceberg, EMR Serverless storage) and
`aws-data-analytics:creating-data-lake-table`.

- **Glue zero-ETL -> S3 Tables** (GA 2025-07-16, ~14 regions) — from DynamoDB + 8 SaaS apps
  into S3 Tables (Iceberg), no custom pipeline. (Limitations: ~15–30 min lag, KMS required,
  schema caps.)
- **Amazon QuickSight -> Amazon Quick Suite** (global UI/branding GA 2025-10-09) — classic
  BI unchanged (evolution, not migration); new agentic features (Quick Research/Flows/
  Automate/Index) GA in 4 regions (us-east-1, us-west-2, eu-west-1, ap-southeast-2).
- **Amazon Q in QuickSight (generative BI)** +7 regions (GA 2025-07-08) — data stories.
  **Amazon Data Firehose -> S3 Tables** GA 2025-03-14.

> Still **not verified** in-window: **Athena** (engine/provisioned-capacity/federated) and
> **Kinesis Data Streams** (vs Firehose); re-check before assuming none.
> Sources: https://aws.amazon.com/about-aws/whats-new/2025/07/aws-glue-zero-etl-integrations-amazon-dynamodb-applications-s3-tables ·
> https://aws.amazon.com/blogs/business-intelligence/reimagine-business-intelligence-amazon-quicksight-evolves-to-amazon-quick-suite/ ·
> https://aws.amazon.com/about-aws/whats-new/2025/07/amazon-q-in-quicksight-7-additional-regions/ ·
> https://aws.amazon.com/about-aws/whats-new/2025/03/amazon-data-firehose-real-time-streaming-data-s3-tables/
