# dbt Init Notes

This file documents the `dbt init` run performed inside this project folder.

## Command Used

```powershell
cd D:\Workspace\workspace\Analytics\apps\AI_Data_Engineering
dbt init food_delivery
```

## Prompts Answered

- Database: `snowflake`
- Account: `HCKCKEU-PY52911`
- User: `M20WAS`
- Authentication type: `password`
- Role: `DBT_ROLE`
- Warehouse: `FOOD_DELIVERY_WH`
- Database: `FOOD_DELIVERY`
- Schema: `STAGING`
- Threads: `8`

## Result

- dbt version: `1.12.0`
- Python version: `3.13.13`
- Python path: `D:\Workspace\workspace\Analytics\.venv\Scripts\python.exe`
- Profile written to: `C:\Users\Asus\.dbt\profiles.yml`
- Project created successfully
- Connection test: passed
- New project path: `D:\Workspace\workspace\Analytics\apps\AI_Data_Engineering\food_delivery\food_delivery`

## Notes

- `python-dotenv` reported parse warnings at the start of the run.
- The password was entered interactively and is intentionally not stored here.