# Database Schema

## Entity Relationship Diagram

```mermaid
erDiagram
    User {
        uuid id PK
        string name
        string email
        timestamp created_at
        timestamp updated_at
    }
    
    Group {
        uuid id PK
        string name
        string description
        uuid created_by FK
        timestamp created_at
        timestamp updated_at
    }
    
    Run {
        uuid id PK
        uuid group_id FK
        uuid store_id FK
        string state
        json designated_shoppers
        text delivery_info
        timestamp created_at
        timestamp updated_at
    }
    
    Store {
        uuid id PK
        string name
        string location
        timestamp created_at
        timestamp updated_at
    }
    
    Product {
        uuid id PK
        uuid store_id FK
        string name
        decimal base_price
        timestamp created_at
        timestamp updated_at
    }
    
    ProductBid {
        uuid id PK
        uuid user_id FK
        uuid run_id FK
        uuid product_id FK
        integer quantity
        boolean interested_only
        timestamp created_at
        timestamp updated_at
    }
    
    GroupMembership {
        uuid user_id FK
        uuid group_id FK
        timestamp joined_at
    }

    User ||--o{ GroupMembership : "belongs to"
    Group ||--o{ GroupMembership : "has members"
    Group ||--o{ Run : "organizes"
    Store ||--o{ Run : "targeted by"
    Store ||--o{ Product : "sells"
    User ||--o{ ProductBid : "places"
    Run ||--o{ ProductBid : "contains"
    Product ||--o{ ProductBid : "receives"
    User ||--o{ Group : "creates"
```

## Run States

- `planning` - Initial state, collecting product interest
- `active` - Users placing bids, quantities being tracked
- `confirmed` - Thresholds met, shopping list finalized
- `shopping` - Designated shoppers executing the run
- `completed` - Run finished, costs calculated
- `cancelled` - Run cancelled before completion

## Key Relationships

- **Users ↔ Groups**: Many-to-many via GroupMembership
- **Groups → Runs**: One group can have multiple runs
- **Runs → Store**: Each run targets a specific store
- **Store → Products**: Products belong to specific stores
- **ProductBids**: Junction of User + Run + Product with quantity/interest data