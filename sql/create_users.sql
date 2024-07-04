-- Create dev user
CREATE USER 'dev' @'%' IDENTIFIED BY 'password';

GRANT ALL PRIVILEGES ON development.* TO 'dev' @'%';

DROP USER IF EXISTS 'acc' @'%';
-- Create acc user
CREATE USER 'acc' @'%' IDENTIFIED BY 'password';

GRANT ALL PRIVILEGES ON acceptance.* TO 'acc' @'%';

ALTER USER 'acc' @'%' IDENTIFIED BY "password";

DROP USER IF EXISTS 'prod' @'%';
-- Create prod user
CREATE USER 'prod' @'%' IDENTIFIED BY 'password';

GRANT ALL PRIVILEGES ON production.* TO 'prod' @'%';

-- Create prod-read-only user
CREATE USER 'prod_readonly' @'%' IDENTIFIED BY 'password';

GRANT SELECT ON production.* TO 'prod_readonly' @'%';