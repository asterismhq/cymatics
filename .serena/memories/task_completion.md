# Task Completion Checklist
- Run `just lint` (or `just format`) and `just test` relevant subsets to confirm code quality.
- Ensure Docker-related files still build via `docker build` or `just build-test` if touched.
- Update documentation (README, change logs) when behavior or setup changes.
- Verify `.env` defaults and dependency container wiring align with new functionality.
- Communicate remaining follow-ups or environment assumptions in the task response.