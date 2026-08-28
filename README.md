# PBIRS Mailer

**EN** | [FR](README.fr.md)

PBIRS Mailer automates the capture and email delivery of **Power BI Report Server** report pages using Playwright and Microsoft Edge.

V1 keeps configuration separate from the application code: users define their reports, target pages, recipients, and runtime settings in `config.json`.

## V1 Features

- multiple subscriptions in a single configuration file;
- navigation by Power BI internal page name or visible page label;
- waits for Power BI requests, loading indicators, and rendering stability before taking a screenshot;
- PNG image embedded in the email, with a link back to the report;
- independent subscription processing: one failure does not prevent subsequent subscriptions from running;
- rotating logs in `logs/` and diagnostic screenshots when an error occurs;
- validation-only, capture-only, and headed-browser modes.

## Quick Start on Windows

Requirements: Microsoft Edge and Python 3.10 or later.

After cloning or extracting the project, open a terminal in the project directory and run the setup.

### From PowerShell

```powershell
.\setup.cmd
```

PowerShell requires the `.\` prefix to run a script located in the current directory.

If no compatible Python version is detected, install Python from PowerShell:

```powershell
winget install --id Python.Python.3.12 -e
```

You can also download it from the [official Python website](https://www.python.org/downloads/windows/).

Then close PowerShell, open it again, and rerun:

```powershell
.\setup.cmd
```

If multiple Python versions are installed, the setup script automatically selects a compatible Python 3.10+ version. No existing installation needs to be removed.

### From Windows Command Prompt (CMD)

```cmd
setup.cmd
```

CMD does not require the `.\` prefix. You can also double-click `setup.cmd` from File Explorer.

The setup script:

- checks the Python version;
- creates `.venv`, isolated from the system Python installation;
- installs PBIRS Mailer and Playwright;
- creates `config.json` only if it does not already exist;
- detects Microsoft Edge;
- validates the configuration.

It also works when the project is located on a UNC network share. The Python environment does not need to be activated manually.

Then configure the SMTP server, sender, reports, pages, and recipients in `config.json`.

Use `.\configure.cmd` from PowerShell or `configure.cmd` from CMD to open it directly in Notepad.

This file is ignored by Git.

### Waiting for Power BI Rendering

Before each screenshot, PBIRS Mailer waits for `querydata` requests to complete, loading indicators to disappear, and the visual DOM to remain stable.

The default values are suitable for reports connected to sources such as SSAS:

```json
"render_timeout_seconds": 120,
"render_quiet_seconds": 5,
"render_stable_seconds": 3
```

Increase `render_timeout_seconds` for particularly slow reports.

If the report does not stabilize before the timeout, the subscription fails and a `*-error.png` screenshot is created. No email containing an incomplete image is sent.

### Project Located on a UNC Network Share

`CMD.EXE` may display a warning when the project path starts with `\\server`.

To run the setup without this warning, use:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1
```

## Progressive Testing

Validate the configuration without opening Edge:

```powershell
.\run.cmd --dry-run
```

Generate screenshots without sending email:

```powershell
.\run.cmd --no-send
```

Edge runs headlessly by default with `browser.headless: true`.

Use `--headed` only when troubleshooting browser navigation.

To display Edge and troubleshoot a single subscription:

```powershell
.\run.cmd --no-send --headed --subscription "Example report" --verbose
```

Then enable `smtp.enabled` in `config.json` and run:

```powershell
.\run.cmd
```

The exit code is:

- `0` if all subscriptions succeed;
- `1` if at least one subscription fails;
- `2` if the configuration or environment is invalid.

From CMD, use the same commands without the `.\` prefix:

```cmd
run.cmd --dry-run
run.cmd --no-send
run.cmd
```

## Selecting the Report Page

The preferred method to test is `page.internal_name`, for example:

```text
ReportSection42
```

It adds `pageName` to the URL and avoids relying on visible UI text.

Its behavior should be validated against the PBIRS version in use: the parameter is documented for embedded Power BI reports, while the PBIRS documentation explicitly guarantees only `rs:embed=true`.

If the internal name is unknown or unsupported, leave `internal_name` set to `null` and configure `page.display_name`.

PBIRS Mailer will then look for an accessible tab, button, or link matching that label.

If navigation fails, run the test with `--headed --verbose`. A `*-error.png` screenshot will also be created in `captures/`.

One subscription represents one page and produces one image.

To capture multiple pages from the same report, duplicate the subscription and use a unique subscription name, page, and PNG filename for each one.

## Scheduled Execution

For scheduled execution, use Windows Task Scheduler with the same technical account that can access the PBIRS reports and reach the SMTP relay.

Set the project directory as the task's working directory.

## Security and Publishing

- never publish `config.json`, screenshots, logs, or business data;
- use synthetic data in screenshots and documentation;
- verify that the execution account has access to each PBIRS report;
- start with `smtp.enabled: false` and a single test subscription.

## Developer Installation

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\ruff.exe check .
```

Activating `.venv` is optional: the commands directly use the executables from the virtual environment.

## Resources

- **EN** — [From Report Server to Inbox: Automating Power BI Report Server Screenshots with Python and Playwright](https://medium.com/@nenesidibebakary/from-report-server-to-inbox-automating-power-bi-report-server-screenshots-with-python-and-c65962e66fec)
- **FR** — [PBIRS Mailer : automatiser l'envoi de captures Power BI Report Server avec Python et Playwright](https://medium.com/@nenesidibebakary/pbirs-mailer-automatiser-lenvoi-de-captures-power-bi-report-server-avec-python-et-playwright-dce9a160d3bc)
- [Power BI Report Server documentation](https://learn.microsoft.com/en-us/power-bi/report-server/get-started)
- [Playwright for Python documentation](https://playwright.dev/python/docs/intro)

## Documentation

- [Troubleshooting Guide](docs/TROUBLESHOOTING.md)
- [Acceptance Test Checklist](docs/ACCEPTANCE_TEST_CHECKLIST.md)
- [Changelog](CHANGELOG.md)
- [Security Policy](SECURITY.md)
- [Contributing](CONTRIBUTING.md)

## Project Status

Version `1.0.1` improves report rendering synchronization, particularly for reports connected to SSAS.

See the changelog for detailed changes.

License: MIT.
