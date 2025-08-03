# Application Layer

This directory contains the application layer implementation following CQRS (Command Query Responsibility Segregation) pattern with Domain-Driven Design principles.

## Structure

```
application/
├── commands/           # Command definitions
│   ├── base.py        # Base command classes and interfaces
│   ├── game_commands.py     # Game-related commands
│   ├── analysis_commands.py # Analysis-related commands
│   └── training_commands.py # Training-related commands
├── handlers/          # Command handlers
│   ├── game_command_handlers.py     # Game command handlers
│   ├── analysis_command_handlers.py # Analysis command handlers
│   └── training_command_handlers.py # Training command handlers
├── queries/           # Query definitions (TBD)
├── validators/        # Command validators
│   └── command_validators.py # Validation logic for commands
├── decorators/        # Decorators for cross-cutting concerns
│   └── transactional.py # Transaction management
├── services/          # Application services
│   └── command_bus.py # Command bus for routing and orchestration
└── dto/              # Data Transfer Objects (TBD)
```

## Key Components

### Commands

Commands represent user intentions and are immutable data structures:
- `CreateGameCommand` - Create a new OFC game
- `PlaceCardCommand` - Place a card in player's layout
- `RequestAnalysisCommand` - Request strategy analysis
- `StartTrainingSessionCommand` - Start a training session

### Command Handlers

Each command has a corresponding handler that:
1. Validates business rules
2. Orchestrates domain services
3. Manages transactions
4. Publishes domain events
5. Returns results

### Command Bus

The `CommandBus` provides:
- Command routing to appropriate handlers
- Automatic validation via validators
- Transaction management
- Middleware support (logging, metrics, auth)
- Consistent error handling

### Validation

Command validators ensure:
- Required fields are present
- Values are within valid ranges
- Referenced entities exist
- Business rules are satisfied

### Transaction Management

The `@transactional` decorator ensures:
- All database operations within a handler use the same transaction
- Automatic rollback on errors
- Configurable isolation levels
- Unit of Work pattern support

## Usage Example

```python
# Create command bus
command_bus = (
    CommandBusBuilder()
    .with_handler(CreateGameCommand, CreateGameCommandHandler(...))
    .with_validator(CreateGameCommand, CreateGameCommandValidator(...))
    .with_logging()
    .with_metrics(metrics_collector)
    .build()
)

# Execute command
command = CreateGameCommand(
    player_ids=["player1", "player2"],
    rules=GameRules(),
    game_variant="standard"
)

result = await command_bus.execute(command)

if result.success:
    game_id = result.data["game_id"]
else:
    error = result.error
```

## Testing

Integration tests are provided in `tests/application/handlers/`:
- `test_game_command_handlers.py` - Game command handler tests
- `test_analysis_command_handlers.py` - Analysis command handler tests
- `test_command_bus.py` - Command bus integration tests

## Design Principles

1. **Separation of Concerns**: Commands, handlers, and validation are separate
2. **Single Responsibility**: Each handler handles one command type
3. **Dependency Injection**: All dependencies injected via constructor
4. **Async/Await**: Full async support for scalability
5. **Error Handling**: Consistent error handling and result types
6. **Testability**: All components are easily testable

## Future Enhancements

- [ ] Query handlers for read operations
- [ ] Event sourcing support
- [ ] Saga/Process managers for long-running workflows
- [ ] Command versioning
- [ ] Command replay/audit log