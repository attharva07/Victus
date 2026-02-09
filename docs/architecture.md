flowchart LR
  %% Victus – Secure Request Processing & Module Architecture (GitHub-safe)

  subgraph Clients
    CLI[CLI]
    WEB[Web App]
    MOB[Mobile App]
    WAT[Watch Client]
  end

  subgraph APIGW["API Gateway"]
    GW["API Gateway<br/>• Input validation<br/>• Request ID generation<br/>• Rate limit precheck<br/>• Request normalization"]
  end

  subgraph AuthID["Auth / Identity"]
    AUTH["Authentication & MFA<br/>• Session / JWT validation<br/>• MFA verification<br/>• User + device context"]
  end

  subgraph PolicyLane["Security / Policy Control"]
    POL["Policy Engine<br/>• Scope resolution<br/>• Allowlist enforcement<br/>• Local / Cloud mode gate<br/>• Risk score<br/>• Decision + reason"]
  end

  subgraph RouteLane["Routing & Safety"]
    IR["Intent Router<br/>• Intent classification<br/>• Action contract selection<br/>• Target module selection"]
    CG["Confidence Gate<br/>• Confidence score<br/>• Risk threshold<br/>• Execute / Clarify / Deny"]
  end

  subgraph ModuleLane["Module Execution"]
    MEM["Memory Service<br/>Requires scope: memory:*"]
    TASKS["Tasks / Reminders<br/>Requires scope: tasks:*"]
    FIN["Finance Service<br/>Isolated domain<br/>Requires scope: finance:*"]
    OSB["OS Bridge<br/>Quarantined<br/>Requires scope: os:control<br/>Allowlisted actions only"]
  end

  subgraph Storage["Storage"]
    APPDB[(App DB)]
    MEMDB[(Memory DB)]
    VECDB[(Vector DB<br/>Embeddings only)]
    FINDB[(Finance DB<br/>Isolated)]
    HOST[Host OS]
    AUD[(Append-only Audit Log)]
  end

  %% Execution flow (solid)
  CLI -->|HTTPS request| GW
  WEB -->|HTTPS request| GW
  MOB -->|HTTPS request| GW
  WAT -->|HTTPS request| GW

  GW --> AUTH --> POL --> IR --> CG

  CG -->|Execute| MEM
  CG -->|Execute| TASKS
  CG -->|Execute| FIN
  CG -->|Execute| OSB

  CG -->|Clarify| GW
  CG -->|Deny| GW

  %% Storage access (solid)
  MEM -->|write/read| MEMDB
  MEM -->|embeddings only| VECDB
  TASKS -->|write/read| APPDB
  FIN -->|write/read only| FINDB
  OSB -->|allowlisted OS actions| HOST

  %% Audit logging (dashed)
  GW -.->|audit event| AUD
  AUTH -.->|audit event| AUD
  POL -.->|audit event| AUD
  IR -.->|audit event| AUD
  CG -.->|audit event| AUD
  MEM -.->|audit event| AUD
  TASKS -.->|audit event| AUD  
  FIN -.->|audit event| AUD
  OSB -.->|audit event| AUD
