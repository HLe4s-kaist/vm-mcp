# Project Structure and Workflow

This document outlines the organizational structure and operational workflow for this project.

## Directory Structure

- `design/`: High-level abstraction documents of all project features. All documents are in Markdown. The `main.md` file serves as the entry point, and other documents are explicitly included from there.
- `src/`: The directory where the actual project source code resides.
- `interface/`: Communication documents between the user (designer/instructor) and the developer (agent/LLM). These are Markdown files that record instructions, additional instructions, results, etc.
- `MEMORY.md`: A file used by the developer (LLM) to maintain context periodically. Before performing any 'task', this file must be read. After completing a task, the file must be updated with any additions or changes. It tracks the current project state (in-progress, completed, pending) and important instructions from the user.

## Project Workflow

1.  **Instruction**: The user instructs the developer (LLN) to perform a task.
2.  **Planning**: Before executing the task, the developer reads `MEMORY.md` and creates a document in `interface/` named `{task_number}.md` (using a unique, non-overlapping random number). This file specifies what will be done, how it will be executed, what files will be added, and what features will be implemented.
3.  **Approval & Execution**: Upon user approval of the plan in `{task_number}.md`, the developer executes the task and records the results in the same `{task_number}.md` file.
4.  **Feedback Loop**: If the user has further instructions after reviewing the results, the developer appends the results of the additional instructions to the same `{task_number}.md` file and goes through the approval process again.
5.  **Completion**: Once the user gives final approval that the 'task' is complete, the task is finalized with a `git commit`. Following this, `MEMORY.md` is updated with a summary of the task and the project state (e.g., moving tasks from 'in-progress' to 'completed').

All documents are written in Markdown.
