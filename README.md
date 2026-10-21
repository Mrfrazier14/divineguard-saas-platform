# DivineGuard SaaS Platform

Shared AWS CloudFormation starter infrastructure for GovCon Pulse and Gray Fox AI. This repository defines a foundation; the application repositories are not deployed or connected by this template.

## Resources

- Cognito user pool with email sign-in, admin-created users, strong passwords, optional software-token MFA and a public client using SRP (no client secret).
- DynamoDB on-demand table with `PK`/`SK`, encryption, point-in-time recovery and deletion protection.
- Private versioned S3 assets bucket with encryption, blocked public access and a deny policy for insecure transport.
- Python Lambda health function, limited concurrency, a 14-day log group and a role limited to writing its logs. No public function URL, API Gateway, data-access permissions or deployment workflow is created.

Identity, table and bucket are retained on deletion/replacement. Retention can leave billable resources after stack deletion; use the cleanup instructions below.

## Validate locally

Follow development setup below, then run:

```sh
cfn-lint infra/template.json
```

Structural tests and CloudFormation linting do not prove deployment or runtime access in your AWS account.

## AWS setup and deployment

Requires AWS CLI v2, an AWS account/region, and an authorized SSO profile with CloudFormation, IAM role creation/PassRole, Cognito, DynamoDB, S3, Lambda and CloudWatch Logs provisioning permissions. Use short-lived SSO credentials; do not paste AWS access keys into chat or commit them.

```sh
aws configure sso --profile divineguard-dev
aws sso login --profile divineguard-dev
export AWS_PROFILE=divineguard-dev
export AWS_REGION=us-west-2
aws sts get-caller-identity
aws cloudformation validate-template --template-body file://infra/template.json
aws cloudformation deploy --stack-name divineguard-saas-dev --template-file infra/template.json --capabilities CAPABILITY_IAM --no-execute-changeset
# Review the generated change set in CloudFormation, including region/account and costs.
# When ready, rerun without --no-execute-changeset to execute the deployment.
aws cloudformation describe-stacks --stack-name divineguard-saas-dev --query 'Stacks[0].Outputs'
```

The script does not read `.env` automatically. `.env.example` documents shell settings and the outputs to copy into private application configuration. A change set may create billable resources when executed. Billing alerts are notifications, not a hard spending cap; configure an AWS Budget and appropriate quotas before launch.

After deployment, invoke the `HealthFunctionName` output through `aws lambda invoke --function-name FUNCTION_NAME /tmp/divineguard-health.json`, inspect the returned payload, confirm the bucket is private and test Cognito sign-in with an admin-created test user. Deployment and these account-level smoke checks remain to be performed.

## Tenant contract and application integration

Planned keys: `PK = TENANT#<verified-tenant-id>` and `SK = OPPORTUNITY#<id>` or another domain entity key. This is a convention only. It does not enforce isolation. Build an authenticated API, validate Cognito access tokens and audience/issuer, resolve server-side tenant membership, enforce every query and mutation, and test cross-tenant denial before storing real data.

Add application-specific roles with the minimum table/bucket/secret permissions. This foundation intentionally has no runtime access to table or bucket. Store Anthropic/OpenAI API keys in Secrets Manager or another approved secret store; grant retrieval only to the backend that needs them. No provider secrets, GitHub OIDC role, API authorizer, app hosting, DNS/TLS, billing integration or CI deployment is included.

## Cleanup and recovery

Back up/export required records before teardown. `aws cloudformation delete-stack --stack-name divineguard-saas-dev` deletes disposable resources but retains Cognito, DynamoDB and S3. Inventory retained resources and their costs. To remove them deliberately, first export data, disable DynamoDB deletion protection, empty every S3 object version/delete marker and delete each retained resource through its service. Never automate destructive cleanup against production data. Restore drills and resource import after replacement remain operational work.

Official resource references: [Cognito user pool](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-cognito-userpool.html), [DynamoDB table](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-dynamodb-table.html).

## Repository family

| Repository | Responsibility |
| --- | --- |
| [GovCon Pulse](https://github.com/Mrfrazier14/divineguard-govcon-pulse) | Local opportunity tracking and evidence links |
| [Gray Fox AI](https://github.com/Mrfrazier14/divineguard-gray-fox-ai) | Server-side Anthropic and OpenAI adapters |
| [SaaS Platform](https://github.com/Mrfrazier14/divineguard-saas-platform) | Shared AWS identity, storage and runtime foundation |

## Development

Python 3.12-3.14 is required for the pinned infrastructure tools. Each repository has its own environment; run commands from its root.

```sh
python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
```

GitHub Actions runs tests on Python 3.12 and 3.14. `.env`, local databases, virtual environments and AWS configuration are ignored. `.env.example` contains placeholders only. Never commit keys, credentials, customer data or bid evidence containing private information.

Read [architecture](docs/ARCHITECTURE.md) for the future integration boundary. These are new starter implementations; they do not migrate the earlier desktop application or hosted pilot. No production readiness, live billing, bid submission or deployed AWS service is implied.
