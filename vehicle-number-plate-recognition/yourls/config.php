<?php
// Domain configuration. Set APP_DSN (e.g. mysql:host=...;dbname=...) to use another database.
return [
    'name' => 'YOURLS',
    'tagline' => 'Short links with simple click stats',
    'description' => 'Self-hosted URL shortener with custom keywords, click statistics, plugins, an API and a bookmarklet for generating links.',
    'special' => 'shortener',
    'dsn' => getenv('APP_DSN') ?: 'sqlite:' . __DIR__ . '/data/app.sqlite',
    'resources' => [
        [
            'name' => 'links',
            'label' => 'Links',
            'description' => '',
            'fields' => [
                'slug' => [
                    'required' => true,
                    'type' => 'text',
                    'label' => 'Slug',
                ],
                'target' => [
                    'required' => true,
                    'label' => 'Target URL',
                    'type' => 'text',
                ],
                'title' => [
                    'type' => 'text',
                    'label' => 'Title',
                ],
                'tags' => [
                    'default' => '',
                    'type' => 'text',
                    'label' => 'Tags',
                ],
                'clicks' => [
                    'type' => 'int',
                    'default' => 0,
                    'label' => 'Clicks',
                ],
                'status' => [
                    'default' => 'active',
                    'type' => 'text',
                    'label' => 'Status',
                ],
            ],
        ],
        [
            'name' => 'domains',
            'label' => 'Domains',
            'description' => '',
            'fields' => [
                'domain' => [
                    'required' => true,
                    'type' => 'text',
                    'label' => 'Domain',
                ],
                'status' => [
                    'default' => 'active',
                    'type' => 'text',
                    'label' => 'Status',
                ],
                'notes' => [
                    'multiline' => true,
                    'type' => 'text',
                    'label' => 'Notes',
                ],
            ],
        ],
    ],
    'seed' => [],
];
