# Rain Module Cache Guard Task

## 🎯 Goal
Ensure the packaged GUI no longer falls back to the legacy rain module by preventing FastF1 cache initialisation errors when the `cache/` directory is missing in the distribution build.

## ✅ Scope
- Audit the shared CLI base import that enables the FastF1 cache at import time.
- Introduce a safe guard so GUI contexts can run without a writable `cache/` directory.
- Verify that the rain module follows the API-only code path in both development and packaged builds.

## 🛠️ Steps
1. Add a defensive check around the global `fastf1.Cache.enable_cache('cache')` call to create the directory when possible and ignore errors gracefully in read-only environments.
2. Confirm no other modules rely on side effects from this call during GUI startup.
3. Rebuild or simulate the packaged environment to confirm the rain module no longer triggers the legacy fallback path.

## 🧪 Validation
- Run the existing unit test suite.
- Launch the GUI (dev build) and open the rain analysis module to ensure it loads using the API workflow without warnings.
- For packaged validation, inspect runtime logs (once rebuilt) to confirm the absence of `[LEGACY]` fallbacks for rain analysis.

## 📎 Notes
- This change must respect the API-ONLY policy: no automatic CLI execution from GUI modules.
- The guard should prefer creating the cache directory when running from source but fail silently (with a warning) when the directory cannot be created in packaged builds.
