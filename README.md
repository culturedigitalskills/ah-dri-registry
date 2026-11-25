# A&H DRI Registry

An open registry of the compute, tools and AI services that UK arts and humanities researchers can use: what each one is good for, who can access it, how to apply, what it costs and how it handles data.

It is a community resource for digital research infrastructure (DRI), and a starting draft for the community to correct, extend and own.

- **Browse:** https://culturedigitalskills.github.io/ah-dri-registry/
- **API:** https://culturedigitalskills.github.io/ah-dri-registry/api/v1/index.json
- **Suggest an entry or a correction:** [open an issue](https://github.com/culturedigitalskills/ah-dri-registry/issues/new/choose)

## What's in it

| Collection | What it covers | Folder |
|---|---|---|
| Resources | Compute that runs your work on someone else's hardware: national supercomputers, institutional clusters, cloud and notebook services | `data/resources/` |
| Tools and models | Software you run yourself and model libraries | `data/tools/` |
| AI services | Chat assistants and model APIs, one entry per version (free, institutional, API), because their data terms differ | `data/ai-services/` |

Each entry is one YAML file. Fields follow the [EOSC Service Profile v5.0](https://eosc-service-profile.readthedocs.io/en/5.0/) where one exists, plus fields added for arts and humanities researchers (good for, eligibility, cost, grant costing, sensitive data and so on). `schema/fields.yml` describes every field.

Entries marked `[to be confirmed]` have not yet been verified. `Last checked` gives the date an entry was last reviewed.

## Using the API

The API is a set of static JSON files, rebuilt whenever the data changes.

| Endpoint | Returns |
|---|---|
| `/api/v1/index.json` | List of endpoints |
| `/api/v1/resources.json` | All resources (also `tools.json`, `ai-services.json`) |
| `/api/v1/resources/{id}.json` | One resource, e.g. `/api/v1/resources/isambard-ai.json` |
| `/api/v1/resources.csv` | Spreadsheet download (also for tools and AI services) |
| `/api/v1/schema/resources.schema.json` | JSON Schema for each collection |
| `/api/v1/vocabularies.json` | Allowed values for every controlled field, with EOSC vocabulary IDs |
| `/api/v1/eosc/resources.json` | Draft export using EOSC field names and vocabulary IDs |
| `/api/v1/report.json` | Entries with missing fields or items still to be confirmed |

Example:

```bash
curl https://culturedigitalskills.github.io/ah-dri-registry/api/v1/resources/isambard-ai.json
```

The `v1` in the path will stay stable. If the structure changes in a way that would break existing uses, it will be published as `v2` alongside.

## Contributing

You don't need to know Git. See [CONTRIBUTING.md](CONTRIBUTING.md) for the three ways to contribute: an issue form, the Pages CMS editor, or a pull request.

## How this was made

The first version was compiled with AI assistance from public sources and is being checked by people. See [docs/how-this-was-made.md](docs/how-this-was-made.md).

## Licence

- **Registry data** (everything in `data/`) is licensed under [CC BY 4.0](data/LICENSE). Please credit "A&H DRI Registry, DRI community contributors".
- **Code** (scripts, schemas, workflow and web page) is licensed under the [MIT Licence](LICENSE).
- Provider names and logos belong to their owners. The registry links to logos; it does not copy them.

To cite the registry, see [CITATION.cff](CITATION.cff) or use "Cite this repository" on GitHub.

## For maintainers

```bash
pip install -r scripts/requirements.txt
python scripts/build.py --validate   # check the data
python scripts/build.py              # build the site and API into site/
python scripts/generate.py           # after changing schema/fields.yml or data/vocabularies.yml
```

The GitHub Action in `.github/workflows/publish.yml` validates every change and publishes `main` to GitHub Pages.
