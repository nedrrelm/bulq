# Development Notes

## Architecture Decisions

- **Monolithic Backend**: Single FastAPI application, suitable for expected load
- **WebSockets**: For real-time bid updates during group orders
- **No Image Storage**: Avoiding complexity, text-based product descriptions only

## Non-Features (Intentionally Excluded)

- In-app payments (users settle manually)
- Chat functionality (users communicate externally)
- Image uploads/storage

## Design Principles

- Trust-based system for friend groups
- Focus on management and calculation tools
- Keep it simple for initial version

## Future Considerations

- Payment integration if user base grows
- Image support for product catalogs
- Chat if coordination becomes complex