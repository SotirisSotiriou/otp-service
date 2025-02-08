-- Create the database
CREATE DATABASE IF NOT EXISTS otp_service;
USE otp_service;

-- Create the users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create the otps table
CREATE TABLE IF NOT EXISTS otps (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    otp VARCHAR(6) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create a stored procedure for cleaning up expired OTPs
DELIMITER //

CREATE PROCEDURE cleanup_expired_otps()
BEGIN
    DELETE FROM otps WHERE expires_at < NOW();
END //

DELIMITER ;

-- Create an event to call the stored procedure every minute
CREATE EVENT IF NOT EXISTS cleanup_otps_event
ON SCHEDULE EVERY 1 MINUTE
DO
CALL cleanup_expired_otps();

-- Enable the event scheduler
SET GLOBAL event_scheduler = ON;

-- Optional: Insert sample data into the users table
INSERT INTO users (username, email, phone) VALUES
('John Doe', 'john.doe@example.com', '+1234567890'),
('Jane Smith', 'jane.smith@example.com', '+0987654321');