# Design Recovery / Netleştirme

An experimental Node/Python application for understanding and reconstructing artwork from photos, mockups and low-quality design sources. It aims to preserve the design's lettering, figures, composition, geometry and colors while removing fabric texture, folds, lighting and perspective.

Source-preserving extraction and AI reconstruction are distinct workflows. Sharpening, upscaling and background removal are auxiliary operations.

## Project guide

- [Current application and training source](source/current/)
- [Latest status and validation limits](CURRENT_STATUS.md)
- [Installation and dependencies](KURULUM.md)
- [Architecture and module map](MIMARI.md)
- [Known limitations](EKSIKLER.md)
- [Contribution guidelines](CONTRIBUTING.md)

## Application setup

Inspect `source/current/app/package.json`, `runtime-config.json` and the installation notes before starting. From the app folder, the existing Node scripts are:

```sh
npm ci
npm test
npm start
```

The generative backend and optional model dependencies require separate setup. Package installation alone does not provide trained reconstruction quality. The newer understanding adapter's local integration and general image-quality acceptance are unfinished. Existing source/training scripts are published for inspection and continued development, without customer/reference artwork, private training datasets or fine-tuned checkpoints.

## Planned maintenance agent

The maintainer plans a development agent shared with Lenticular Studio, DTF Studio and order/stock/cost applications. Proposed API use is scoped coding assistance, debugging, regression tests, review, documentation and release preparation. Human review, measurable task outcomes and API-cost tracking are part of the plan; no completed autonomous agent is claimed.

## License

Original contributions are [MIT licensed](LICENSE). Dependencies, pretrained models and third-party code retain [their own license terms](THIRD_PARTY_NOTICES.md). API keys, private history and personal/customer records are excluded.
