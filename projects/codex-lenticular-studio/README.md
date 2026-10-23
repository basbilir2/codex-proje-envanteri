# Lenticular Studio

Python and web tools for lenticular print preparation: photo/depth inputs, scene and camera planning, multi-view rendering, animation workflows and interlacing.

The goal is to make specialized print-production workflows easier to inspect, reproduce and maintain for small print shops and creators. Lens pitch, print resolution and physical dimensions are explicit inputs. Software checks do not replace a physical print/lens calibration test.

## Start here

| Resource | Purpose |
| --- | --- |
| [Current source](source/current/) | Python package, Studio interface, tools and tests |
| [Installation](KURULUM.md) | Dependencies and reconstruction notes |
| [Architecture](MIMARI.md) | Pipeline and module map |
| [Known limitations](EKSIKLER.md) | Missing dependencies and validation limits |
| [Roadmap](ROADMAP.md) | Maintenance goals and proposed development agent |
| [Contributing](CONTRIBUTING.md) | Reproducible issues and focused changes |

## Development setup

Python 3.10+ is required by the package manifest. From `source/current`, create an isolated environment and install the package:

```sh
python -m venv .venv
# Activate the environment for your operating system.
python -m pip install -e .
lenticular-studio --help
```

Depth models, Blender and animation backends may require separate setup; see the installation guide before running a render. Fresh-machine installation and physical print quality have not been verified for this public snapshot.

## Maintenance and API-credit plan

The primary maintainer is [basbilir2](https://github.com/basbilir2). Proposed API use is repository-grounded code assistance, issue triage, regression-test development, code/security review, documentation and reproducible release preparation. A planned development agent would work across this project, DTF/Design Recovery and order/stock/cost applications, with scoped changes, relevant checks and human approval before publication or deployment.

This is an early public project. No community adoption, download volume or universal physical-print accuracy is claimed. Credits would support measurable maintenance work, rather than replace project evidence.

## License and privacy

Original contributions are [MIT licensed](LICENSE). Third-party code and models retain [their own terms](THIRD_PARTY_NOTICES.md). This repository contains an independently created, sanitized source snapshot. Private history, customer data, personal identifiers, API keys and account settings are excluded. Historical source variants under `source/` are not a chronological public Git history.
