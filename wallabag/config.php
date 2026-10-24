<?php
// Domain configuration. Set APP_DSN (e.g. mysql:host=...;dbname=...) to use another database.
return [
    'name' => 'Wallabag',
    'tagline' => 'Save it, read it, keep what matters',
    'description' => 'Read-it-later service that saves articles and pages, extracts clean readable content, then supports tags, annotations, search and exports.',
    'special' => 'readlater',
    'dsn' => getenv('APP_DSN') ?: 'sqlite:' . __DIR__ . '/data/app.sqlite',
    'resources' => [
        [
            'name' => 'articles',
            'label' => 'Articles',
            'description' => '',
            'fields' => [
                'title' => [
                    'required' => true,
                    'type' => 'text',
                    'label' => 'Title',
                ],
                'url' => [
                    'required' => true,
                    'type' => 'text',
                    'label' => 'Url',
                ],
                'site' => [
                    'default' => '',
                    'type' => 'text',
                    'label' => 'Site',
                ],
                'author' => [
                    'type' => 'text',
                    'label' => 'Author',
                ],
                'excerpt' => [
                    'multiline' => true,
                    'type' => 'text',
                    'label' => 'Excerpt',
                ],
                'content' => [
                    'multiline' => true,
                    'required' => true,
                    'type' => 'text',
                    'label' => 'Content',
                ],
                'tags' => [
                    'default' => '',
                    'type' => 'text',
                    'label' => 'Tags',
                ],
                'status' => [
                    'default' => 'unread',
                    'type' => 'text',
                    'label' => 'Status',
                ],
                'added_at' => [
                    'type' => 'text',
                    'label' => 'Added At',
                ],
            ],
        ],
        [
            'name' => 'annotations',
            'label' => 'Annotations',
            'description' => '',
            'fields' => [
                'article_id' => [
                    'type' => 'int',
                    'required' => true,
                    'label' => 'Article ID',
                ],
                'quote' => [
                    'multiline' => true,
                    'type' => 'text',
                    'label' => 'Quote',
                ],
                'note' => [
                    'multiline' => true,
                    'required' => true,
                    'type' => 'text',
                    'label' => 'Note',
                ],
                'author' => [
                    'type' => 'text',
                    'label' => 'Author',
                ],
            ],
        ],
        [
            'name' => 'tags',
            'label' => 'Tags',
            'description' => '',
            'fields' => [
                'name' => [
                    'required' => true,
                    'type' => 'text',
                    'label' => 'Name',
                ],
                'color' => [
                    'default' => '#3b6e5a',
                    'type' => 'text',
                    'label' => 'Color',
                ],
                'description' => [
                    'multiline' => true,
                    'type' => 'text',
                    'label' => 'Description',
                ],
            ],
        ],
    ],
    'seed' => [],
];
