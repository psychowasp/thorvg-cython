# Engine

The `Engine` class manages ThorVG's global initialization and teardown. It must be created before using any other thorvg-cython objects.

## Usage

```python
import thorvg_cython as tvg

# Context manager (recommended) — auto-terminates on exit
with tvg.Engine(threads=4) as engine:
    canvas = tvg.SwCanvas(800, 600)
    # ... render ...

# Manual lifecycle
engine = tvg.Engine(threads=2)
# ... use thorvg ...
engine.term()
```

## Constructor

### `Engine(threads=0)`

Initialize the ThorVG engine.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `threads` | `int` | `0` | Number of worker threads. `0` = single-threaded. |

!!! tip "Thread Count"
    For CPU-bound rendering, set `threads` to your core count. For GPU rendering (`GlCanvas`), threads primarily help with scene preparation.

## Properties

### `init_result`

```python
@property
def init_result(self) -> Result
```

Returns the `Result` from the engine initialization call.

## Methods

### `init(threads=0)`

```python
def init(self, threads: int = 0) -> Result
```

Re-initialize the engine. Rarely needed — prefer creating a new `Engine` instance.

### `term()`

```python
def term(self) -> Result
```

Terminate the engine and release all resources. Called automatically when using the context manager.

### `version()`

```python
def version(self) -> tuple[Result, int, int, int, str | None]
```

Get the ThorVG library version.

**Returns:** `(result, major, minor, micro, version_string)`

```python
with tvg.Engine() as engine:
    result, major, minor, micro, ver = engine.version()
    print(f"ThorVG {ver}")  # e.g., "ThorVG 1.0.5"
```

## Context Manager Protocol

`Engine` implements `__enter__` and `__exit__` for use with the `with` statement. The engine is terminated automatically when the block exits:

```python
with tvg.Engine(threads=4) as engine:
    # Engine is active here
    pass
# Engine is terminated here
```

!!! warning "Singleton Behavior"
    ThorVG uses a global singleton internally. Only one engine should be active at a time. Creating a second `Engine` while one is active may produce unexpected results.
