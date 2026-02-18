# AI Risk-Constrained Autonomous DeFi Agent

Autonomous DeFi portfolio management with AI-driven allocation, composable on-chain risk policies, and post-execution verification. The system uses AI models to suggest yield allocations, a risk engine to constrain them, and smart contracts to enforce safety invariants on-chain.

## Architecture

- **contracts/** — Solidity (Foundry). Composable policy system, ERC-4626 vault, Safe modules.
- **risk-engine/** — Pure Python risk computation (VaR, CVaR, stress testing).
- **ai/** — ML pipeline for allocation suggestions (regime detection, portfolio optimization).
- **backend/** — FastAPI orchestration service.
- **indexer/** — Subgraph definitions (The Graph).
- **monitoring/** — Prometheus + Grafana + Alertmanager.

## Quick Start

### Contracts
```bash
cd contracts
forge build
forge test -vvv
```

### Backend (Docker)
```bash
cd backend
docker compose up -d
```
