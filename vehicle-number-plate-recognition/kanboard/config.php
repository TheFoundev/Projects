<?php
// Domain configuration. Set APP_DSN (e.g. mysql:host=...;dbname=...) to use another database.
return [
    'name' => 'Kanboard',
    'tagline' => 'A calm kanban board for focused teams',
    'description' => 'Self-hosted kanban project management with swimlanes, subtasks, comments, attachments, Gantt charts and an automation plugin API.',
    'special' => 'kanban',
    'dsn' => getenv('APP_DSN') ?: 'sqlite:' . __DIR__ . '/data/app.sqlite',
    'resources' => [
        [
            'name' => 'projects',
            'label' => 'Projects',
            'description' => '',
            'fields' => [
                'name' => [
                    'required' => true,
                    'type' => 'text',
                    'label' => 'Name',
                ],
                'description' => [
                    'multiline' => true,
                    'type' => 'text',
                    'label' => 'Description',
                ],
                'status' => [
                    'default' => 'active',
                    'type' => 'text',
                    'label' => 'Status',
                ],
                'owner' => [
                    'type' => 'text',
                    'label' => 'Owner',
                ],
            ],
        ],
        [
            'name' => 'tasks',
            'label' => 'Tasks',
            'description' => '',
            'fields' => [
                'project_id' => [
                    'type' => 'int',
                    'required' => true,
                    'label' => 'Project ID',
                ],
                'title' => [
                    'required' => true,
                    'type' => 'text',
                    'label' => 'Title',
                ],
                'description' => [
                    'multiline' => true,
                    'type' => 'text',
                    'label' => 'Description',
                ],
                'status' => [
                    'default' => 'backlog',
                    'type' => 'text',
                    'label' => 'Status',
                ],
                'assignee' => [
                    'type' => 'text',
                    'label' => 'Assignee',
                ],
                'priority' => [
                    'default' => 'normal',
                    'type' => 'text',
                    'label' => 'Priority',
                ],
                'due_date' => [
                    'type' => 'text',
                    'label' => 'Due Date',
                ],
                'position' => [
                    'type' => 'int',
                    'default' => 0,
                    'label' => 'Position',
                ],
            ],
        ],
        [
            'name' => 'comments',
            'label' => 'Comments',
            'description' => '',
            'fields' => [
                'task_id' => [
                    'type' => 'int',
                    'required' => true,
                    'label' => 'Task ID',
                ],
                'author' => [
                    'required' => true,
                    'type' => 'text',
                    'label' => 'Author',
                ],
                'body' => [
                    'multiline' => true,
                    'required' => true,
                    'type' => 'text',
                    'label' => 'Body',
                ],
            ],
        ],
    ],
    'seed' => [],
];
