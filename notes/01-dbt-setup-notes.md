# Analytics Setup Notes

## Activate the virtual environment

### PowerShell

```powershell
Set-Location "D:\Workspace\workspace\Analytics"
.\.venv\Scripts\Activate.ps1
```

### Command Prompt

```cmd
cd /d D:\Workspace\workspace\Analytics
.venv\Scripts\activate.bat
```

## Install dbt Snowflake

```cmd
uv add dbt-snowflake
```

## Check the installed version

From the `food_delivery` folder, use the local wrapper:

```cmd
dbt --version
```

If you want to call the venv executable directly:

```cmd
D:\Workspace\workspace\Analytics\.venv\Scripts\dbt.exe --version
```

or

```cmd
uv pip show dbt-snowflake
```

## Troubleshooting

If `dbt --version` says it is not recognized in `cmd`, make sure you are inside `D:\Workspace\workspace\Analytics\apps\AI_Data_Engineering\food_delivery` so the local `dbt.cmd` wrapper is on the PATH. If needed, use the full venv path above. In this workspace, activating the venv did not reliably put `dbt` on `PATH`, but calling `dbt.exe` directly worked.

## dbt profiles file

`C:\Users\Asus\.dbt\profiles.yml` is dbt's connection config file. It stores the profile name and warehouse settings dbt uses to connect, such as account, user, role, warehouse, database, schema, threads, and auth method.