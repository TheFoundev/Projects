<?php
// Domain configuration. Set APP_DSN (e.g. mysql:host=...;dbname=...) to use another database.
return [
    'name' => 'Sylius',
    'tagline' => 'An ecommerce core with a clear data model',
    'description' => 'Ecommerce framework on Symfony with product variants, promotions, taxes, shipping, inventory and multi-channel sales.',
    'special' => 'commerce',
    'dsn' => getenv('APP_DSN') ?: 'sqlite:' . __DIR__ . '/data/app.sqlite',
    'resources' => [
        [
            'name' => 'products',
            'label' => 'Products',
            'description' => '',
            'fields' => [
                'name' => [
                    'required' => true,
                    'type' => 'text',
                    'label' => 'Name',
                ],
                'price_cents' => [
                    'type' => 'int',
                    'required' => true,
                    'label' => 'Price (cents)',
                    'default' => 2500,
                ],
                'stock' => [
                    'type' => 'int',
                    'default' => 10,
                    'label' => 'Stock',
                ],
                'category' => [
                    'default' => 'General',
                    'type' => 'text',
                    'label' => 'Category',
                ],
                'description' => [
                    'multiline' => true,
                    'type' => 'text',
                    'label' => 'Description',
                ],
            ],
        ],
        [
            'name' => 'orders',
            'label' => 'Orders',
            'description' => '',
            'fields' => [
                'customer_email' => [
                    'required' => true,
                    'label' => 'Customer email',
                    'type' => 'text',
                ],
                'total_cents' => [
                    'type' => 'int',
                    'default' => 0,
                    'label' => 'Total (cents)',
                ],
                'status' => [
                    'default' => 'paid',
                    'type' => 'text',
                    'label' => 'Status',
                ],
            ],
        ],
        [
            'name' => 'promotions',
            'label' => 'Promotions',
            'description' => '',
            'fields' => [
                'name' => [
                    'required' => true,
                    'type' => 'text',
                    'label' => 'Name',
                ],
                'code' => [
                    'required' => true,
                    'type' => 'text',
                    'label' => 'Code',
                ],
                'percent_off' => [
                    'type' => 'int',
                    'default' => 10,
                    'label' => 'Percent Off',
                ],
                'status' => [
                    'default' => 'active',
                    'type' => 'text',
                    'label' => 'Status',
                ],
            ],
        ],
        [
            'name' => 'channels',
            'label' => 'Channels',
            'description' => '',
            'fields' => [
                'name' => [
                    'required' => true,
                    'type' => 'text',
                    'label' => 'Name',
                ],
                'currency' => [
                    'default' => 'USD',
                    'type' => 'text',
                    'label' => 'Currency',
                ],
                'status' => [
                    'default' => 'enabled',
                    'type' => 'text',
                    'label' => 'Status',
                ],
            ],
        ],
    ],
    'seed' => [],
];
