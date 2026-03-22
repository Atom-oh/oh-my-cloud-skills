---
remarp: true
block: canvas-demo
---

@type: cover
@background: linear-gradient(135deg, #161D26 0%, #0d1117 50%, #1a2332 100%)

# Canvas Animation Demo
AWS Observability 서비스 맵 & 아키텍처 시각화

@speaker: Remarp Demo
@speaker-title: Interactive Presentation Framework

---
@type: canvas
@canvas-id: obs-service-map

## AWS Observability 서비스 맵

:::canvas
icon cw "CloudWatch" at 80,120 size 48 step 1
box collect "Collect" at 55,180 size 100,35 color #41B3FF step 1

icon guru "DevOpsGuru" at 272,120 size 48 step 2
box analyze "Analyze" at 247,180 size 100,35 color #AD5CFF step 2

icon anomaly "CloudWatch" at 464,120 size 48 step 3
box detect "Detect" at 439,180 size 100,35 color #FF5C85 step 3

icon xray "X-Ray" at 656,120 size 48 step 4
box trace "Trace" at 631,180 size 100,35 color #00E500 step 4

icon eb "EventBridge" at 848,120 size 48 step 5
box act "Act" at 823,180 size 100,35 color #FF693C step 5

arrow collect -> analyze "metrics" step 6
arrow analyze -> detect "insights" step 6
arrow detect -> trace "traces" step 7
arrow trace -> act "events" step 7
:::

---
@type: canvas
@canvas-id: serverless-arch

## Serverless Event-Driven Architecture

:::canvas
box apigw "API Gateway" at 60,150 size 130,40 color #41B3FF step 1
box lambda "Lambda" at 260,150 size 130,40 color #FF9900 step 2
box dynamo "DynamoDB" at 460,150 size 130,40 color #4053D6 step 3
box sns "SNS" at 460,60 size 130,40 color #FF4F8B step 4
box sqs "SQS" at 660,60 size 130,40 color #FF4F8B step 4
box s3 "S3" at 460,240 size 130,40 color #3F8624 step 5

arrow apigw -> lambda "invoke" step 6
arrow lambda -> dynamo "read/write" step 6
arrow lambda -> sns "publish" step 7
arrow sns -> sqs "fanout" step 7
arrow lambda -> s3 "store" step 8
:::
