-- Create development and production databases
CREATE DATABASE IF NOT EXISTS development;

CREATE DATABASE IF NOT EXISTS acceptance;

CREATE DATABASE IF NOT EXISTS production;

-- Create dev and prod users
DROP USER IF EXISTS 'dev' @'%';

CREATE USER 'dev' @'%' IDENTIFIED BY 'dev_password';

ALTER USER 'dev' @'%' IDENTIFIED BY 'other';

DROP USER IF EXISTS 'acc' @'%';

CREATE USER 'acc' @'%' IDENTIFIED BY 'acc_password';
-- ALTER USER 'acc' @'%' IDENTIFIED BY 'other';

DROP USER IF EXISTS 'prod' @'%';

CREATE USER 'prod' @'%' IDENTIFIED BY 'complex_password';
-- ALTER USER 'prod' @'%' IDENTIFIED BY 'other';

-- Grant privileges
GRANT ALL PRIVILEGES ON development.* TO 'dev' @'%';

GRANT ALL PRIVILEGES ON acceptance.* TO 'acc' @'%';

GRANT ALL PRIVILEGES ON production.* TO 'prod' @'%';

-- Apply changes
FLUSH PRIVILEGES;