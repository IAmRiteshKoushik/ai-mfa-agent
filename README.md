# AI MFA agent

Python 3.13 A2A service managed by uv, using LangGraph and Aerospike checkpoints.
`uv.lock` records the resolved dependency versions.

## Start the service

```sh
uv sync
docker compose up -d
uv run agent
```

Wait for Aerospike to accept connections before starting the service. Startup
opens the Aerospike connection and compiles the graph. Shutdown closes the
connection. Stop local Aerospike with `docker compose down`.

`ENVIRONMENT` selects `local`, `dev`, `sit`, or `prod` and defaults to `local`.
The Aerospike client currently uses the minimal single-node connection in local
and dev environments. For local development, the defaults target the bundled
Docker service at `127.0.0.1:3000` in namespace `test`. Set `AEROSPIKE_HOST`,
`AEROSPIKE_PORT`, and `AEROSPIKE_NAMESPACE` to override those values. The
infra client owns connection cleanup; environment-specific HA, TLS, and
authentication options can be added there as the deployment settings are
defined. Set `A2A_PUBLIC_URL` to the externally reachable JSON-RPC endpoint
that peers should use. Its default is `http://localhost:8000/`.

At startup, the service reads the Agent Card skill from Aerospike. The record
uses namespace `AEROSPIKE_NAMESPACE`, set `AEROSPIKE_AGENT_SKILL_SET` (default
`agent_skills`), and key `AEROSPIKE_AGENT_SKILL_KEY` (default
`mfa-verification`). It must contain string bins `id`, `name`, and
`description`, plus a list of non-empty string values in `tags`. For example,
the record with the default location can be created with Aerospike's AQL:

```sql
INSERT INTO test.agent_skills (PK, id, name, description, tags)
VALUES ('mfa-verification', 'mfa-verification', 'MFA Verification',
        'Authenticate a user via password and OTP verification.',
        ['authentication', 'mfa', 'security', 'password', 'otp'])
```

Change the namespace, set, and key in the statement to match the configured
values. Startup fails with a validation error if the record is missing or its
bins do not match this shape. `AgentSkillConfig` provides the typed application
representation before conversion to the A2A SDK's `AgentSkill`.

## A2A interface

- `GET /.well-known/agent-card.json` publishes the Agent Card.
- `POST /` handles A2A v1.0 JSON-RPC requests through the official SDK.

```sh
curl http://localhost:8000/.well-known/agent-card.json
```

The Agent Card advertises JSON input and text output for the `mfa-journey`
skill. Send one A2A data part containing string fields `user_id` and
`journey_id`. The initial hardcoded journey registry accepts `mfa-login` and
`mfa-recovery`; unknown IDs and missing or empty fields receive an A2A
invalid-params error before graph execution. Both IDs currently reach the same
deterministic decision node, which logs them and returns an acknowledgement.
This flow does not call an LLM or perform MFA actions.

The graph uses the A2A `context_id` as its Aerospike checkpoint thread ID. That
ID identifies the run and remains separate from the reusable journey definition
and the user whose journey is being handled.

Start the interactive prober against the agent with:

```sh
uv run probe
```

Type a message and press Enter to send it over A2A. The response appears in the
REPL; use Ctrl-D or Ctrl-C to exit. Set `MFA_AGENT_URL` to target a different
agent endpoint.

The service returns immediate A2A messages. Streaming and push notifications
are disabled in the card. The SDK's in-memory task store satisfies its handler
interface; this scaffold does not implement durable A2A task management or
authentication. Those remain to be defined before production deployment.

`peer.py` provides outbound Agent Card discovery plus text and structured MFA
journey messaging.

## Files

- `src/graphs/`: graph definitions and state.
- `src/nodes/`: graph node implementations.
- `src/a2a/`: ASGI service, Agent Card, executor, and outbound peer client.
- `src/prober/`: interactive A2A client REPL.
- `src/infra/`: Aerospike checkpoint connection and cleanup.
- `src/config/`: centralized application, Aerospike, and MCP configuration.
- `src/utils/`: reserved for shared utilities.
- `src/mcp/`: named MCP client connections and integrations.

`src` is the Python package. Project A2A modules use `src.a2a` so they do not
shadow the official SDK's `a2a` package.

`src.config.AppConfig.from_env()` loads `.env` (without overriding variables
already exported by the process) and assembles `AerospikeConfig` and
`McpConfig` alongside application URLs. MCP server definitions are then read
from the YAML path selected by `MCP_CONFIG_PATH`.

## MCP connections

`src/mcp/` provides `MCPClientManager` for named, concurrently available MCP
server sessions. Add servers to `src/mcp/servers.yaml`, or point
`MCP_CONFIG_PATH` in `.env` at another YAML file. The example config format is:

```yaml
servers:
  - name: weather
    url: https://weather.example.com/mcp
  - name: internal-tools
    url: http://localhost:8080/mcp
```

Load that file when the graph runtime starts, then make the manager available
to the nodes that need its named clients:

```python
from src.mcp import MCPClientManager

async with MCPClientManager() as mcp:
    clients = await mcp.connect_from_yaml()
    tools = await mcp.get("weather").list_tools()
```

Pass a path to `connect_from_yaml(path)` to override `MCP_CONFIG_PATH`.

Each connection is closed when the manager exits. Configuration-based setup is
all-or-nothing and closes any already opened sessions if a server cannot
connect.
YAML parsing and URL validation live in `src/mcp/config.py`; nodes can call SDK
client methods such as `list_tools`, `call_tool`, `list_resources`, or
`get_prompt`.

## Checks

```sh
uv run ruff check src tests
uv run ruff format --check src tests
uv run python -m unittest discover -s tests -v
```

HTTP tests substitute an in-memory checkpointer for Aerospike. They cover card
discovery, structured message execution, context checkpointing, shutdown
cleanup, and invalid journey input. Live Aerospike persistence remains
unverified.

Integration references: [Aerospike checkpointer](https://github.com/aerospike/langgraph-aerospike)
and [official A2A server setup](https://a2a-protocol.org/v1.0.0/tutorials/python/5-start-server/).
