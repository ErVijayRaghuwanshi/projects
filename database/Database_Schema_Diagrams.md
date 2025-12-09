# Target Anomalies Database Schema Diagrams

**Version:** 3.0  
**Date:** December 8, 2025  
**PostgreSQL Version:** 14.17  
**Schema:** iadbschema  
**System:** Sunshine IPR 2.0 - Target Anomaly Detection (TAD)

---

## Table of Contents

1. [Complete Entity Relationship Diagram](#1-complete-entity-relationship-diagram)
2. [Schema Organization](#2-schema-organization)
3. [Rule-Based System Schema](#3-rule-based-system-schema)
4. [Behavior-Based System Schema](#4-behavior-based-system-schema)
5. [Table Dependency Graph](#5-table-dependency-graph)
6. [Index and Constraint Diagram](#6-index-and-constraint-diagram)
7. [Data Flow Diagram](#7-data-flow-diagram)

---

## 1. Complete Entity Relationship Diagram

### Full Schema ERD

```mermaid
erDiagram
    %% ========================================
    %% SHARED TABLES (Core Target Management)
    %% ========================================
    
    tad_target_groups {
        INTEGER group_id PK "Primary Key"
        VARCHAR(255) name UK "Unique group name"
        TEXT description "Group description"
        TIMESTAMP created_at "Default: CURRENT_TIMESTAMP"
        TIMESTAMP updated_at "Default: CURRENT_TIMESTAMP"
        INTEGER training_days "Default: 7"
        BOOLEAN is_enabled "Default: true"
        VARCHAR(20) group_type "RULE or BEHAVIOR"
        VARCHAR(100) created_by "User who created"
        TEXT users "Comma-separated user list"
    }
    
    tad_targets {
        INTEGER target_id PK "Composite PK with group_id"
        INTEGER group_id "PK FK Composite PK, FK to groups"
        VARCHAR(100) mobile_number "Target phone number"
        TIMESTAMP created_at "Default: CURRENT_TIMESTAMP"
        VARCHAR(100) target_name "Default: 'A'"
    }
    
    %% ========================================
    %% RULE-BASED TABLES
    %% ========================================
    
    tad_rules {
        SERIAL rule_id PK "Auto-increment PK"
        VARCHAR(255) name "Rule name"
        TEXT description "Rule description"
        VARCHAR(50) rule_type "Type of rule"
        VARCHAR(50) data_source "Data source identifier"
        BOOLEAN is_enabled "Default: true"
        TEXT configurable_field "Nullable"
        TEXT sql_template "SQL query template"
        TIMESTAMP created_at "Default: now()"
        TIMESTAMP updated_at "Nullable"
        TEXT info "Additional info, nullable"
        VARCHAR(50) type "Default: 'predefined'"
    }
    
    tad_column_master {
        INTEGER field_id PK "Primary Key"
        VARCHAR(100) field_name "Unique field name"
        VARCHAR(100) display_name "UI display name"
        VARCHAR(50) field_type "Data type"
        VARCHAR(50) ui_component "UI component type"
        TEXT available_operators "Nullable"
        TEXT group_subfields "Nullable"
        TIMESTAMP created_at "Default: now()"
        TIMESTAMP updated_at "Nullable"
    }
    
    tad_rule_configuration {
        SERIAL configuration_id PK "Auto-increment PK"
        INTEGER rule_id FK "FK to tad_rules"
        INTEGER field_id FK "FK to tad_column_master"
        TEXT default_value "Nullable"
        BOOLEAN is_mandatory "Default: false"
        BOOLEAN is_editable "Default: true"
        TEXT selected_operator "Nullable"
        TIMESTAMP created_at "Default: now()"
        TIMESTAMP updated_at "Nullable"
        BOOLEAN is_operator_editable "Default: false"
    }
    
    tad_target_group_rules {
        INTEGER group_id "PK FK Composite PK, FK to groups"
        INTEGER rule_id "PK FK Composite PK, FK to rules"
        VARCHAR(255) name "Nullable"
        VARCHAR(255) unique_name PK "Composite PK"
        JSONB custom_params "Rule parameters"
        TIMESTAMP added_at "Default: CURRENT_TIMESTAMP"
        TIMESTAMP updated_at "Default: CURRENT_TIMESTAMP"
        JSONB helper_json "Helper data, nullable"
    }
    
    %% ========================================
    %% BEHAVIOR-BASED TABLES
    %% ========================================
    
    tad_insight {
        INTEGER insight_id PK "Primary Key"
        VARCHAR(100) insight_name UK "Unique insight name"
        VARCHAR(200) insight_display_name "Display name, nullable"
        TEXT description "Nullable"
        TIMESTAMP created_at "Default: CURRENT_TIMESTAMP"
        TIMESTAMP updated_at "Default: CURRENT_TIMESTAMP"
    }
    
    tad_dimensions {
        INTEGER dimension_id PK "Primary Key"
        VARCHAR(100) dimension_name UK "Unique dimension name"
        VARCHAR(200) dimension_display_name "Display name, nullable"
        TEXT description "Nullable"
        TIMESTAMP created_at "Default: CURRENT_TIMESTAMP"
        TIMESTAMP updated_at "Default: CURRENT_TIMESTAMP"
    }
    
    tad_criteria {
        INTEGER criteria_id PK "Primary Key"
        VARCHAR(100) criteria_name UK "Unique criteria name"
        VARCHAR(200) criteria_display_name "Display name, nullable"
        TEXT description "Nullable"
        TIMESTAMP created_at "Default: CURRENT_TIMESTAMP"
        TIMESTAMP updated_at "Default: CURRENT_TIMESTAMP"
    }
    
    tad_behaviors_mapping {
        INTEGER behavior_id PK "Primary Key"
        INTEGER insight_id FK "FK to tad_insight"
        INTEGER dimension_id FK "FK to tad_dimensions"
        INTEGER criteria_id FK "FK to tad_criteria"
        TEXT sql_template "SQL query template"
        VARCHAR(200) template_name "Nullable"
        TEXT description "Nullable"
        BOOLEAN is_active "Default: true"
        TIMESTAMP created_at "Default: CURRENT_TIMESTAMP"
        TIMESTAMP updated_at "Default: CURRENT_TIMESTAMP"
    }
    
    tad_target_group_behaviors {
        INTEGER group_id "PK FK Composite PK, FK to groups"
        INTEGER behavior_id "PK FK Composite PK, FK to behaviors"
        TIMESTAMP created_at "Default: CURRENT_TIMESTAMP"
        TIMESTAMP updated_at "Default: CURRENT_TIMESTAMP"
    }
    
    %% ========================================
    %% RELATIONSHIPS
    %% ========================================
    
    %% Shared Relationships
    tad_target_groups ||--o{ tad_targets : "contains (group_id)"
    tad_target_groups ||--o{ tad_target_group_rules : "has rules (group_id)"
    tad_target_groups ||--o{ tad_target_group_behaviors : "has behaviors (group_id)"
    
    %% Rule-Based Relationships
    tad_rules ||--o{ tad_rule_configuration : "configured by (rule_id)"
    tad_rules ||--o{ tad_target_group_rules : "assigned to groups (rule_id)"
    tad_column_master ||--o{ tad_rule_configuration : "defines fields (field_id)"
    
    %% Behavior-Based Relationships
    tad_insight ||--o{ tad_behaviors_mapping : "mapped to (insight_id)"
    tad_dimensions ||--o{ tad_behaviors_mapping : "mapped to (dimension_id)"
    tad_criteria ||--o{ tad_behaviors_mapping : "mapped to (criteria_id)"
    tad_behaviors_mapping ||--o{ tad_target_group_behaviors : "assigned to groups (behavior_id)"
```

---

## 2. Schema Organization

### Logical Schema Layers

```mermaid
graph TB
    subgraph "iadbschema - PostgreSQL 14.17"
        subgraph "Shared Layer - Target Management"
            A[tad_target_groups<br/>Group definitions]
            B[tad_targets<br/>Target phone numbers]
        end
        
        subgraph "Rule-Based Layer"
            C[tad_rules<br/>Rule definitions]
            D[tad_column_master<br/>Field metadata]
            E[tad_rule_configuration<br/>Rule-field mapping]
            F[tad_target_group_rules<br/>Group-rule assignments]
        end
        
        subgraph "Behavior-Based Layer"
            G[tad_insight<br/>Behavior catalog]
            H[tad_dimensions<br/>Analytical dimensions]
            I[tad_criteria<br/>Metrics/criteria]
            J[tad_behaviors_mapping<br/>Valid combinations]
            K[tad_target_group_behaviors<br/>Group-behavior assignments]
        end
    end
    
    %% Shared relationships
    A -->|1:N| B
    A -->|1:N| F
    A -->|1:N| K
    
    %% Rule relationships
    C -->|1:N| E
    C -->|1:N| F
    D -->|1:N| E
    
    %% Behavior relationships
    G -->|1:N| J
    H -->|1:N| J
    I -->|1:N| J
    J -->|1:N| K
    
    style A fill:#558b2f,stroke:#c5e1a5,stroke-width:2px
    style B fill:#558b2f,stroke:#c5e1a5,stroke-width:2px
    style C fill:#a35174,stroke:#f8bbd0,stroke-width:2px
    style D fill:#a35174,stroke:#f8bbd0,stroke-width:2px
    style E fill:#a35174,stroke:#f8bbd0,stroke-width:2px
    style F fill:#a35174,stroke:#f8bbd0,stroke-width:2px
    style G fill:#4682b4,stroke:#b3e5fc,stroke-width:2px
    style H fill:#4682b4,stroke:#b3e5fc,stroke-width:2px
    style I fill:#4682b4,stroke:#b3e5fc,stroke-width:2px
    style J fill:#4682b4,stroke:#b3e5fc,stroke-width:2px
    style K fill:#4682b4,stroke:#b3e5fc,stroke-width:2px
```

### Table Count by Category

| Category | Tables | Purpose |
|----------|--------|---------|
| **Shared** | 2 | Core target group and target management |
| **Rule-Based** | 4 | Rule definition, configuration, and assignment |
| **Behavior-Based** | 5 | Behavior catalog, mapping, and assignment |
| **Total** | **11** | Complete TAD system |

---

## 3. Rule-Based System Schema

### Rule System ERD (Detailed)

```mermaid
erDiagram
    tad_target_groups ||--o{ tad_target_group_rules : "group_id"
    tad_target_groups ||--o{ tad_targets : "group_id"
    
    tad_rules ||--o{ tad_rule_configuration : "rule_id"
    tad_rules ||--o{ tad_target_group_rules : "rule_id"
    
    tad_column_master ||--o{ tad_rule_configuration : "field_id"
    
    tad_target_groups {
        INTEGER group_id PK
        VARCHAR(255) name UK
        VARCHAR(20) group_type "Must be 'RULE'"
        INTEGER training_days
        BOOLEAN is_enabled
    }
    
    tad_targets {
        INTEGER target_id PK
        INTEGER group_id "PK FK"
        VARCHAR(100) mobile_number
        VARCHAR(100) target_name
    }
    
    tad_rules {
        SERIAL rule_id PK
        VARCHAR(255) name
        TEXT description
        VARCHAR(50) rule_type
        VARCHAR(50) data_source
        BOOLEAN is_enabled
        TEXT sql_template
        VARCHAR(50) type "predefined/custom"
    }
    
    tad_column_master {
        INTEGER field_id PK
        VARCHAR(100) field_name
        VARCHAR(100) display_name
        VARCHAR(50) field_type
        VARCHAR(50) ui_component
        TEXT available_operators
    }
    
    tad_rule_configuration {
        SERIAL configuration_id PK
        INTEGER rule_id FK
        INTEGER field_id FK
        TEXT default_value
        BOOLEAN is_mandatory
        BOOLEAN is_editable
        TEXT selected_operator
        BOOLEAN is_operator_editable
    }
    
    tad_target_group_rules {
        INTEGER group_id "PK FK"
        INTEGER rule_id "PK FK"
        VARCHAR(255) unique_name PK
        VARCHAR(255) name
        JSONB custom_params
        JSONB helper_json
    }
```

### Rule Configuration Flow

```mermaid
graph LR
    A[tad_rules<br/>Rule Definition] --> B[tad_rule_configuration<br/>Field Mappings]
    C[tad_column_master<br/>Field Metadata] --> B
    B --> D[tad_target_group_rules<br/>Group Assignment]
    E[tad_target_groups<br/>Target Group] --> D
    
    style A fill:#8b3e3e,stroke:#ff7f7f,stroke-width:2px
    style B fill:#8b6d3e,stroke:#ffdd77,stroke-width:2px
    style C fill:#4a7e52,stroke:#9ff2a8,stroke-width:2px
    style D fill:#3e6a8b,stroke:#7fa8ff,stroke-width:2px
    style E fill:#6a3e8b,stroke:#c4a5d8,stroke-width:2px
```

---

## 4. Behavior-Based System Schema

### Behavior System ERD (Detailed)

```mermaid
erDiagram
    tad_target_groups ||--o{ tad_target_group_behaviors : "group_id"
    tad_target_groups ||--o{ tad_targets : "group_id"
    
    tad_insight ||--o{ tad_behaviors_mapping : "insight_id"
    tad_dimensions ||--o{ tad_behaviors_mapping : "dimension_id"
    tad_criteria ||--o{ tad_behaviors_mapping : "criteria_id"
    
    tad_behaviors_mapping ||--o{ tad_target_group_behaviors : "behavior_id"
    
    tad_target_groups {
        INTEGER group_id PK
        VARCHAR(255) name UK
        VARCHAR(20) group_type "Must be 'BEHAVIOR'"
        INTEGER training_days
        BOOLEAN is_enabled
    }
    
    tad_targets {
        INTEGER target_id PK
        INTEGER group_id "PK FK"
        VARCHAR(100) mobile_number
        VARCHAR(100) target_name
    }
    
    tad_insight {
        INTEGER insight_id PK
        VARCHAR(100) insight_name UK
        VARCHAR(200) insight_display_name
        TEXT description
    }
    
    tad_dimensions {
        INTEGER dimension_id PK
        VARCHAR(100) dimension_name UK
        VARCHAR(200) dimension_display_name
        TEXT description
    }
    
    tad_criteria {
        INTEGER criteria_id PK
        VARCHAR(100) criteria_name UK
        VARCHAR(200) criteria_display_name
        TEXT description
    }
    
    tad_behaviors_mapping {
        INTEGER behavior_id PK
        INTEGER insight_id FK
        INTEGER dimension_id FK
        INTEGER criteria_id FK
        TEXT sql_template
        VARCHAR(200) template_name
        BOOLEAN is_active
    }
    
    tad_target_group_behaviors {
        INTEGER group_id "PK FK"
        INTEGER behavior_id "PK FK"
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }
```

### Behavior Mapping Flow

```mermaid
graph TB
    A[tad_insight<br/>CDR Calls, SMS, etc.] --> D[tad_behaviors_mapping<br/>Valid Combinations]
    B[tad_dimensions<br/>Time, Location, etc.] --> D
    C[tad_criteria<br/>Count, Duration, etc.] --> D
    D --> E[tad_target_group_behaviors<br/>Group Assignment]
    F[tad_target_groups<br/>Target Group] --> E
    
    style A fill:#8b3e3e,stroke:#ff7f7f,stroke-width:2px
    style B fill:#3e6a8b,stroke:#7fa8ff,stroke-width:2px
    style C fill:#4a7e52,stroke:#9ff2a8,stroke-width:2px
    style D fill:#8b6d3e,stroke:#ffdd77,stroke-width:2px
    style E fill:#6a3e8b,stroke:#c4a5d8,stroke-width:2px
    style F fill:#3e8b8b,stroke:#7fffff,stroke-width:2px
```

### Behavior Combination Matrix

```mermaid
graph LR
    subgraph "Insight Layer"
        I1[CDR Calls]
        I2[SMS Activity]
        I3[Location]
    end
    
    subgraph "Dimension Layer"
        D1[Time]
        D2[Frequency]
        D3[Volume]
    end
    
    subgraph "Criteria Layer"
        C1[Call Count]
        C2[Duration]
        C3[Unique Contacts]
    end
    
    subgraph "Mapping Layer"
        M[tad_behaviors_mapping<br/>Validates combinations]
    end
    
    I1 --> M
    I2 --> M
    I3 --> M
    D1 --> M
    D2 --> M
    D3 --> M
    C1 --> M
    C2 --> M
    C3 --> M
    
    style M fill:#8b6d3e,stroke:#ff9e8a,stroke-width:4px
```

---

## 5. Table Dependency Graph

### Creation Order and Dependencies

```mermaid
graph TD
    subgraph "Level 0 - Independent Tables"
        A[tad_target_groups]
        B[tad_rules]
        C[tad_column_master]
        D[tad_insight]
        E[tad_dimensions]
        F[tad_criteria]
    end
    
    subgraph "Level 1 - Single Dependency"
        G[tad_targets<br/>depends on: target_groups]
        H[tad_rule_configuration<br/>depends on: rules, column_master]
        I[tad_behaviors_mapping<br/>depends on: insight, dimensions, criteria]
    end
    
    subgraph "Level 2 - Multiple Dependencies"
        J[tad_target_group_rules<br/>depends on: target_groups, rules]
        K[tad_target_group_behaviors<br/>depends on: target_groups, behaviors_mapping]
    end
    
    %% Dependencies
    A --> G
    A --> J
    A --> K
    
    B --> H
    B --> J
    
    C --> H
    
    D --> I
    E --> I
    F --> I
    
    I --> K
    
    style A fill:#4a7e52,stroke:#c5e1a5,stroke-width:2px
    style B fill:#a35174,stroke:#f8bbd0,stroke-width:2px
    style C fill:#a35174,stroke:#f8bbd0,stroke-width:2px
    style D fill:#3e6a8b,stroke:#b3e5fc,stroke-width:2px
    style E fill:#3e6a8b,stroke:#b3e5fc,stroke-width:2px
    style F fill:#3e6a8b,stroke:#b3e5fc,stroke-width:2px
    style G fill:#4a7e52,stroke:#c5e1a5,stroke-width:2px
    style H fill:#a35174,stroke:#f8bbd0,stroke-width:2px
    style I fill:#3e6a8b,stroke:#b3e5fc,stroke-width:2px
    style J fill:#4a7e52,stroke:#c5e1a5,stroke-width:2px
    style K fill:#3e6a8b,stroke:#b3e5fc,stroke-width:2px
```

### Drop Order (Reverse Dependency)

```mermaid
graph TD
    A[1. DROP tad_target_group_behaviors] --> B[2. DROP tad_target_group_rules]
    B --> C[3. DROP tad_targets]
    C --> D[4. DROP tad_behaviors_mapping]
    D --> E[5. DROP tad_rule_configuration]
    E --> F[6. DROP tad_criteria]
    F --> G[7. DROP tad_dimensions]
    G --> H[8. DROP tad_insight]
    H --> I[9. DROP tad_column_master]
    I --> J[10. DROP tad_rules]
    J --> K[11. DROP tad_target_groups]
    
    style A fill:#8b3e3e,stroke:#ff7f7f,stroke-width:2px
    style K fill:#b00000,stroke:#ff7f7f,stroke-width:2px
```

---

## 6. Index and Constraint Diagram

### Indexes Overview

```mermaid
graph TB
    subgraph "Primary Key Indexes (Auto-created)"
        PK1[tad_target_groups.group_id]
        PK2[tad_targets.target_id + group_id]
        PK3[tad_rules.rule_id]
        PK4[tad_column_master.field_id]
        PK5[tad_rule_configuration.configuration_id]
        PK6[tad_target_group_rules.group_id + rule_id + unique_name]
        PK7[tad_insight.insight_id]
        PK8[tad_dimensions.dimension_id]
        PK9[tad_criteria.criteria_id]
        PK10[tad_behaviors_mapping.behavior_id]
        PK11[tad_target_group_behaviors.group_id + behavior_id]
    end
    
    subgraph "Unique Indexes"
        UK1[tad_target_groups.name]
        UK2[tad_insight.insight_name]
        UK3[tad_dimensions.dimension_name]
        UK4[tad_criteria.criteria_name]
        UK5[tad_behaviors_mapping.insight_id + dimension_id + criteria_id]
    end
    
    subgraph "Custom Indexes"
        IDX1[idx_tad_column_master_field_name<br/>ON field_name]
        IDX2[idx_tad_rule_config_field_id<br/>ON field_id]
        IDX3[idx_tad_rule_config_rule_id<br/>ON rule_id]
        IDX4[idx_mapping_insight<br/>ON insight_id]
        IDX5[idx_mapping_dimension<br/>ON dimension_id]
        IDX6[idx_mapping_criteria<br/>ON criteria_id]
        IDX7[idx_tgb_group<br/>ON group_id]
        IDX8[idx_tgb_created_at<br/>ON created_at]
    end
    
    style PK1 fill:#4a7e52,stroke:#c5e1a5,stroke-width:2px
    style PK2 fill:#4a7e52,stroke:#c5e1a5,stroke-width:2px
    style UK1 fill:#8b6d3e,stroke:#ffdd77,stroke-width:2px
    style UK2 fill:#8b6d3e,stroke:#ffdd77,stroke-width:2px
    style IDX1 fill:#3e6a8b,stroke:#b3e5fc,stroke-width:2px
    style IDX2 fill:#3e6a8b,stroke:#b3e5fc,stroke-width:2px
```

### Foreign Key Constraints

```mermaid
graph LR
    subgraph "Rule System FKs"
        R1[tad_rule_configuration] -->|rule_id| R2[tad_rules]
        R1 -->|field_id| R3[tad_column_master]
        R4[tad_target_group_rules] -->|rule_id| R2
        R4 -->|group_id| R5[tad_target_groups]
    end
    
    subgraph "Behavior System FKs"
        B1[tad_behaviors_mapping] -->|insight_id| B2[tad_insight]
        B1 -->|dimension_id| B3[tad_dimensions]
        B1 -->|criteria_id| B4[tad_criteria]
        B5[tad_target_group_behaviors] -->|behavior_id| B1
        B5 -->|group_id| R5
    end
    
    subgraph "Shared FKs"
        T1[tad_targets] -->|group_id| R5
    end
    
    style R2 fill:#a35174,stroke:#f8bbd0,stroke-width:2px
    style R3 fill:#a35174,stroke:#f8bbd0,stroke-width:2px
    style R5 fill:#4a7e52,stroke:#c5e1a5,stroke-width:2px
    style B2 fill:#3e6a8b,stroke:#b3e5fc,stroke-width:2px
    style B3 fill:#3e6a8b,stroke:#b3e5fc,stroke-width:2px
    style B4 fill:#3e6a8b,stroke:#b3e5fc,stroke-width:2px
```

### Constraint Summary Table

| Table | Primary Key | Foreign Keys | Unique Constraints | Check Constraints |
|-------|-------------|--------------|-------------------|-------------------|
| **tad_target_groups** | group_id | - | name | - |
| **tad_targets** | target_id, group_id | group_id → tad_target_groups | - | - |
| **tad_rules** | rule_id | - | - | - |
| **tad_column_master** | field_id | - | - | - |
| **tad_rule_configuration** | configuration_id | rule_id → tad_rules<br/>field_id → tad_column_master | - | - |
| **tad_target_group_rules** | group_id, rule_id, unique_name | group_id → tad_target_groups<br/>rule_id → tad_rules | - | - |
| **tad_insight** | insight_id | - | insight_name | - |
| **tad_dimensions** | dimension_id | - | dimension_name | - |
| **tad_criteria** | criteria_id | - | criteria_name | - |
| **tad_behaviors_mapping** | behavior_id | insight_id → tad_insight<br/>dimension_id → tad_dimensions<br/>criteria_id → tad_criteria | insight_id + dimension_id + criteria_id | - |
| **tad_target_group_behaviors** | group_id, behavior_id | group_id → tad_target_groups<br/>behavior_id → tad_behaviors_mapping | - | - |

---

## 7. Data Flow Diagram

### Rule-Based Data Flow

```mermaid
graph TB
    A[User Creates Rule Group] --> B[tad_target_groups<br/>group_type = 'RULE']
    B --> C[Add Targets]
    C --> D[tad_targets<br/>mobile numbers]
    
    E[Select Rule] --> F[tad_rules<br/>rule definition]
    F --> G[Load Configuration]
    G --> H[tad_rule_configuration<br/>field mappings]
    I[tad_column_master<br/>field metadata] --> H
    
    H --> J[Configure Parameters]
    J --> K[tad_target_group_rules<br/>custom_params JSONB]
    B --> K
    
    K --> L[Daily Processing]
    L --> M[Generate SQL from template]
    M --> N[Execute on Data Sources]
    
    style B fill:#4a7e52,stroke:#c5e1a5,stroke-width:2px
    style D fill:#4a7e52,stroke:#c5e1a5,stroke-width:2px
    style F fill:#a35174,stroke:#f8bbd0,stroke-width:2px
    style H fill:#a35174,stroke:#f8bbd0,stroke-width:2px
    style K fill:#a35174,stroke:#f8bbd0,stroke-width:2px
    style N fill:#b04f37,stroke:#ff9e8a,stroke-width:2px
```

### Behavior-Based Data Flow

```mermaid
graph TB
    A[User Creates Behavior Group] --> B[tad_target_groups<br/>group_type = 'BEHAVIOR']
    B --> C[Add Targets]
    C --> D[tad_targets<br/>mobile numbers]
    
    E[Select Insight] --> I[tad_insight]
    F[Select Dimension] --> J[tad_dimensions]
    G[Select Criteria] --> K[tad_criteria]
    
    I --> L[tad_behaviors_mapping<br/>validate combination]
    J --> L
    K --> L
    
    L --> M[tad_target_group_behaviors<br/>assign to group]
    B --> M
    
    M --> N[Daily Processing]
    N --> O[Calculate Baseline Statistics]
    O --> P[Detect Anomalies]
    
    style B fill:#4a7e52,stroke:#c5e1a5,stroke-width:2px
    style D fill:#4a7e52,stroke:#c5e1a5,stroke-width:2px
    style I fill:#3e6a8b,stroke:#b3e5fc,stroke-width:2px
    style J fill:#3e6a8b,stroke:#b3e5fc,stroke-width:2px
    style K fill:#3e6a8b,stroke:#b3e5fc,stroke-width:2px
    style L fill:#4a8b8e,stroke:#8cd9e5,stroke-width:2px
    style M fill:#4a8b8e,stroke:#8cd9e5,stroke-width:2px
    style P fill:#2f4f8d,stroke:#6a9eff,stroke-width:2px
```

### Combined System Architecture

```mermaid
graph TB
    subgraph "Shared Core"
        A[tad_target_groups]
        B[tad_targets]
    end
    
    subgraph "Rule Path"
        C[tad_rules]
        D[tad_column_master]
        E[tad_rule_configuration]
        F[tad_target_group_rules]
    end
    
    subgraph "Behavior Path"
        G[tad_insight]
        H[tad_dimensions]
        I[tad_criteria]
        J[tad_behaviors_mapping]
        K[tad_target_group_behaviors]
    end
    
    subgraph "Processing Layer"
        L[Rule Processor]
        M[Behavior Processor]
    end
    
    subgraph "Output"
        N[(Anomaly Database)]
        O[(Solr Index)]
    end
    
    A --> B
    A --> F
    A --> K
    
    C --> E
    D --> E
    E --> F
    
    G --> J
    H --> J
    I --> J
    J --> K
    
    F --> L
    K --> M
    
    L --> N
    L --> O
    M --> N
    M --> O
    
    style A fill:#4a7e52,stroke:#c5e1a5,stroke-width:3px
    style B fill:#4a7e52,stroke:#c5e1a5,stroke-width:3px
    style C fill:#a35174,stroke:#f8bbd0,stroke-width:2px
    style D fill:#a35174,stroke:#f8bbd0,stroke-width:2px
    style E fill:#a35174,stroke:#f8bbd0,stroke-width:2px
    style F fill:#a35174,stroke:#f8bbd0,stroke-width:2px
    style G fill:#3e6a8b,stroke:#b3e5fc,stroke-width:2px
    style H fill:#3e6a8b,stroke:#b3e5fc,stroke-width:2px
    style I fill:#3e6a8b,stroke:#b3e5fc,stroke-width:2px
    style J fill:#3e6a8b,stroke:#b3e5fc,stroke-width:2px
    style K fill:#3e6a8b,stroke:#b3e5fc,stroke-width:2px
    style L fill:#b04f37,stroke:#ff9e8a,stroke-width:2px
    style M fill:#2f4f8d,stroke:#6a9eff,stroke-width:2px
    style N fill:#4a7e52,stroke:#c5e1a5,stroke-width:2px
    style O fill:#8b6d3e,stroke:#ffdd77,stroke-width:2px
```

---

## Schema Statistics

### Table Size Estimates

| Table | Estimated Rows | Growth Rate | Notes |
|-------|---------------|-------------|-------|
| **tad_target_groups** | 100-500 | Low | One per investigation group |
| **tad_targets** | 1,000-10,000 | Medium | Multiple targets per group |
| **tad_rules** | 50-200 | Low | Predefined + custom rules |
| **tad_column_master** | 30-50 | Very Low | Field definitions |
| **tad_rule_configuration** | 200-1,000 | Low | Rule × Fields |
| **tad_target_group_rules** | 500-5,000 | Medium | Groups × Rules |
| **tad_insight** | 10-20 | Very Low | Behavior categories |
| **tad_dimensions** | 5-10 | Very Low | Analytical dimensions |
| **tad_criteria** | 15-30 | Very Low | Metrics |
| **tad_behaviors_mapping** | 50-200 | Low | Valid combinations |
| **tad_target_group_behaviors** | 200-2,000 | Medium | Groups × Behaviors |

### Sequence Information

| Sequence | Table | Column | Current Strategy |
|----------|-------|--------|------------------|
| **tad_rule_configuration_configuration_id_seq** | tad_rule_configuration | configuration_id | INCREMENT 1, START 1, CACHE 1 |
| **tad_rules_rule_id_seq** | tad_rules | rule_id | Auto-created by SERIAL |

---

## Color Legend

- 🟢 **Green** - Shared/Core tables
- 🔴 **Red/Pink** - Rule-based system tables
- 🔵 **Blue** - Behavior-based system tables
- 🟡 **Yellow** - Configuration/Metadata tables
- 🟣 **Purple** - Junction/Mapping tables

---

## Notes

1. **PostgreSQL Version**: Schema requires PostgreSQL 14.0 or higher
2. **Schema Name**: All tables reside in `iadbschema`
3. **Cascade Deletes**: 
   - `tad_target_group_rules` has `ON DELETE CASCADE` for `group_id`
   - `tad_behaviors_mapping` has `ON DELETE CASCADE` for all FKs
4. **JSONB Columns**: 
   - `tad_target_group_rules.custom_params` - Stores rule parameters
   - `tad_target_group_rules.helper_json` - Stores helper data
5. **Composite Primary Keys**:
   - `tad_targets`: (target_id, group_id)
   - `tad_target_group_rules`: (group_id, rule_id, unique_name)
   - `tad_target_group_behaviors`: (group_id, behavior_id)

---

**Document End**
