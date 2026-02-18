CLAUDE.md — AI Risk-Constrained Autonomous DeFi Agent
Project Overview
This is an autonomous DeFi portfolio management system that uses AI models to suggest yield allocations, a risk engine to constrain them, and on-chain smart contracts to enforce safety invariants. The system manages real capital — every design decision must prioritize security over convenience.
The architecture has five layers: Data → AI Decision → Risk Engine → Execution (on-chain) → Monitoring. Each layer is independently deployable and testable.

Monorepo Structure
/
├── contracts/              # Foundry project — all Solidity
│   ├── src/
│   │   ├── policies/       # Composable policy contracts (NOT a monolithic Guardrail)
│   │   │   ├── IPolicyManager.sol
│   │   │   ├── PolicyManager.sol
│   │   │   ├── MaxExposurePolicy.sol
│   │   │   ├── CumulativeSlippagePolicy.sol
│   │   │   ├── WhitelistPolicy.sol
│   │   │   └── OracleCircuitBreakerPolicy.sol
│   │   ├── vault/
│   │   │   └── Treasury.sol          # ERC-4626 vault with post-execution verification
│   │   ├── execution/
│   │   │   ├── ExecutionRouter.sol    # Safe Module for constrained agent execution
│   │   │   └── AgentGuard.sol        # Safe Guard for pre/post-execution checks
│   │   └── governance/
│   │       └── AgentTimelock.sol     # TimelockController for privileged operations
│   ├── test/
│   ├── script/             # Forge deployment scripts
│   ├── foundry.toml
│   └── remappings.txt
├── backend/                # FastAPI orchestration service
│   ├── app/
│   │   ├── api/            # REST endpoints
│   │   ├── services/       # Business logic (proposal pipeline, tx submission)
│   │   ├── models/         # SQLAlchemy models (decision audit trail)
│   │   └── config.py       # Environment-based configuration
│   ├── docker-compose.yml
│   └── pyproject.toml
├── risk-engine/            # Pure Python risk computation package
│   ├── risk_engine/
│   │   ├── var.py          # VaR / CVaR calculators
│   │   ├── stress.py       # Scenario-based stress testing
│   │   ├── correlation.py  # Rolling correlation monitor
│   │   └── evaluator.py    # Proposal approve/reject logic
│   └── pyproject.toml
├── ai/                     # ML pipeline for allocation suggestions
│   ├── ai_agent/
│   │   ├── features.py     # Feature engineering
│   │   ├── regime.py       # HMM regime classifier
│   │   ├── optimizer.py    # Portfolio optimizer (MVO + Black-Litterman)
│   │   ├── registry.py     # Model versioning and registry
│   │   └── logger.py       # Decision logging with hash commitments
│   └── pyproject.toml
├── indexer/                # Subgraph definitions (The Graph)
├── monitoring/             # Prometheus + Grafana configs
│   ├── prometheus/
│   ├── grafana/dashboards/
│   └── alertmanager/
└── CLAUDE.md               # THIS FILE

Technology Stack
Smart Contracts

Solidity 0.8.25+ (use named imports, custom errors, no string reverts)
Foundry (forge, cast, anvil) — NOT Hardhat
OpenZeppelin v5 (contracts + contracts-upgradeable)
Safe (Gnosis Safe) smart accounts — Modules, Guards, Zodiac Roles Module
Chainlink oracles + Automation for circuit breakers

Backend

Python 3.12, FastAPI, SQLAlchemy (PostgreSQL), Redis
web3.py for chain interaction
All packages share types via a common types/ package

AI / Risk Engine

numpy, scipy, pandas, scikit-learn, pytorch
MLflow for model registry
All functions must be pure and deterministic for same inputs

Infrastructure

Docker Compose for local dev (API + PostgreSQL + Redis + Prometheus + Grafana)
GitHub Actions CI for both Solidity (forge test, slither) and Python (pytest, mypy)


Architecture Principles (Read Before Writing Any Code)
1. Composable Policies, NOT a Monolithic Guardrail
NEVER create a single Guardrail contract. The policy system is modular:

PolicyManager chains multiple independent policy contracts
Each policy (exposure cap, slippage limit, whitelist, circuit breaker) is its own deployable contract
New policies can be added without touching existing ones
Modeled on Enzyme Finance's PolicyManager pattern

2. Post-Execution State Verification
Every strategy execution MUST be followed by a state check:
Before: snapshot totalAssets
Execute: run strategy call
After: verify |newTotalAssets - oldTotalAssets| <= maxDeviationBps
If violated: REVERT entire transaction
This is inspired by Sommelier's Cellar pattern and catches malicious/erroneous execution.
3. AI Never Holds Keys
The AI layer PROPOSES allocations. It never signs or submits transactions.

Execution flows through a Safe smart account with constrained Modules
The ExecutionRouter is a Safe Module with scoped permissions
AgentGuard enforces policy checks on every Module-initiated transaction
Multi-sig owners set boundaries; the agent operates within them

4. Separation of Authorities
Three distinct roles, held by DIFFERENT addresses — enforced by tests:

