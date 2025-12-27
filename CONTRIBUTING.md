# Contributing Guide

This repository follows a specific workflow to manage custom configurations while staying up-to-date with the manufacturer's upstream changes.

## Repository Structure

- **`origin`**: Your personal GitHub repository (e.g., `mpetito/thinker-x400`). This is where you push your work.
- **`upstream`**: The manufacturer's GitCode repository. This is read-only and used for pulling updates.
- **`master`**: The production branch. This code runs on the printer.

## Setup

If you haven't already, configure your remotes:

```bash
# Rename default origin to upstream (if cloned from manufacturer)
git remote rename origin upstream

# Add your fork as origin
git remote add origin https://github.com/YOUR_USERNAME/thinker-x400.git

# Set master to track your fork
git push -u origin master
```

## Workflow 1: Making Config Changes

Use this workflow when adding macros, changing settings, or fixing bugs.

1. **Start fresh**:

    ```bash
    git checkout master
    git pull origin master
    ```

2. **Create a feature branch**:

    ```bash
    git checkout -b feature/description-of-change
    # Example: git checkout -b feature/tweak-z-offset
    ```

3. **Make changes, commit, and push**:

    ```bash
    git add .
    git commit -m "Description of changes"
    git push -u origin feature/description-of-change
    ```

4. **Open a Pull Request**:
    - Go to GitHub.
    - Open a PR from your feature branch to `master`.
    - Review changes and merge.

## Workflow 2: Syncing with Manufacturer (Upstream)

Use this workflow to pull in updates from the manufacturer without breaking your custom config.

1. **Start fresh**:

    ```bash
    git checkout master
    git pull origin master
    ```

2. **Create a maintenance branch**:

    ```bash
    git checkout -b maintenance/sync-upstream
    ```

3. **Pull upstream changes**:

    ```bash
    git fetch upstream
    git merge upstream/master
    ```

    *Note: Resolve any merge conflicts in VS Code (e.g., in `printer.cfg`), then commit the merge.*

4. **Push and Review**:

    ```bash
    git push -u origin maintenance/sync-upstream
    ```

5. **Open a Pull Request**:
    - Go to GitHub.
    - Open a PR from `maintenance/sync-upstream` to `master`.
    - This allows you to see exactly what the manufacturer changed before it hits your printer.

## Deploying to Printer

On the physical printer, ensure it is pulling from your fork:

```bash
cd ~/thinker-x400
git pull origin master
# Restart Klipper if necessary
```
