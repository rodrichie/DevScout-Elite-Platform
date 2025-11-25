# Clean Architecture Implementation

## Architecture Overview

This refactored codebase follows **Clean Architecture** (aka Hexagonal/Ports & Adapters) with proper separation of concerns and dependency injection.

## Layers

### 1. Domain Layer (`api/domain/`)
- **Pure business logic**, framework-independent
- **Entities** (`entities.py`): Core business objects (Candidate, Skill, etc.)
- **Repository Interfaces** (`repositories.py`): Abstract contracts for data access
- **Business rules**: Validation logic in entities
- **No dependencies** on infrastructure or frameworks

### 2. Application Layer (`api/application/`)
- **Use Cases** (`use_cases.py`): Application-specific business logic
- **Orchestrates** domain entities and repositories
- Each use case follows **Single Responsibility Principle**
- **Query objects**: Type-safe request parameters
- **Dependencies**: Only on domain layer interfaces

### 3. Infrastructure Layer (`api/infrastructure/`)
- **Adapters** that implement domain interfaces
- **PostgreSQL Repositories** (`postgres_repositories.py`): Concrete implementations
- **Dependency Container** (`container.py`): DI configuration
- **Framework-specific** code isolated here
- **Depends on**: Domain interfaces (Dependency Inversion)

### 4. Presentation Layer (`api/routers/`)
- **Thin controllers** that delegate to use cases
- **DTOs** (Data Transfer Objects): Request/response models
- **Mappers**: Convert between domain entities and DTOs
- **HTTP concerns only**: Routing, status codes, validation
- **No business logic** in controllers

## SOLID Principles Applied

### Single Responsibility Principle (SRP)
- Each use case handles one specific operation
- Repositories handle only data access
- Controllers handle only HTTP concerns

### Open/Closed Principle (OCP)
- System open for extension via new use cases
- Closed for modification via stable interfaces

### Liskov Substitution Principle (LSP)
- Repository implementations are interchangeable
- Can swap PostgreSQL for MongoDB without changing business logic

### Interface Segregation Principle (ISP)
- Separate repository interfaces for each entity
- Clients depend only on methods they use

### Dependency Inversion Principle (DIP)
- High-level modules (use cases) depend on abstractions (interfaces)
- Low-level modules (repositories) implement abstractions
- Dependencies injected via constructor

## Dependency Injection

### Container Pattern
```python
container = get_container(db)
use_case = container.get_candidate_use_case()
result = await use_case.execute(query)
```

### Benefits
- **Testability**: Easy to mock dependencies
- **Flexibility**: Swap implementations without code changes
- **Maintainability**: Clear dependency graph
- **Decoupling**: Components know only interfaces

## Testing Strategy

### Unit Tests (Easy with DI)
```python
# Mock repository
mock_repo = Mock(spec=ICandidateRepository)
mock_repo.get_by_id.return_value = test_candidate

# Test use case in isolation
use_case = GetCandidateUseCase(mock_repo)
result = await use_case.execute(query)

assert result == test_candidate
```

### Integration Tests
```python
# Use real repository with test database
repo = PostgreSQLCandidateRepository(test_session)
use_case = GetCandidateUseCase(repo)
```

## Domain-Driven Design (DDD)

### Value Objects
```python
@dataclass(frozen=True)
class CandidateId:
    """Immutable identifier with validation."""
    value: int
```

### Entities
```python
@dataclass
class Candidate:
    """Business entity with behavior."""
    def calculate_experience_score(self) -> float:
        # Domain logic in entity
```

### Repository Pattern
```python
class ICandidateRepository(ABC):
    """Contract for data access."""
    @abstractmethod
    async def get_by_id(self, id: CandidateId) -> Optional[Candidate]:
        pass
```

## Migration Path

### Phase 1: New Clean Endpoints ✅
- Created parallel clean architecture implementation
- New routers in `candidates_clean.py`
- Can run alongside existing code

### Phase 2: Gradual Migration (Next)
1. Add new endpoints to main.py
2. Update client code to use clean endpoints
3. Keep old endpoints for backward compatibility
4. Monitor and test

### Phase 3: Complete Refactor
1. Migrate all routers to clean architecture
2. Remove old coupled code
3. Add comprehensive unit tests
4. Update documentation

## Code Comparison

### Before (Tight Coupling)
```python
@router.get("/{candidate_id}")
def get_candidate(candidate_id: int, db: Session = Depends(get_db)):
    # SQL query directly in route handler
    result = db.execute(text("""
        SELECT * FROM silver.candidates WHERE candidate_id = :id
    """), {"id": candidate_id})
    # Manual data mapping
    row = result.fetchone()
    return {"id": row[0], "name": row[1], ...}
```

### After (Clean Architecture)
```python
@router.get("/{candidate_id}")
async def get_candidate(candidate_id: int, db: Session = Depends(get_db)):
    # Delegate to use case
    container = get_container(db)
    use_case = container.get_candidate_use_case()
    
    query = GetCandidateQuery(candidate_id=candidate_id)
    candidate = await use_case.execute(query)
    
    return map_candidate_to_response(candidate)
```

## Benefits Achieved

### Testability
- Unit tests without database
- Mock dependencies easily
- Fast test execution

### Maintainability
- Changes isolated to single layer
- Clear responsibility boundaries
- Easy to understand flow

### Flexibility
- Swap database without changing business logic
- Add new features without modifying existing code
- Support multiple data sources

### Scalability
- Clear separation enables team collaboration
- Independent layer deployment possible
- Easier to optimize specific layers

## Next Steps

1. **Add Unit Tests**: Test use cases with mocked repositories
2. **Migrate More Endpoints**: Apply pattern to jobs, skills, GitHub endpoints
3. **Add Service Layer**: For complex multi-entity operations
4. **Implement Event Sourcing**: For audit trails
5. **Add CQRS**: Separate read/write models if needed