ADMIN: upgrade contracts, add/remove policies (behind 48hr timelock)
EXECUTOR: submit approved proposals for on-chain execution
GUARDIAN: emergency pause only (bypasses timelock)

No single address may hold more than one of these roles.
5. Off-Chain/On-Chain Trust Boundary
The off-chain system is untrusted from the on-chain perspective:

On-chain policies validate EVERY transaction regardless of source
Transactions include nonce + expiry block (reject stale proposals)
Decision records are hashed (SHA-256) and anchored on-chain for auditability
All on-chain state changes emit events

6. MEV Protection
ALL swaps and DeFi interactions MUST route through private mempools:

Use Flashbots Protect RPC or MEV Blocker for transaction submission
On-chain slippage checks: transactions revert if realized slippage > expected + tolerance
For DEX operations, prefer CoW Protocol batch auctions when possible

7. Oracle Strategy
Never rely on a single price source:

Primary: Chainlink price feeds
Secondary: Pyth Network
Tertiary: On-chain TWAP (Uniswap V3)
Cross-verify: if feeds diverge > threshold bps, pause operations
Staleness check: revert if feed is older than configurable maxAge
L2: check Chainlink Sequencer Uptime Feed before trusting L2 prices


Smart Contract Coding Standards
DO:

Use OpenZeppelin v5 contracts (AccessControl, Pausable, ReentrancyGuard, ERC4626, TimelockController)
Use custom errors (error MaxExposureExceeded(address protocol, uint256 requested, uint256 limit);)
Use named imports (import {ERC4626} from "@openzeppelin/contracts/token/ERC20/extensions/ERC4626.sol";)
Emit events for ALL state changes
Add NatSpec to every external/public function
Use uint256 for all numeric types unless there's a specific packing reason
Pin pragma to exact version: pragma solidity 0.8.25;
Use checks-effects-interactions pattern

DO NOT:

Use string reverts (require(x, "message")) — use custom errors
Use transfer() or send() — use call() with reentrancy guards
Use delegatecall unless absolutely necessary and thoroughly tested
Hardcode addresses — use constructor injection or immutable variables
Use floating pragma (^0.8.0)
Create a monolithic Guardrail contract
Use block.timestamp for randomness (use for time-based checks only)

Testing Requirements (Foundry):

Unit tests for every external function
Fuzz tests for any function accepting numeric inputs (minimum 1000 runs)
Invariant tests for:

Share accounting: totalAssets >= totalSupply * minSharePrice (accounting for rounding)
Policy consistency: active policies count matches registry
Role separation: no address holds ADMIN + EXECUTOR + GUARDIAN simultaneously


Integration tests: full flow from proposal → policy check → execution → post-check → event
Fork tests against mainnet state for protocol integrations
Gas snapshots for all critical paths

Static Analysis:
After writing contracts, always run:
bashslither . --filter-paths "lib|test|script"
Address all High and Medium findings. Document any accepted Low findings.

Python Coding Standards
ALL Python code must:

Be 100% type-annotated (enforce with mypy --strict)
Use pydantic for all data models and configuration
Log structured JSON with correlation IDs
Never hardcode secrets — use environment variables via pydantic-settings
Pin all dependencies with exact versions in pyproject.toml

Risk Engine specific:

All computation functions must be pure (no side effects, no API calls)
Same inputs must ALWAYS produce same outputs (pin random seeds)
Functions return typed result objects, not raw dicts
Test with >90% coverage, including edge cases (empty data, NaN, extreme values)

AI Pipeline specific:

Every model version tracked in registry: git hash, data hash, hyperparameters, metrics, timestamp
Decision logger captures: inputs snapshot, model version, raw output, risk verdict, final action
SHA-256 hash of each decision record for on-chain anchoring
Shadow mode: new models run in parallel before promotion
Drift detection: alert when PSI > 0.1, halt when PSI > 0.25

Backend specific:

Every endpoint authenticated (API key + HMAC)
Rate limiting on all write endpoints
Full decision audit trail in PostgreSQL
Transaction signing via injected signer (NEVER import private keys in code)
Multi-provider RPC with failover (primary + 2 fallbacks)
Structured logging with request correlation IDs


Key Management (CRITICAL)
Production Target Architecture:
Multi-sig Owners (hardware wallets)
    └── Safe Smart Account ($50B+ in assets secured by Safe globally)
        ├── Module: ExecutionRouter (agent executes within policy constraints)
        ├── Guard: AgentGuard (validates every tx against PolicyManager)
        ├── Module: Delay Module (time delays on sensitive operations)
        └── Module: Zodiac Roles (per-agent function-level permissions)
For Development:

Use Anvil with deterministic accounts
.env.example with placeholder values, .env in .gitignore
Test scripts use vm.addr() and vm.sign() — never real keys

For Deployment:

MPC wallet (Fireblocks, Fordefi) for multi-sig owners
ERC-4337 session keys for time-limited agent access
Hardware-backed signing for any human-initiated transaction
Separate hot wallet for gas funding only (minimal balance)


Deployment & Upgrade Safety
Deployment Order:

