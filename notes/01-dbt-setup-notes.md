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

```cmd
dbt --version
```

or

```cmd
uv pip show dbt-snowflake
```