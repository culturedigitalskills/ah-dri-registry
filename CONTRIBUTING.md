# Contributing to the A&H DRI Registry

Thank you for helping. The registry is only as good as the people who check and update it, and every contributor is credited.

## Three ways to contribute

### 1. Suggest an entry or a correction (no account setup needed beyond GitHub)

Use the [issue forms](https://github.com/culturedigitalskills/ah-dri-registry/issues/new/choose): "Suggest a resource, tool or AI service" or "Report a correction". A maintainer will check it and add it, crediting you.

### 2. Edit in Pages CMS (for invited editors)

Pages CMS gives you a form for each entry, with dropdowns for the controlled fields. No Git or YAML needed.

1. Accept the invitation email and sign in at https://app.pagescms.org.
2. Open the **ah-dri-registry** project and choose a collection: Resources, Tools and models, or AI services.
3. Open an entry to edit it, or click **Add an entry**.
4. Save. Your change is recorded under your name.

Ask a maintainer for an invitation if you'd like to edit regularly.

### 3. Pull request (if you use Git)

Each entry is a YAML file in `data/resources/`, `data/tools/` or `data/ai-services/`. Copy an existing file as a template. Run `python scripts/build.py --validate` before opening the pull request; the GitHub Action runs the same check.

## Rules for entries

- **Use public sources only**, and add the link in Notes when a fact is not obvious from the provider's own pages.
- **Mark anything you could not verify** with `[to be confirmed]`.
- **Update `Last checked`** to today's date when you check an entry, and put your name in **Collected by**.
- **Use team contact addresses**, such as a service desk, never a named individual's email.
- **Write descriptions in your own words.** Don't copy text from providers' websites.
- **Link to logos; don't upload them.** They belong to the providers.
- **The ID is permanent.** It is used in API addresses, so don't change it once an entry is published. Use lowercase letters, numbers and hyphens.
- **"Works on" (Tools)** should list only resources whose own documentation supports the tool, not ones where it would probably work.
- **"Suitable for sensitive data"** should reflect only what the service itself states.

If you used an AI tool to help gather or draft information, say so in **Collected by**, for example "Your Name, AI-assisted (tool name)", and check every fact against its source.

## Adding a field or an option to a dropdown

Fields are defined in `schema/fields.yml` and dropdown options in `data/vocabularies.yml`. After changing either, run `python scripts/generate.py` to update the JSON Schemas and the Pages CMS form, and commit the result. Please open an issue first so the change can be discussed: other people may be using the API.

## Licence of contributions

By contributing, you agree that your contribution to the registry data is published under [CC BY 4.0](data/LICENSE), and that any code you contribute is published under the [MIT Licence](LICENSE). You keep the credit: contributors are named in the entries they collect and in the repository history.

## Code of conduct

Be kind and assume good faith. The registry brings together people from very different disciplines and roles, and questions from people new to computing are welcome.
