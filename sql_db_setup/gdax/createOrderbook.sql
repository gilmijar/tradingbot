USE `gdax`;
-- create table `orderbook`
-- orderType is a number for speed and small table size
-- row_format is fixed for speed, size, and better maintenance
DROP TABLE IF EXISTS `orderbook`;
CREATE TABLE IF NOT EXISTS `orderbook` (
    `orderTimeStamp` int(11) NOT NULL,
    `step` smallint(4) NOT NULL COMMENT 'negative for ask, positive for bid',
    `price` DECIMAL(12,4) UNSIGNED NOT NULL,
    `amount` DECIMAL(14,8) UNSIGNED NOT NULL,
    `orderCount` INTEGER UNSIGNED NOT NULL,
    PRIMARY KEY (`orderTimeStamp`,`step`)
    )
ROW_FORMAT=FIXED
ENGINE=ARIA;

-- CREATE INDEX iPrice ON orderbook(`price`);
