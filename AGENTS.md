# Instructions for AI coding agents

pyCamillaDSP is a Python client library for the websocket API of CamillaDSP.
It works with CamillaDSP 5.0 and newer.
The GUI no longer uses it, but scripts and other tools do.

These rules apply to human contributors too.
Read [CONTRIBUTING.md](CONTRIBUTING.md) first.
Where these rules say to ask, an agent should stop and ask its user,
who can then check with the maintainer in an issue.

## Project layout

- `camilladsp/camilladsp.py`: `CamillaClient`, the entry point.
  It groups the commands by topic in properties such as `.config`, `.volume` and `.levels`,
  each an instance of a `_CommandGroup` subclass.
- `camilladsp/camillaws.py`: sending commands, reading replies, and subscriptions.
- One module per command group: `config.py`, `general.py`, `levels.py`, `ratemonitor.py`,
  `settings.py`, `spectrum.py`, `status.py`, `versions.py` and `volume.py`.
- `camilladsp/datastructures.py`: enums and types for the values in replies.
  `camilladsp/exceptions.py`: one exception per error result of the protocol.
- `tests/test_camillaws.py`: tests of the library against a mocked websocket.
- `tests/test_schema.py`: checks the commands and replies against `tests/websocket_schema.json`.
- `docs/`: mkdocs templates. The content is generated from the docstrings.

The websocket protocol is defined in the camilladsp repository,
in `camilladsp-schema/src/protocol.rs`, and described in `docs/websocket.md` there.
Check the protocol there rather than guessing from the existing code.

## Protocol schema

`tests/websocket_schema.json` is a copy of `docs/websocket_schema.json` from camilladsp.
Refresh it whenever the protocol changes, see "Websocket protocol schema" in the README.

- A new command needs a method, an entry in `CALLS` in `tests/test_schema.py`,
  and a reply value in `REPLY_VALUES` if the reply has one.
- Replies in the tests must be ones CamillaDSP can send. Fix a reply that fails the schema,
  do not loosen the check.

## Scope

- Keep the diff as small as the change allows, and do only what the issue or PR is about.
- Do not add dependencies, CI jobs or test infrastructure without asking first.
- Before finishing, go through the diff and ask for each part: is this needed, can it be simpler?

## Breaking changes

Scripts and tools use the public methods of this library, and a change to them breaks those.
Do not rename methods or change their arguments or return values without asking first.
A breaking change in the CamillaDSP protocol does not have to break the Python API.

## Code

- Read the surrounding code first and match it: structure, naming, comment density, idiom.
- A method sends one command with `self.client.query(...)` and returns the value,
  converted to a Python type where that helps.
- Every public method gets a docstring in the style of its module,
  since the docs are generated from them.
- Tests go in the existing test files.

## Commits and pull requests

- Commit subjects are plain imperative sentences, with no `feat:` style prefix.
- Keep PR descriptions short: one summary line and a few bullets.
- Ask which branch to target before starting.

## Validation

Install the development dependencies with `pip install -e ".[dev]"`, then run:

```sh
black camilladsp tests
pylint camilladsp
mypy camilladsp
pytest tests/
```
