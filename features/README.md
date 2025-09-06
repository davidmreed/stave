# Behavioral Tests

This directory contains [behave](https://behave.readthedocs.io/) tests for Stave.
Behave is a BDD ([Behavior Driven Development](https://en.wikipedia.org/wiki/Behavior-driven_development)) framework for Python
that allows you to write tests in a natural language style, using [Gherkin](https://cucumber.io/docs/gherkin/reference) syntax.

This is extended with [behave-django](https://behave-django.readthedocs.io/) to provide Django-specific testing capabilities.

## Running the Tests

To run the tests, execute from the root of the repository:

```bash
just behave
```

If you want to specify a particular feature file, you can do so by providing the path to the file:

```bash
just behave features/admin_login.feature
```
