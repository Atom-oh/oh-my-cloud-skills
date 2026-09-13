"""Shared peer launch policy; never read credential files."""
import os
import re

_PEER_ENV_KEEP = {
    "claude": {"ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "CLAUDE_CODE_OAUTH_TOKEN",
               "ANTHROPIC_CUSTOM_HEADERS", "CLAUDE_CODE_CLIENT_CERT",
               "CLAUDE_CODE_CLIENT_KEY", "CLAUDE_CODE_CLIENT_KEY_PASSPHRASE"},
    "codex": {"OPENAI_API_KEY", "CODEX_API_KEY"},
    "kiro-cli": {"KIRO_API_KEY"},
}
# Retirement removes the peer's allowlist, not credential filtering. These names
# remain scoped so benign-looking project/config variables cannot leak to a peer.
_RETIRED_PEER_AUTH = {
    "GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_GENAI_API_KEY",
    "CLOUDSDK_CONFIG", "GCLOUD_PROJECT", "gcloud_project",
}
CLAUDE_GATE_ISOLATION = (
    "--tools", "Read,Grep,Glob", "--setting-sources", "",
    "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
)
# Standard credential-chain inputs, not an AWS_* wildcard:
# https://docs.aws.amazon.com/sdkref/latest/guide/standardized-credentials.html
# https://docs.aws.amazon.com/sdkref/latest/guide/feature-container-credentials.html
_AWS_AUTH = set("""
    AWS_REGION AWS_DEFAULT_REGION AWS_PROFILE AWS_CONFIG_FILE AWS_SHARED_CREDENTIALS_FILE
    AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN AWS_CREDENTIAL_EXPIRATION
    AWS_ROLE_ARN AWS_ROLE_SESSION_NAME AWS_WEB_IDENTITY_TOKEN_FILE AWS_SDK_LOAD_CONFIG
    AWS_CONTAINER_CREDENTIALS_RELATIVE_URI AWS_CONTAINER_CREDENTIALS_FULL_URI
    AWS_CONTAINER_AUTHORIZATION_TOKEN AWS_CONTAINER_AUTHORIZATION_TOKEN_FILE
    AWS_EC2_METADATA_DISABLED AWS_EC2_METADATA_V1_DISABLED
    AWS_EC2_METADATA_SERVICE_ENDPOINT AWS_EC2_METADATA_SERVICE_ENDPOINT_MODE
    AWS_LOGIN_CACHE_DIRECTORY AWS_CA_BUNDLE AWS_ENDPOINT_URL AWS_ENDPOINT_URL_BEDROCK
    AWS_ENDPOINT_URL_BEDROCK_RUNTIME AWS_ENDPOINT_URL_STS AWS_ENDPOINT_URL_SSO
    AWS_ENDPOINT_URL_SSO_OIDC
""".split())
# GoogleAuth ADC/project discovery, including its documented lowercase aliases:
# https://github.com/googleapis/google-auth-library-nodejs/blob/main/src/auth/googleauth.ts
_GOOGLE_AUTH = set("""
    GOOGLE_APPLICATION_CREDENTIALS google_application_credentials
    GOOGLE_CLOUD_PROJECT google_cloud_project GCLOUD_PROJECT gcloud_project
    GOOGLE_CLOUD_QUOTA_PROJECT CLOUDSDK_CONFIG
""".split())
# Foundry's Azure credential chain: environment, workload/managed identity, CLI.
# https://github.com/Azure/azure-sdk-for-js/tree/main/sdk/identity/identity/src/credentials
_AZURE_AUTH = set("""
    AZURE_CLIENT_ID AZURE_TENANT_ID AZURE_CLIENT_SECRET AZURE_AUTHORITY_HOST
    AZURE_CLIENT_CERTIFICATE_PATH AZURE_CLIENT_CERTIFICATE_PASSWORD
    AZURE_CLIENT_SEND_CERTIFICATE_CHAIN AZURE_ADDITIONALLY_ALLOWED_TENANTS
    AZURE_USERNAME AZURE_PASSWORD AZURE_FEDERATED_TOKEN_FILE AZURE_TOKEN_CREDENTIALS
    AZURE_CONFIG_DIR IDENTITY_ENDPOINT IDENTITY_HEADER IDENTITY_SERVER_THUMBPRINT
    MSI_ENDPOINT MSI_SECRET IMDS_ENDPOINT AZURE_POD_IDENTITY_AUTHORITY_HOST
    ANTHROPIC_FOUNDRY_API_KEY ANTHROPIC_FOUNDRY_AUTH_TOKEN
""".split())
# Backend selectors also present in the official Claude CLI 2.1.268.
_BACKENDS = {
    "BEDROCK": ("aws", _AWS_AUTH | {"AWS_BEARER_TOKEN_BEDROCK"}),
    "MANTLE": ("aws", _AWS_AUTH | {"AWS_BEARER_TOKEN_BEDROCK"}),
    "ANTHROPIC_AWS": ("aws", _AWS_AUTH | {"ANTHROPIC_AWS_API_KEY"}),
    "VERTEX": ("google", _GOOGLE_AUTH),
    "ANTHROPIC_GOOGLE_CLOUD": ("google", _GOOGLE_AUTH),
    "FOUNDRY": ("azure", _AZURE_AUTH),
}
# Some auth inputs (e.g. IDENTITY_HEADER) do not look like secrets by name.
_SCOPED_ENV = set().union(_RETIRED_PEER_AUTH, *_PEER_ENV_KEEP.values(),
                        *(keys for _, keys in _BACKENDS.values()))
# Match credential names without stripping benign PATH/PWD/KEYBOARD variables.
_SENSITIVE_ENV_RE = re.compile(
    r"TOKEN|SECRET|PASSWORD|PASSWD|CREDENTIAL|PRIVATE_KEY|API_?KEY|"
    r"(?:^|_)KEY(?![A-Za-z])|(?:^|_)PAT(?![A-Za-z])|_PWD(?![A-Za-z])|"
    r"^AWS_|^GOOGLE_|^GCP_|^AZURE_|^GH_|^GITHUB_", re.I)


def sanitized_env(peer):
    """Keep only this peer's auth and explicitly selected Claude cloud auth.

    Preserve HOME/PATH and other ordinary runtime settings. Absolute-path file
    reads and custom credential-process dependencies remain outside this filter.
    """
    keep = set(_PEER_ENV_KEEP.get(peer, ()))
    if peer == "claude":
        selected = [value for name, value in _BACKENDS.items()
                    if os.environ.get("CLAUDE_CODE_USE_" + name, "").strip().lower()
                    in ("1", "true", "yes", "on")]
        if len({family for family, _ in selected}) > 1:
            raise ValueError("select one Claude cloud backend family before probing or reviewing")
        for _, keys in selected:
            keep.update(keys)
    return {key: value for key, value in os.environ.items()
            if key in keep or (key not in _SCOPED_ENV and not _SENSITIVE_ENV_RE.search(key))}
