<?php
// Domain configuration. Set APP_DSN (e.g. mysql:host=...;dbname=...) to use another database.
return [
    'name' => 'BookStack',
    'tagline' => 'Documentation that stays organised',
    'description' => 'Documentation wiki that organises pages into shelves, books and chapters with WYSIWYG editing, versioning, search and role permissions.',
    'special' => 'wiki',
    'dsn' => getenv('APP_DSN') ?: 'sqlite:' . __DIR__ . '/data/app.sqlite',
    'resources' => [
        [
            'name' => 'books',
            'label' => 'Books',
            'description' => '',
            'fields' => [
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
                'owner' => [
                    'type' => 'text',
                    'label' => 'Owner',
                ],
                'status' => [
                    'default' => 'published',
                    'type' => 'text',
                    'label' => 'Status',
                ],
            ],
        ],
        [
            'name' => 'chapters',
            'label' => 'Chapters',
            'description' => '',
            'fields' => [
                'title' => [
                    'required' => true,
                    'type' => 'text',
                    'label' => 'Title',
                ],
                'book_id' => [
                    'type' => 'int',
                    'required' => true,
                    'label' => 'Book ID',
                ],
                'description' => [
                    'multiline' => true,
                    'type' => 'text',
                    'label' => 'Description',
                ],
                'position' => [
                    'type' => 'int',
                    'default' => 1,
                    'label' => 'Position',
                ],
            ],
        ],
        [
            'name' => 'pages',
            'label' => 'Pages',
            'description' => '',
            'fields' => [
                'title' => [
                    'required' => true,
                    'type' => 'text',
                    'label' => 'Title',
                ],
                'chapter_id' => [
                    'type' => 'int',
                    'required' => true,
                    'label' => 'Chapter ID',
                ],
                'body' => [
                    'multiline' => true,
                    'required' => true,
                    'type' => 'text',
                    'label' => 'Body',
                ],
                'tags' => [
                    'type' => 'text',
                    'label' => 'Tags',
                ],
                'version' => [
                    'type' => 'int',
                    'default' => 1,
                    'label' => 'Version',
                ],
            ],
        ],
    ],
    'seed' => [
        'books' => [
            [
                'title' => 'Engineering Handbook',
                'description' => 'How we build, review and operate software.',
                'owner' => 'Platform team',
                'status' => 'published',
            ],
            [
                'title' => 'Product Playbook',
                'description' => 'Discovery, delivery and launch checklists.',
                'owner' => 'Product team',
                'status' => 'published',
            ],
        ],
        'chapters' => [
            [
                'title' => 'Getting started',
                'book_id' => 1,
                'description' => 'Local setup and first contribution.',
                'position' => 1,
            ],
            [
                'title' => 'Architecture',
                'book_id' => 1,
                'description' => 'Service boundaries and data ownership.',
                'position' => 2,
            ],
            [
                'title' => 'Discovery',
                'book_id' => 2,
                'description' => 'Turning a problem into a scoped bet.',
                'position' => 1,
            ],
        ],
        'pages' => [
            [
                'title' => 'Welcome',
                'chapter_id' => 1,
                'body' => 'Welcome to the handbook.

This wiki is organised into books, chapters and pages. Every page edit creates a revision so you can see how documentation evolved.

Start by creating a book, add a chapter, then write a page.',
                'tags' => 'onboarding',
                'version' => 1,
            ],
            [
                'title' => 'Service boundaries',
                'chapter_id' => 2,
                'body' => 'Each service owns its data and exposes a small API.

Rules of thumb:
- One reason to deploy
- Explicit contracts
- No shared database writes
- Observable by default',
                'tags' => 'architecture,api',
                'version' => 1,
            ],
            [
                'title' => 'Writing a problem statement',
                'chapter_id' => 3,
                'body' => 'A good problem statement names the user, the situation, the friction and the evidence.

Avoid jumping to a solution before the problem is understood.',
                'tags' => 'product,discovery',
                'version' => 1,
            ],
        ],
    ],
];
