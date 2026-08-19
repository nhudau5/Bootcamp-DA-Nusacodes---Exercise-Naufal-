CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    city VARCHAR(100)
);

CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    product_name VARCHAR(100) NOT NULL,
    price NUMERIC(12,2) NOT NULL
);

CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES customers(customer_id),
    order_date DATE NOT NULL
);

CREATE TABLE order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INT REFERENCES orders(order_id),
    product_id INT REFERENCES products(product_id),
    quantity INT NOT NULL
);

INSERT INTO customers (name, city) VALUES
('Budi', 'Jakarta'),
('Andi', 'Bandung'),
('Siti', 'Surabaya');

INSERT INTO products (product_name, price) VALUES
('Laptop', 10000000),
('Mouse', 300000),
('Keyboard', 500000);

INSERT INTO orders (customer_id, order_date) VALUES
(1, '2026-08-01'),
(2, '2026-08-02'),
(3, '2026-08-03');

INSERT INTO order_items (order_id, product_id, quantity) VALUES
(1, 1, 1),
(2, 2, 2),
(3, 3, 1);