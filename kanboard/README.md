# Kanboard

A calm kanban board for focused teams

> Self-hosted kanban project management with swimlanes, subtasks, comments, attachments, Gantt charts and an automation plugin API.

## Overview

An original, self-contained implementation of the **Kanboard** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Projects, tasks and comments
- Status, assignee, priority and due date on every task
- Search across projects and tasks
- Owner/member accounts
- Seed project with a realistic backlog

## Stack

`PHP; SQLite; JavaScript; Bootstrap`

The application follows a small MVC structure (front controller, PDO models, PHP views) and uses PDO so the same code runs on SQLite locally and MySQL in production.

## Run

```bash
php -S localhost:8000 -t public
# open http://localhost:8000
```

## Structure

```text
kanboard/
├── public/index.php     front controller (PHP built-in server router)
├── routes.php           HTTP routes and controllers
├── src/                 PDO database layer, helpers, bootstrap
├── views/               server-rendered templates
├── config.php           resources, seed data and DSN
└── data/app.sqlite      local database (gitignored)
```

## Testing

```bash
composer test      # or: php tests/run.php
```

67 assertions in two suites: the rules of the board on their own (the
columns, the order of the cards, the work in progress limit, the validation
of a card, the reordering, the overdue cards, the swimlanes, who may see
which project and the summary) and the app itself on a real server (the board
renders, a card moves, a full column refuses a card, the rules that run when
a card is created, and the configured defaults).

## The board

`src/kanban.php` holds the rules, as pure functions:

- the columns of the board and the priorities
- the cards of a project, grouped by column and in the order they were
  placed
- the work in progress limit: `in_progress` holds three cards and `review`
  two, and the card being moved is not counted against the limit
- the validation of a card: the project has to exist, the status has to be a
  column, the priority has to be one the board knows and the due date has to
  be written as `YYYY-MM-DD`
- the reordering after a move
- the overdue cards, the swimlanes and the board summary
- who may see which project

The app has a board at `/board` with the columns, the move buttons, the
swimlanes and the overdue count, and a card can be moved with
`POST /r/tasks/{id}/move`.

## Notes and limitations

- The board is rendered through the generic resource views rather than a drag-and-drop surface; status and position are editable per task.
- The upstream Kanboard is PHP with SQLite/MySQL; this implementation uses the same PHP + PDO stack.
- Comments and tasks are separate resources with explicit IDs, which keeps the schema easy to port.

## License

MIT. See `LICENSE`.
