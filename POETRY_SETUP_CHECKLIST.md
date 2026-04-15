# Poetry Setup Checklist

Use this checklist to ensure your Poetry migration is complete and working.

## Pre-Migration Cleanup

- [ ] Backup your current environment (optional but recommended)
- [ ] Deactivate any active virtual environment: `deactivate`
- [ ] Remove old virtual environment folder: `rm -rf venv/` (if exists)

## Poetry Installation

### Linux/macOS/WSL
- [ ] Run: `curl -sSL https://install.python-poetry.org | python3 -`
- [ ] Add to PATH: `export PATH="$HOME/.local/bin:$PATH"`
- [ ] Verify installation: `poetry --version`

### Windows
- [ ] Run in PowerShell: `(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -`
- [ ] Add `%APPDATA%\Python\Scripts` to PATH
- [ ] Verify installation: `poetry --version`

## Project Setup

- [ ] Navigate to project root directory
- [ ] Run: `poetry install`
- [ ] Wait for dependency resolution and installation
- [ ] Verify no errors in output
- [ ] Check that `poetry.lock` file was created

## Configuration (Optional)

- [ ] Enable parallel installation: `poetry config installer.parallel true`
- [ ] Disable keyring if causing issues: `poetry config keyring.enabled false`
- [ ] Set Python version if needed: `poetry env use python3.11`

## Testing the Setup

### Backend Server
- [ ] Run: `poetry run uvicorn main:app --reload --port 5000`
- [ ] Or run: `poetry run start`
- [ ] Verify server starts without errors
- [ ] Check http://localhost:5000/docs loads
- [ ] Stop server (Ctrl+C)

### Run Tests
- [ ] Run: `poetry run pytest`
- [ ] Verify all tests pass (or check which ones fail)
- [ ] Run with coverage: `poetry run pytest --cov=. --cov-report=html`
- [ ] Check coverage report in `htmlcov/index.html`

### Import Verification
- [ ] Run: `poetry run python -c "import fastapi; import uvicorn; print('Imports OK')"`
- [ ] Verify "Imports OK" is printed
- [ ] Run: `poetry run python -c "from services.rag_service import rag_service; print('Services OK')"`
- [ ] Verify "Services OK" is printed

## Docker Testing

- [ ] Build Docker image: `docker build -t pdf-chatbot-backend .`
- [ ] Verify build completes successfully
- [ ] Run container: `docker run -p 10000:10000 --env-file .env pdf-chatbot-backend`
- [ ] Check container starts and serves requests
- [ ] Stop container

## Frontend Integration

- [ ] Start backend: `poetry run start`
- [ ] In another terminal, start frontend: `cd frontend && npm run dev`
- [ ] Open frontend in browser
- [ ] Test login/register
- [ ] Test PDF upload
- [ ] Test chat functionality
- [ ] Verify no CORS errors

## Environment Variables

- [ ] Verify `.env` file exists
- [ ] Check `GOOGLE_API_KEY` is set
- [ ] Check `JWT_SECRET_KEY` is set
- [ ] Check `MONGODB_URI` is set (if using MongoDB)
- [ ] Test with: `poetry run python -c "from dotenv import load_dotenv; load_dotenv(); import os; print('API Key:', 'SET' if os.getenv('GOOGLE_API_KEY') else 'NOT SET')"`

## Common Commands Verification

- [ ] Add package: `poetry add httpx` (then remove: `poetry remove httpx`)
- [ ] Show packages: `poetry show`
- [ ] Show tree: `poetry show --tree`
- [ ] Update packages: `poetry update --dry-run`
- [ ] Check environment: `poetry env info`

## Documentation Review

- [ ] Read [QUICKSTART_POETRY.md](QUICKSTART_POETRY.md)
- [ ] Read [POETRY_MIGRATION.md](POETRY_MIGRATION.md)
- [ ] Read [MIGRATION_SUMMARY.md](MIGRATION_SUMMARY.md)
- [ ] Bookmark [Poetry Documentation](https://python-poetry.org/docs/)

## Team Communication

- [ ] Notify team about Poetry migration
- [ ] Share [QUICKSTART_POETRY.md](QUICKSTART_POETRY.md) with team
- [ ] Update team documentation/wiki
- [ ] Schedule knowledge sharing session (if needed)

## CI/CD Updates (if applicable)

- [ ] Update GitHub Actions workflow
- [ ] Update GitLab CI configuration
- [ ] Update Jenkins pipeline
- [ ] Update deployment scripts
- [ ] Test CI/CD pipeline

## Cleanup (Optional)

After confirming everything works:
- [ ] Consider removing `requirements.txt` (keep for now recommended)
- [ ] Consider removing `tests/test_requirements.txt` (keep for now recommended)
- [ ] Update any scripts that reference pip
- [ ] Update documentation that mentions pip

## Troubleshooting

If you encounter issues:

### Poetry not found
```bash
# Add to PATH
export PATH="$HOME/.local/bin:$PATH"
# Or reinstall Poetry
```

### Dependency conflicts
```bash
# Clear cache and reinstall
poetry cache clear pypi --all
poetry install
```

### Virtual environment issues
```bash
# Remove and recreate
poetry env remove python
poetry install
```

### Slow installation
```bash
# Enable parallel installation
poetry config installer.parallel true
```

### Import errors
```bash
# Verify you're using Poetry's environment
poetry run python -c "import sys; print(sys.executable)"
# Should show path to Poetry's virtual environment
```

## Success Criteria

✅ All items checked above
✅ Backend server starts without errors
✅ Tests pass successfully
✅ Docker build and run work
✅ Frontend can communicate with backend
✅ No import errors
✅ Team is informed and onboarded

## Next Steps

Once all checks pass:
1. Commit `pyproject.toml` and `poetry.lock` to git
2. Update deployment documentation
3. Monitor for any issues in production
4. Enjoy better dependency management! 🎉

## Support Resources

- [Poetry Documentation](https://python-poetry.org/docs/)
- [Poetry Commands](https://python-poetry.org/docs/cli/)
- [Dependency Specification](https://python-poetry.org/docs/dependency-specification/)
- [Managing Environments](https://python-poetry.org/docs/managing-environments/)
- Project-specific: [POETRY_MIGRATION.md](POETRY_MIGRATION.md)

---

**Date Completed:** _______________

**Completed By:** _______________

**Notes:** _______________