TimelockController (with ADMIN multisig as proposer + executor, GUARDIAN as canceller)
PolicyManager (owned by Timelock)
Individual Policy contracts (registered in PolicyManager via Timelock proposal)
Treasury vault (references PolicyManager)
Safe Smart Account (with ExecutionRouter as Module, AgentGuard as Guard)

Upgrade Process:

All upgradeable contracts use UUPS proxy pattern (OpenZeppelin)
Upgrades require Timelock proposal → 48hr delay → execution
New implementations must pass ALL existing tests + new tests for changes
Slither must report no new High/Medium findings
Deployments scripted with forge script — never manual


Protocol Integrations (Whitelisted)
When integrating with external DeFi protocols, always:

Use official verified contract addresses (check Etherscan)
Interact through typed interfaces — never raw call()
Add protocol-specific guard validation (dHEDGE GOAT pattern):

For Aave: validate supply(), withdraw() function selectors only
For Compound: validate mint(), redeem() selectors only
Reject any unexpected function selectors


Set per-protocol exposure caps in MaxExposurePolicy
Fork-test against mainnet state before deployment


Common Pitfalls to Avoid
MistakeWhy It Kills YouWhat To Do InsteadSingle oracle sourceOracle manipulation = instant drainMulti-oracle with cross-verification + circuit breakerPublic mempool txsSandwich attacks extract valueFlashbots Protect / MEV BlockerMonolithic guardrailUpgrade risk + single point of failureComposable policy contractsAI holds signing keysCompromised model = stolen fundsSafe Module with scoped permissionsNo post-execution checkMalicious strategy drains vault undetectedSommelier-style totalAssets deviation revertSame role on multiple signersSocial engineering of one person = total compromiseSeparate ADMIN / EXECUTOR / GUARDIANNo timelock on upgradesBybit-class attack ($1.4B stolen Feb 2025)48hr minimum delay on all privileged opsString revertsWasted gas + no programmatic error handlingCustom errors with parametersTrusting block.timestampMiner manipulation riskUse for relative time only, not randomnessSingle RPC providerProvider outage = system offlineMulti-provider with automatic failover

Testing Quick Reference
Solidity (Foundry):
bash# Run all tests
forge test -vvv

# Run specific test
forge test --match-test testMaxExposurePolicy -vvv

# Fuzz with more runs
forge test --match-test testFuzz --fuzz-runs 10000

# Invariant tests
forge test --match-test invariant

# Gas snapshot
forge snapshot

# Static analysis
slither . --filter-paths "lib|test|script"

# Fork testing
forge test --fork-url $ETH_RPC_URL --match-test testFork
Python:
bash# Risk engine tests
cd risk-engine && pytest -v --cov=risk_engine --cov-report=term-missing

# AI pipeline tests
cd ai && pytest -v --cov=ai_agent

# Backend tests
cd backend && pytest -v --cov=app

# Type checking
mypy --strict risk-engine/risk_engine/ ai/ai_agent/ backend/app/

File Naming Conventions

Solidity: PascalCase (PolicyManager.sol, MaxExposurePolicy.sol)
Python: snake_case (var_calculator.py, decision_logger.py)
Tests (Solidity): {ContractName}.t.sol
Tests (Python): test_{module}.py
Deployment scripts: Deploy{Component}.s.sol
Interfaces: I{ContractName}.sol


Environment Variables
env# Chain
ETH_RPC_URL=                    # Primary RPC (Alchemy/Infura)
ETH_RPC_FALLBACK_1=             # Fallback RPC 1
ETH_RPC_FALLBACK_2=             # Fallback RPC 2
CHAIN_ID=1

# MEV Protection
FLASHBOTS_RPC=https://rpc.flashbots.net

# Signing (NEVER hardcode)
SAFE_ADDRESS=
EXECUTOR_PRIVATE_KEY=           # Loaded from HSM/vault in production

# Backend
DATABASE_URL=postgresql://...
REDIS_URL=redis://localhost:6379
API_SECRET_KEY=                 # For HMAC authentication

# Monitoring
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
ALERT_SLACK_WEBHOOK=

# AI
MODEL_REGISTRY_PATH=./mlflow
DECISION_LOG_PATH=./logs/decisions/

Regulatory Awareness
This system will likely qualify as high-risk AI under the EU AI Act (applicable August 2026) if it manages assets for EU persons. Design for compliance now:

Decision logging: every AI decision must be reproducible and auditable
Human oversight: emergency pause + human review before resumption
Drift monitoring: automated detection with halt capability
Model documentation: training data lineage, methodology, validation results
Risk management: continuous monitoring throughout lifecycle

The Federal Reserve's SR 11-7 model risk management guidance also applies if interfacing with any regulated financial institution.

Definition of Done (For Any Component)
Before considering a component complete:

 All unit tests pass
 Fuzz tests pass (1000+ runs for Solidity)
 Invariant tests defined and passing
 Integration test with adjacent components
 NatSpec / docstrings on all public interfaces
 No High/Medium Slither findings (Solidity) or mypy errors (Python)
 Events emitted for all state changes (Solidity)
 Structured logging with correlation IDs (Python)
 Gas snapshot recorded (Solidity)
 Edge cases tested (zero values, max values, empty arrays, reentrancy)